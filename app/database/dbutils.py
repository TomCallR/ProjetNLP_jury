from datetime import date, datetime, MINYEAR, timedelta
from typing import Union, List

import gspread
from sqlalchemy import func, and_
from sqlalchemy.orm import Query

from app import db
from app.api.apiutils import ApiAccess
from app.database.models import Course, Student, Form, Question, Answer, Parameter


class Db:

    @classmethod
    def exists(cls) -> bool:
        try:
            coursecount = db.session.query(Course).count()  # TODO à améliorer
        except Exception as ex:
            coursecount = -1
        return coursecount >= 0


class DbParam:

    @classmethod
    def getparam(cls, name: str) -> (bool, str, str):
        success = False
        message = ""
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            try:
                res = str(getattr(ApiAccess, name))
                success = True
            except Exception as ex:
                res = None
                message = f"Erreur : Valeur par défault du paramètre {name} non définie dans la configuration"
        else:
            res = param.value
            success = True
        return success, message, res

    @classmethod
    def setparam(cls, name: str, value: Union[int, str]) -> (bool, str):
        success = True
        message = ""
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            newparam = Parameter(name=name, value=str(value))
            try:
                db.session.add(newparam)
                db.session.commit()
            except Exception as ex:
                db.session.rollback()
                success = False
                message = f"Erreur : Impossible d'ajouter le paramètre {name}"
        else:
            param.value = str(value)
            try:
                db.session.commit()
            except Exception as ex:
                db.session.rollback()
                success = False
                message = f"Erreur : Impossible de mettre à jour le paramètre {name}"
        return success, message


class DbCourse:

    @classmethod
    def querycurrent(cls, minenddate: datetime) -> Query:
        courses = db.session.query(Course).filter(
            Course.filename != "",
            Course.enddate > minenddate,
            Course.startdate <= datetime.now()
        )
        return courses

    @classmethod
    def insert(cls, label: str, startdate: date, enddate: date, fileid: str) -> (bool, str):
        # check fields all filled
        success = (label is not None and label != "")
        message = "Erreur : L'intitulé n'est pas renseigné" if not success else ""
        if success:
            success = (startdate is not None)
            message = "Erreur : La date de début n'est pas renseignée" if not success else ""
        if success:
            success = (enddate is not None)
            message = "Erreur : La date de fin n'est pas renseignée" if not success else ""
        if success:  # TODO pas forcément au début
            success = (fileid is not None and fileid != "")
            message = "Erreur : Le fichier des formulaires n'est pas renseigné" if not success else ""
        # check dates coherent
        if success:
            success = (startdate <= enddate)
            message = "Erreur : La date de début est postérieure à la date de fin" if not success else ""
        # check fileid does not already exist in Courses
        if success:
            success = (Course.query.filter_by(fileid=fileid).count() == 0)
            message = "Erreur : Une formation avec le même id de fichier existe déjà" if not success else ""
        if success:
            # try to read file
            apiaccess = ApiAccess()
            success, message, spreadsheet = apiaccess.getfile(fileid)
            if success:
                # insert new course
                try:
                    metadata = spreadsheet.fetch_sheet_metadata()
                    timezone = metadata["properties"]["timeZone"]
                    newcourse = Course(label=label, startdate=startdate, enddate=enddate,
                                       fileid=fileid, filename=spreadsheet.title, filetz=timezone)
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
        coursetodel = None
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
    def insert(cls, lastname: str, firstname: str, email: str, course_id: str) -> (bool, str):
        # check fields all filled
        success = ((lastname is not None) and (lastname != ""))
        message = "Erreur : Le nom de famille n'est pas renseigné" if not success else ""
        if success:
            success = ((firstname is not None) and (firstname != ""))
            message = "Erreur : Le prénom n'est pas renseigné" if not success else ""
        if success:
            success = ((email is not None) and (email != ""))
            message = "Erreur : L'email n'est pas renseigné" if not success else ""
        if success:
            success = ((course_id is not None) and (course_id != ""))
            message = "Erreur : La formation n'est pas renseignée" if not success else ""
        # check neither label nor filename already exists in Courses
        if success:
            success = (Student.query.filter_by(email=email).count() == 0)
            message = "Erreur : Un(e) étudiant(e) avec le même email existe déjà" if not success else ""
        # TODO check mail coherent
        if success:
            try:
                newstudent = Student(lastname=lastname, firstname=firstname, email=email, course_id=course_id)
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
        studenttodel = None
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
                message = f"Succès: Etudiant(e) {studenttodel.email} supprimé(e)"
            except Exception as ex:
                db.session.rollback()
                success = False
                message = str(ex)
        return success, message


