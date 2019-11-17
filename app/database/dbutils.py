from datetime import date, datetime, MINYEAR, timedelta
from typing import List

import gspread
from sqlalchemy import func
from sqlalchemy.orm import Query, aliased

from app import db
from app.api.apiutils import ApiFile
from app.database.models import Course, Student, Form, Question, Answer, Parameter


class DbParam:

    @classmethod
    def getparam(cls, name: str) -> str:
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            res = None
        else:
            res = param.value
        return res

    @classmethod
    def setparam(cls, name: str, value) -> (bool, str):
        success = True
        message = ""
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            newparam = Parameter(name=name, value=value)
            try:
                db.session.add(newparam)
                db.session.commit()
            except Exception as ex:
                db.session.rollback()
                success = False
                message = f"Erreur : Impossible d'ajouter le paramètre {name}"
        else:
            param.value = value
            try:
                db.session.update(param)
                db.session.commit()
            except Exception as ex:
                db.session.rollback()
                success = False
                message = f"Erreur : Impossible de mettre à jour le paramètre {name}"
        return success, message


class DbCourse:

    @classmethod
    def insert(cls, label: str, startdate: date, enddate: date, spreadsheet: str) -> (bool, str):
        # check fields all filled
        success = (label is not None and label != "")
        message = "Erreur : L'intitulé n'est pas renseigné" if not success else ""
        if success:
            success = (startdate is not None)
            message = "Erreur : La date de début n'est pas renseignée" if not success else ""
        if success:
            success = (enddate is not None)
            message = "Erreur : La date de fin n'est pas renseignée" if not success else ""
        if success:                                                     # TODO pas forcément au début
            success = (spreadsheet is not None and spreadsheet != "")
            message = "Erreur : Le fichier des formulaires n'est pas renseigné" if not success else ""
        # check dates coherent
        if success:
            success = (startdate <= enddate)
            message = "Erreur : La date de début est postérieure à la date de fin" if not success else ""
        # check neither label nor spreadsheet already exists in Courses
        if success:
            success = (Course.query.filter_by(label=label).count() == 0)
            message = "Erreur : Une formation avec le même intitulé existe déjà" if not success else ""
        if success:
            success = (Course.query.filter_by(spreadsheet=spreadsheet).count() == 0)
            message = "Erreur : Une formation avec le même fichier associé existe déjà" if not success else ""
        if success:
            try:
                newcourse = Course(label=label, startdate=startdate, enddate=enddate, spreadsheet=spreadsheet)
                db.session.add(newcourse)
                db.session.commit()
                message = f"Succès : Formation {newcourse.label} ajoutée"
            except Exception as ex:
                db.session.rollback()
                success = False
                message = str(ex)
        return success, message

    @classmethod
    def delete(cls, courseid: str) -> (bool, str):
        # check fields all filled
        success = (courseid is not None and courseid != "")
        message = "Erreur : La formation n'est pas renseignée" if not success else ""
        if success:
            success = courseid.isnumeric()
            message = "Erreur : L'id formation n'est pas numérique" if not success else ""
        if success:
            coursetodel = Course.query.get(int(courseid))
            success = (coursetodel is not None)
            message = "Erreur : Formation inexistante" if not success else ""
        if success:
            print(coursetodel.students)
            success = ((coursetodel.students is None) or (len(coursetodel.students) == 0))
            message = "Erreur : Des étudiants sont rattachés à cette formation" if not success else ""
        if success:
            success = ((coursetodel.questions is None) or (len(coursetodel.questions) == 0))
            message = "Erreur : Des questions sont liées à cette formation" if not success else ""
        if success:
            success = ((coursetodel.forms is None) or (len(coursetodel.forms) == 0))
            message = "Erreur : Des formulaires sont liés à cette formation" if not success else ""
        if success:
            try:
                db.session.delete(coursetodel)
                db.session.commit()
                message = f"Succès: Formation {coursetodel.label} supprimée"
            except Exception as ex:
                db.session.rollback()
                success = False
                message = str(ex)
        return success, message


