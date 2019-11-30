import dataclasses
import math
from datetime import date, datetime, MINYEAR, timedelta
from enum import Enum
from typing import Union, List

import gspread
from flask import flash, session
from sqlalchemy import func, and_
from sqlalchemy.orm import Query

from app import db
from app.api.apiutils import ApiAccess
from app.database.models import Course, Student, Form, Question, Answer, Parameter
from app.params import Const, NumAnswers, DateDecoder


class ParamName(Enum):
    MAX_DAYS_SHEET_NOT_CHANGED = "MAX_DAYS_SHEET_NOT_CHANGED"
    MAX_DELTA_TO_ENDDATE = "MAX_DELTA_TO_ENDDATE"


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
    def getparam(cls, name: str) -> (bool, str):
        success = False
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            try:
                res = str(getattr(ApiAccess, name))
                success = True
            except Exception as ex:
                res = None
                success = False
        else:
            res = param.value
            success = True
        return success, res

    @classmethod
    def setparam(cls, name: str, value: Union[int, str]) -> bool:
        success = False
        param = db.session.query(Parameter).filter(Parameter.name == name).first()
        if param is None:
            newparam = Parameter(name=name, value=str(value))
            try:
                db.session.add(newparam)
                db.session.commit()
                success = True
            except Exception as ex:
                db.session.rollback()
                success = False
                flash(f"Erreur : Impossible d'ajouter le paramètre {name}")
        else:
            param.value = str(value)
            try:
                db.session.commit()
                success = True
            except Exception as ex:
                db.session.rollback()
                success = False
                flash(f"Erreur : Impossible de mettre à jour le paramètre {name}")
        return success


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
            success, spreadsheet = apiaccess.getfile(fileid)
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
    def createfromsheet(cls, course: Course, wsheet: gspread.models.Worksheet) -> bool:
        success = False
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
                flash(f"Succès: Onglet {wsheet.title} ajouté en base (formation {course.label}, " +
                      f"fichier {course.filename})")
            except Exception as ex:
                db.session.rollback()
                flash(f"Erreur: Echec de l'ajout de l'onglet {wsheet.title} en base (formation " +
                      f"{course.label}, fichier {course.filename}). Exception : {ex}")
                success = False
        return success

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
        # subquery Answer aggregating data
        answersubquery = db.session.query(
            Answer.form_id.label("form_id"),
            Answer.student_id.label("student_id")
        ).group_by(
            Answer.form_id,
            Answer.student_id
        ).subquery()
        # join with Course and Form
        res = db.session.query(
            Course,
            Form,
            func.count(answersubquery.c.student_id).label("answercount"),
            ((Form.lastreaddt - Form.lastentrydt) <= deltadays).label("check"),
        ).outerjoin(
            Form,
            Course.id == Form.course_id
        ).outerjoin(
            answersubquery,
            Form.id == answersubquery.c.form_id
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
    def updatedates(cls, gform: Form) -> bool:
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
            success = True
        except Exception as ex:
            db.session.rollback()
            success = False
            flash(f"Erreur : Echec de mise à jour des dates du formulaire (formation {gform.course.label}, " +
                  f"fichier {gform.course.filename}, onglet {gform.sheetlabel})")
        return success

    @classmethod
    def updateall(cls, minenddate: datetime, daysnochange: int) -> bool:
        success = (minenddate is not None)
        if not success:
            flash("Erreur : Aucune date de fin de formation définie")
        if success:
            success = (daysnochange >= 0)
            if not success:
                flash("Erreur : Aucun délai de stabilité défini pour les onglets à ignorer")
        if success:
            courses_list = DbCourse.querycurrent(minenddate=minenddate)
            apiaccess = ApiAccess()
            for course in courses_list:
                success, file = apiaccess.getfile(fileid=course.fileid)
                if not success:
                    success = True  # there might be success with other files
                else:
                    wsheets = file.worksheets()
                    for wsheet in wsheets:
                        success = cls.update(course=course, daysnochange=daysnochange, wsheet=wsheet)
                        success = True  # there might be success with other sheets / files
        return success

    @classmethod
    def update(cls, course: Course, daysnochange: int, wsheet: gspread.Worksheet) -> bool:
        gformsdict = {gform.sheetid: gform for gform in course.forms}
        success = (wsheet.id in gformsdict)
        if not success:
            success = cls.createfromsheet(course=course, wsheet=wsheet)
        if success:
            gformsdict = {gform.sheetid: gform for gform in course.forms}
            gform = gformsdict[wsheet.id]
            if gform.lastentrydt >= gform.lastreaddt - timedelta(days=daysnochange):
                wsheetdata = wsheet.get_all_records()
                if (wsheetdata is not None) and (wsheetdata != {}):
                    DbQuestion.createfromsheet(course=course, wsheetdata=wsheetdata)
                    success = DbAnswer.updatefromsheet(gform=gform, wsheetdata=wsheetdata)
                    if success:
                        try:
                            db.session.commit()
                            success = True
                            flash(f"Succès : Réponses mises à jour (formation {course.label}, " +
                                  f"fichier {course.filename}, onglet {gform.sheetlabel})")
                        except Exception as ex:
                            db.session.rollback()
                            success = False
                            flash(f"Erreur : Echec de la mise à jour des réponses (formation {course.label}, " +
                                  f"fichier {course.filename}, onglet {gform.sheetlabel})")
                        if success:
                            success = cls.updatedates(gform=gform)
        return success


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
                      studentsdict: dict, questionsdict: dict, answersdict: dict) -> bool:
        timestamp = datetime.strptime(row[tsheader].strip(), "%d/%m/%Y %H:%M:%S")  # TODO securiser
        email = row[emailheader].strip()
        success = (email in studentsdict)
        if not success:
            flash(f"Erreur : Email {email} inconnu dans le fichier {gform.course.filename}, " +
                  f"onglet {gform.sheetlabel}, réponse ignorée")
        else:
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
        return success

    @classmethod
    def updatefromsheet(cls, gform: Form, wsheetdata: dict) -> bool:
        success = False
        if gform is not None and wsheetdata is not None and wsheetdata != []:
            tsheader = ApiAccess.TIMESTAMP_HEADER
            emailheader = ApiAccess.EMAIL_HEADER
            success = ((tsheader in wsheetdata[0]) and (emailheader in wsheetdata[0]))
            if not success:
                flash(f"Erreur : Entêtes pour l'horodatage et/ou l'email non trouvés " +
                      f"(formation {gform.course.label}, fichier {gform.course.filename}, " +
                      f"onglet {gform.sheetlabel})")
            else:
                course = gform.course
                studentsdict = {student.email.strip(): student for student in course.students}
                questionsdict = {question.text.strip(): question for question in course.questions}
                answersdict = {(answer.student_id, answer.question_id): answer for answer in gform.answers}
                for index, row in enumerate(wsheetdata):
                    success = cls.updatefromrow(gform=gform, row=row, tsheader=tsheader,
                                                emailheader=emailheader, studentsdict=studentsdict,
                                                questionsdict=questionsdict, answersdict=answersdict)
        return success