class DbForm:

    @classmethod
    def createfromsheet(cls, course: Course, wsheet: gspread.models.Worksheet) -> (bool, str):
        success = False
        message = ""
        if wsheet is not None:
            newform = Form(sheetid=wsheet.id,
                           sheetlabel=wsheet.title,
                           lastentrydt=datetime.now(tz=None),  # default before reading answers
                           lastreaddt=datetime.now(tz=None),
                           course_id=course.id)
            try:
                db.session.add(newform)
                db.session.commit()
                success = True
                message = f"Succès: Onglet {wsheet.title} ajouté en base (formation {course.label}, " \
                          f"fichier {course.filename})"
            except Exception as ex:
                db.session.rollback()
                message = f"Erreur: Echec de l'ajout de l'onglet {wsheet.title} en base (formation " \
                          f"{course.label}, fichier {course.filename}). Exception : {ex}"
        return success, message

    @classmethod
    def queryspreadsheets(cls, minenddate: datetime) -> Query:
        today = datetime.now()
        xminenddate = date(MINYEAR, 1, 1) if minenddate is None else minenddate
        # subquery Form aggregating data
        formsubquery = db.session.query(
            Form.course_id.label("course_id"),
            func.count(Form.id).label("sheetcount"),
            func.max(Form.lastentrydt).label("lastentrydt"),
            func.max(Form.lastreaddt).label("lastreaddt")
        ).group_by(
            Form.course_id
        ).subquery()
        # join with Course
        res = db.session.query(
            Course,
            formsubquery,
            (and_(Course.filename != "",
                  Course.enddate > xminenddate,
                  Course.startdate <= today)).label("check")
        ).outerjoin(
            formsubquery,
            Course.id == formsubquery.c.course_id
        ).order_by(
            ((Course.enddate > xminenddate) + (Course.startdate > today)),
            Course.startdate
        )
        return res

    @classmethod
    def querysheets(cls, minenddate: datetime, daysnochange: int) -> Query:
        deltadays = timedelta(days=daysnochange)
        res = db.session.query(
            Course,
            Form,
            func.count(Answer.id).label("answercount"),
            ((Form.lastreaddt - Form.lastentrydt) <= deltadays).label("check"),
        ).outerjoin(
            Form,
            Course.id == Form.course_id
        ).outerjoin(
            Answer,
            Form.id == Answer.form_id
        ).group_by(
            Course.id,
            Form.id
        ).filter(
            Course.filename != "",
            Course.enddate > minenddate,
            Course.startdate <= datetime.now()
        ).order_by(
            Course.startdate,
            Form.id
        )
        return res

    @classmethod
    def updatedates(cls, gform: Form) -> (bool, str):
        success = True
        message = ""
        lastentrydt = db.session.query(
            func.max(Answer.timestamp).label("lastentrydt")
        ).filter(
            Answer.form_id == gform.id
        ).group_by(Answer.form_id).first()
        if lastentrydt is not None:
            gform.lastentrydt = lastentrydt[0]
        gform.lastreaddt = datetime.now(tz=None)
        try:
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            success = False
            message = f"Erreur : Echec de mise à jour des dates du formulaire (formation {gform.course.label}, " \
                      f"fichier {gform.course.filename}, onglet {gform.sheetlabel})"
        return success, message

    @classmethod
    def updateall(cls, minenddate: datetime, daysnochange: int) -> (bool, List[str]):
        messages = []
        success = (minenddate is not None)
        message = "Erreur : Aucune date de fin définie pour les formations à ignorer" if not success else ""
        if not success:
            messages.append(message)
        if success:
            success = (daysnochange >= 0)
            message = "Erreur : Aucun délai de stabilité défini pour les onglets à ignorer" if not success else ""
            if not success:
                messages.append(message)
        if success:
            courses_list = DbCourse.querycurrent(minenddate=minenddate)
            apiaccess = ApiAccess()
            for course in courses_list:
                success, message, file = apiaccess.getfile(fileid=course.fileid)
                if not success:
                    messages.append(message)
                    success = True  # continue with other files
                else:
                    wsheets = file.worksheets()
                    for wsheet in wsheets:
                        success, message = cls.update(course=course, daysnochange=daysnochange, wsheet=wsheet)
                        messages.append(message)
                        success = True  # continue with other files
        return success, messages

    @classmethod
    def update(cls, course: Course, daysnochange: int, wsheet: gspread.Worksheet) -> (bool, str):
        success = True
        message = ""
        gformsdict = {gform.sheetid: gform for gform in course.forms}
        if wsheet.id not in gformsdict:
            success, message = cls.createfromsheet(course=course, wsheet=wsheet)
        if success:
            gformsdict = {gform.sheetid: gform for gform in course.forms}
            gform = gformsdict[wsheet.id]
            if gform.lastentrydt >= gform.lastreaddt - timedelta(days=daysnochange):
                wsheetdata = wsheet.get_all_records()
                if (wsheetdata is not None) and (wsheetdata != {}):
                    DbQuestion.createfromsheet(course=course, wsheetdata=wsheetdata)
                    success, message = DbAnswer.updatefromsheet(gform=gform, wsheetdata=wsheetdata)
                    if success:
                        try:
                            db.session.commit()
                            success = True
                            message = f"Succès : Réponses mises à jour (formation {course.label}, " \
                                      f"fichier {course.filename}, onglet {gform.sheetlabel})"
                        except Exception as ex:
                            db.session.rollback()
                            success = False
                            message = f"Erreur : Echec de la mise à jour des réponses (formation {course.label}, " \
                                      f"fichier {course.filename}, onglet {gform.sheetlabel})"
                        if success:
                            success, message = cls.updatedates(gform=gform)
        return success, message