class DbStudent:

    @classmethod
    def insert(cls, lastname: str, firstname: str, mail: str, course_id: str) -> (bool, str):
        # check fields all filled
        success = ((lastname is not None) and (lastname != ""))
        message = "Erreur : Le nom de famille n'est pas renseigné" if not success else ""
        if success:
            success = ((firstname is not None) and (firstname != ""))
            message = "Erreur : Le prénom n'est pas renseigné" if not success else ""
        if success:
            success = ((mail is not None) and (mail != ""))
            message = "Erreur : L'adresse mail n'est pas renseignée" if not success else ""
        if success:
            success = ((course_id is not None) and (course_id != ""))
            message = "Erreur : La formation n'est pas renseignée" if not success else ""
        # check neither label nor spreadsheet already exists in Courses
        if success:
            success = (Student.query.filter_by(mail=mail).count() == 0)
            message = "Erreur : Un(e) étudiant(e) avec le même mail existe déjà" if not success else ""
        # TODO check mail coherent
        if success:
            try:
                newstudent = Student(lastname=lastname, firstname=firstname, mail=mail, course_id=course_id)
                db.session.add(newstudent)
                db.session.commit()
                message = f"Succès : Etudiant(e) {newstudent.lastname} {newstudent.firstname} ajouté(e)"
            except Exception as ex:
                db.session.rollback()
                success = False
                message = str(ex)
        return success, message

    @classmethod
    def delete(cls, studentid: str) -> (bool, str):
        # check field filled and no dependent data exist
        success = ((studentid is not None) and (studentid != ""))
        message = "Erreur : L'étudiant(e) n'est pas renseigné(e)" if not success else ""
        if success:
            success = studentid.isnumeric()
            message = "Erreur : L'id d'étudiant(e) n'est pas numérique" if not success else ""
        if success:
            studenttodel = Student.query.get(int(studentid))
            success = (studenttodel is not None)
            message = "Erreur : Etudiant(e) inexistant(e)" if not success else ""
        if success:
            success = ((studenttodel.answers is None) or (len(studenttodel.answers) == 0))
            message = "Erreur : Des formulaires sont rattachés à cet(te) étudiant(e)" if not success else ""
        if success:
            try:
                db.session.delete(studenttodel)
                db.session.commit()
                message = f"Succès: Etudiant(e) {studenttodel.label} supprimé(e)"
            except Exception as ex:
                db.session.rollback()
                success = False
                message = str(ex)
        return success, message