@dataclasses.dataclass()
class Dashboard:
    courses_list: List[Course]
    students_list: List[Student]
    startdate: datetime
    enddate: datetime

    # forms: List[Form] = None

    @classmethod
    def querycriteria(cls):
        course_ids = session["DASHBOARD_COURSE_IDS"]
        if not course_ids:
            courses = db.session.query(Course).all()
        else:
            courses = db.session.query(Course).filter(Course.id.in_(course_ids))
        student_ids = session["DASHBOARD_STUDENT_IDS"]
        if not student_ids:
            students = db.session.query(Student).all()
        else:
            students = db.session.query(Student).filter(Student.id.in_(student_ids))
        # sdate = session["DASHBOARD_STARTDATE"]
        # startdate = date(year=sdate[0], month=sdate[1], day=sdate[2])
        startdate = DateDecoder.decode(session["DASHBOARD_STARTDATE"])
        # edate = session["DASHBOARD_ENDDATE"]
        enddate = DateDecoder.decode(session["DASHBOARD_ENDDATE"])
        instance = cls(courses_list=courses, students_list=students, startdate=startdate, enddate=enddate)
        return instance

    def queryanswers(self) -> List:
        res = list()
        course_ids = [] if self.courses_list is None else [c.id for c in self.courses_list]
        forms = db.session.query(Form).filter(
            Course.id.in_(course_ids),
            Form.lastentrydt >= self.startdate,
            Form.lastentrydt <= self.enddate
        )
        # for form in forms:
        #     print(form.sheetlabel)
        #     print(Form.lastentrydt >= self.startdate)
        #     print(Form.lastentrydt <= self.enddate)
        form_ids = [f.id for f in forms]
        student_ids = [] if self.students_list is None else [s.id for s in self.students_list]
        answers = db.session.query(Answer).filter(
            Answer.form_id.in_(form_ids),
            Answer.student_id.in_(student_ids)
        ).order_by(Answer.question_id)
        questions = list({a.question for a in answers})
        questions.sort(key=(lambda q: q.id))
        numquestions = [q for q in questions if q.isint == Const.DBTRUE]
        for question in numquestions:
            grades = [int(answer.text) for answer in answers.filter(Answer.question_id == question.id)]
            gradecount = len(grades)
            gradesum = 0
            for grade in grades:
                gradesum += grade
            gradeaverage = gradesum / gradecount if gradecount > 0 else math.nan
            res.append(NumAnswers(questiontext=question.text, grades=grades,
                                  count=gradecount, average=gradeaverage))
        return res

    @classmethod
    def wraptext(cls, text: str, maxlen: int) -> str:
        words = text.split()
        failure = len([w for w in words if len(w) > maxlen]) > 0
        if failure:
            res = text
        else:
            lines = []
            while len(words) > 0:
                line = [words[0]]
                size = len(line[0])
                words.pop(0)
                while len(words) > 0 and (size + 1 + len(words[0]) <= maxlen):
                    line.append(words[0])
                    size = size + 1 + len(words[0])
                    words.pop(0)
                lines.append(line)
            res = "\n".join([" ".join(line) for line in lines])
        return res