class DbQuestion:

    @classmethod
    def createfromsheet(cls, course: Course, wsheetdata: dict):
        if wsheetdata is not None and wsheetdata != []:
            existingquestions = [question.text.strip() for question in course.questions]
            for index, text in enumerate(wsheetdata[0].keys()):
                if text.strip() in [ApiAccess.TIMESTAMP_HEADER, ApiAccess.EMAIL_HEADER]:
                    pass
                elif text.strip() not in existingquestions:
                    numint, numstr = 0, 0
                    for row in wsheetdata:
                        if (type(row[text]) == int) or (row[text].isnumeric()):
                            numint += 1
                        else:
                            numstr += 1
                    isint = "Y" if numstr == 0 else "N"
                    newquestion = Question(isint=isint, text=text, course_id=Course.id)
                    course.questions.append(newquestion)


class DbAnswer:

    @classmethod
    def updatefromrow(cls, gform: Form, row: dict, tsheader: str, emailheader: str,
                      studentsdict: dict, questionsdict: dict, answersdict: dict) -> (bool, str):
        timestamp = datetime.strptime(row[tsheader].strip(), "%d/%m/%Y %H:%M:%S")  # TODO securiser
        email = row[emailheader].strip()
        success = (email in studentsdict)
        message = f"Erreur : Email {email} inconnu dans le fichier {gform.course.filename}, " \
                  f"onglet {gform.sheetlabel}, réponse ignorée" if not success else ""
        if success:
            studentid = studentsdict[email].id
            for header, value in row.items():
                if header not in (tsheader, emailheader):
                    text = str(value).strip()
                    questionid = questionsdict[header].id
                    if (studentid, questionid) in answersdict:
                        answer = answersdict[(studentid, questionid)]
                        answer.timestamp = timestamp
                        answer.text = text
                    else:
                        newanswer = Answer(timestamp=timestamp, text=text, form_id=gform.id,
                                           student_id=studentid, question_id=questionid)
                        gform.answers.append(newanswer)
        return success, message

    @classmethod
    def updatefromsheet(cls, gform: Form, wsheetdata: dict) -> (bool, str):
        success = True
        message = ""
        if gform is not None and wsheetdata is not None and wsheetdata != []:
            tsheader = ApiAccess.TIMESTAMP_HEADER
            emailheader = ApiAccess.EMAIL_HEADER
            if tsheader not in wsheetdata[0] or emailheader not in wsheetdata[0]:
                success = False
                message = f"Erreur : Entêtes pour l'horodatage et/ou l'email non trouvés " \
                          f"(formation {gform.course.label}, fichier {gform.course.filename}, " \
                          f"onglet {gform.sheetlabel})"
            else:
                course = gform.course
                studentsdict = {student.email.strip(): student for student in course.students}
                questionsdict = {question.text.strip(): question for question in course.questions}
                answersdict = {(answer.student_id, answer.question_id): answer for answer in gform.answers}
                for index, row in enumerate(wsheetdata):
                    success, message = cls.updatefromrow(gform=gform, row=row, tsheader=tsheader,
                                                         emailheader=emailheader, studentsdict=studentsdict,
                                                         questionsdict=questionsdict, answersdict=answersdict)
        return success, message