class DbForm:

    @classmethod
    def createfromsheet(cls, courseid: int, sheet: gspread.models.Worksheet) -> Form:
        newform = Form(sheetid=sheet.id,
                       sheetlabel=sheet.title,
                       lastentrydate=datetime.today(),          # default before reading answers
                       lastreaddate=datetime.today(),
                       course_id=courseid)
        return newform

    @classmethod
    def queryspreadsheets(cls, minenddate: date) -> Query:
        today = datetime.today()
        xminenddate = date(MINYEAR, 1, 1)
        if minenddate is not None:
            xminenddate = minenddate
        # subquery aggregating data from Form
        groupedform = db.session.query(
            Form.course_id.label("course_id"),
            func.count(Form.id).label("sheetcount"),
            func.max(Form.lastentrydate).label("lastentrydate"),
            func.max(Form.lastreaddate).label("lastreaddate")
        ).group_by(Form.course_id).subquery()
        # query joining Course and subquery
        res = db.session.query(
            Course,
            groupedform,
            ((Course.spreadsheet != "") and (Course.enddate >= xminenddate)).label("check"),
            ((Course.enddate >= xminenddate) + (Course.startdate > today)).label("order")
        ).outerjoin(
            groupedform,
            Course.id == groupedform.c.course_id
        ).order_by(
            Course.startdate
        )
        return res

    @classmethod
    def querysheets(cls, minenddate: date, daysnochange: int) -> Query:
        deltadays = timedelta(days=daysnochange)
        res = db.session.query(
            Course,
            Form,
            func.count(Answer.id).label("answercount"),
            ((Form.lastreaddate - Form.lastentrydate) <= deltadays).label("check"),
        ).outerjoin(
            Form,
            Course.id == Form.course_id
        ).outerjoin(
            Answer,
            Form.id == Answer.form_id
        ).group_by(
            Course.id,                  # in case a course has no file => should not appear anyway, so theoretical
            Form.id
        ).filter(
            Course.spreadsheet != "",
            Course.enddate > minenddate,
            Course.startdate <= datetime.today()
        ).order_by(
            Course.startdate,
            Form.id
        )
        return res

    @classmethod
    def update(cls, minenddate: date, daysnochange: int) -> dict:
        successes = {}
        success = (minenddate is not None)
        if not success:
            successes["allfiles"] = (success, "Erreur : Aucune date de fin définie pour les formations à ignorer")
        if success:
            success = (daysnochange <= 0)
            if not success:
                successes["allfiles"] = (success, "Erreur : Aucun délai de stabilité défini pour les onglets à ignorer")
        if success:
            courses_list = db.session.query(Course).filter(
                Course.spreadsheet != "",
                Course.enddate > minenddate,
                Course.startdate <= datetime.today()
            )
            api = ApiFile()
            for course in courses_list:
                success, message, file = api.getfile(name=course.spreadsheet)
                if not success:
                    successes[course.spreadsheet] = (success, message)
                else:
                    gforms_list = db.session.query(Form).filter(
                        Form.course_id == course.id)
                    sheets = file.worksheets()
                    for sheet in sheets:
                        sheetdata = sheet.get_all_records()
                        gform = gforms_list.filter(Form.sheetid == sheet.id).first()
                        if (gform is None) and (sheetdata is not None) and (sheetdata != {}):
                            newgform = cls.createfromsheet(courseid=course.id, sheet=sheet)
                            db.session.add(newgform)
                            newquestions = DbQuestion.createfromsheet(course=course,
                                                                      sheetdata=sheetdata)
                            for question in newquestions:
                                db.session.add(question)
                            newanswers = DbAnswer.createfromsheet(course=course,
                                                                  sheetdata=sheetdata)
                            newgform.answers.append(newanswers)
                            db.session.commit()
                        # TODO cas gform non None

                # read Form in DB
                # loop through sheets
                #   check if sheet should be read
                #   if yes:
                #       read questions and save if new ones
                #       read answers and save if new ones
                #       update Form with lastentrydate
                #   in any case update lastreaddate
            # sheets_list =cls.querysheets(minenddate=minenddate,
            #                              daysnochange=daysnochange)
        return successes


class DbAnswer:

    @classmethod
    def createfromsheet(cls, course: Course, sheetdata: dict) -> List[Answer]:
        answers = []
        studentsdict = dict([(student.mail.strip(), student.id) for student in course.students])
        questionsdict = dict([(question.text.strip(), question.id) for question in course.questions])
        for row in sheetdata:
            tempanswers = []
            tempstudentid = None
            tempdatetime = None
            for header, value in row.items()[2:]:
                if header.strip() in questionsdict:
                    tempanswers.append((questionsdict[header.strip()], value))
                elif header.strip() in studentsdict:
                    tempstudentid = studentsdict[value.strip()]
                else:
                    tempdatetime = datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
            if tempstudentid is None:
                pass                        # TODO error message
            elif tempdatetime is None:
                pass                        # TODO error message
            else:
                for tempanswer in tempanswers:
                    newanswer = Answer(timestamp=tempdatetime, text=tempanswer[1],
                                       student_id=tempstudentid,
                                       question_id=tempanswer[0])
                    answers.append(newanswer)
        return answers


class DbQuestion:

    @classmethod
    def createfromsheet(cls, course: Course, sheetdata: dict) -> List[Question]:
        questions = []
        existingquestions = [question.text.strip() for question in course.questions]
        for index, text in enumerate(sheetdata[0].keys()):
            if index in (0, 1):
                pass
            elif text.strip() not in existingquestions:
                numint, numstr = 0, 0
                for row in sheetdata:
                    if (type(row[text]) == int) or (row[text].isnumeric()):
                        numint += 1
                    else:
                        numstr += 1
                newquestion = Question(isint=(numstr == 0), text=text,
                                       course_id=Course.id)
                questions.append(newquestion)
        return questions





