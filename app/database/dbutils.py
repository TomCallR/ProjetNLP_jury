import dataclasses
import math
from datetime import date, datetime, timedelta
from typing import List

import gspread
from flask import flash
from sqlalchemy import func
from sqlalchemy.orm import Query
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer

from app import db
from app.api.apiutils import ApiAccess
from app.apputils import Const, NumAnswer, Params, DTime, TextAnswer
from app.database.models import Course, Student, Form, Question, Answer


@dataclasses.dataclass
class CourseSummary:
    check: bool = False
    course: Course = None
    formscount: int = 0
    lastentrydt: datetime = None
    lastreaddt: datetime = None


@dataclasses.dataclass
class FormSummary:
    check: bool = False
    course: Course = None
    formscount: int = 0
    form: Form = None
    answerscount: int = 0


class Db:

    @classmethod
    def exists(cls) -> bool:
        try:
            coursecount = db.session.query(Course).count()
        except Exception as ex:
            coursecount = -1
        return coursecount >= 0


class DbCourse:

    @classmethod
    def querycurrent(cls, minenddate: datetime) -> Query:
        courses = None
        try:
            courses = db.session.query(Course).filter(
                Course.enddate > minenddate,
                Course.startdate <= datetime.now()
            ).order_by(Course.startdate)
        except Exception as ex:
            flash(f"Erreur : {ex}")
        return courses

    @classmethod
    def querycourses(cls, minenddate: datetime) -> List[CourseSummary]:
        res = []
        today = datetime.now()
        limitdate = DTime.min() if minenddate is None else minenddate
        courses = None
        try:
            courses = db.session.query(Course).order_by(Course.id)
        except Exception as ex:
            flash(f"Erreur : {ex}")
        if courses is not None:
            for course in courses:
                check = (course.enddate > limitdate) and (course.startdate <= today)
                formscount = len(course.forms)
                lastentrydt = DTime.min()
                lastreaddt = DTime.min()
                for form in course.forms:
                    if form.lastentrydt and form.lastentrydt > lastentrydt:
                        lastentrydt = form.lastentrydt
                    if form.lastreaddt and form.lastreaddt > lastreaddt:
                        lastreaddt = form.lastreaddt
                newcourse = CourseSummary(
                    check=check,
                    course=course,
                    formscount=formscount,
                    lastentrydt=lastentrydt,
                    lastreaddt=lastreaddt
                )
                res.append(newcourse)
            res.sort(key=(lambda c: (1 - int(c.check), -c.formscount, c.course.id)))
        return res

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
        if success:
            success = (fileid is not None and fileid != "")
            message = "Erreur : Le fichier des formulaires n'est pas renseigné" if not success else ""
        # check dates coherent
        if success:
            success = (startdate <= enddate)
            message = "Erreur : La date de début est postérieure à la date de fin" if not success else ""
        # check fileid does not already exist in Courses
        if success:
            success = (db.session.query(Course).filter(Course.fileid == fileid).count() == 0)
            message = "Erreur : Une formation avec le même id de fichier existe déjà" if not success else ""
        if success:
            # try to read file
            apiaccess = ApiAccess()
            spreadsheet = apiaccess.getfile(fileid)
            success = (spreadsheet is not None)
            metadata = None
            if success:
                # get metadata
                metadata = apiaccess.getmetadata(spreadsheet)
                success = (metadata is not None)
            if success:
                timezone = metadata["properties"]["timeZone"]
                # insert new course
                try:
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
            try:
                coursetodel = db.session.query(Course).get(int(courseid))
            except Exception as ex:
                flash(f"Erreur : {ex}")
            success = (coursetodel is not None)
            message = "Erreur : Formation inexistante" if not success else ""
        if success:
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
    def queryforms(cls, minenddate: datetime, daysnochange: int) -> List:
        res = []
        limitdate = DTime.min() if minenddate is None else minenddate
        courses = None
        try:
            courses = db.session.query(Course).filter(
                Course.filename != "",
                Course.enddate > limitdate,
                Course.startdate <= datetime.now()
            ).order_by(Course.id)
        except Exception as ex:
            flash(f"Erreur : {ex}")
        if courses is not None:
            for course in courses:
                formscount = len(course.forms)
                if formscount == 0:
                    newform = FormSummary(
                        check=True,
                        course=course,
                        formscount=formscount
                    )
                    res.append(newform)
                else:
                    for form in course.forms:
                        check = (form.lastentrydt is None) or (form.lastreaddt is None)
                        if not check:
                            check = (DTime.timedelta2days(form.lastreaddt - form.lastentrydt) <= daysnochange)
                        studentsdict = {answer.student_id: 1 for answer in form.answers}
                        answerscount = len(studentsdict.keys())
                        newform = FormSummary(
                            check=check,
                            course=course,
                            formscount=formscount,
                            form=form,
                            answerscount=answerscount
                        )
                        res.append(newform)
            res.sort(key=(lambda f: (1 - int(f.check), -f.formscount, f.course.id)))
        return res

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
    def updatedates(cls, gform: Form) -> bool:
        lastentrydt = None
        try:
            lastentrydt = db.session.query(
                func.max(Answer.timestamp).label("lastentrydt")
            ).filter(
                Answer.form_id == gform.id
            ).group_by(Answer.form_id).first()
        except Exception as ex:
            flash(f"Erreur : {ex}")
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
                file = apiaccess.getfile(fileid=course.fileid)
                if file is None:
                    flash(f"Erreur : Fichier {course.label} non trouvé")
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
                wsheetdata = ApiAccess.getwsheetdata(wsheet)
                if wsheetdata:
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
    def createfromsheet(cls, course: Course, wsheetdata: List[dict]):
        existingquestions = [question.text.strip() for question in course.questions]
        for text in wsheetdata[0].keys():
            if text.strip() in [ApiAccess.TIMESTAMP_HEADER, ApiAccess.EMAIL_HEADER]:
                pass
            elif text.strip() not in existingquestions:
                numint, numstr = 0, 0
                for row in wsheetdata:
                    if (type(row[text]) == int) or (row[text].isnumeric()):
                        numint += 1
                    else:
                        numstr += 1
                isint = Const.DBTRUE if numstr == 0 else Const.DBFALSE
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
    def updatefromsheet(cls, gform: Form, wsheetdata: List[dict]) -> bool:
        success = False
        if gform is not None and wsheetdata != []:
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
    forms_list: List[Form]
    questions_list: List[Question]
    startdate: datetime
    enddate: datetime

    @classmethod
    def querycriteria(cls):
        course_ids = Params.getsessionvar(Const.DASHBOARD_COURSE_IDS, default=[])
        if not course_ids:
            courses = db.session.query(Course).all()
            course_ids = [c.id for c in courses]
        else:
            courses = db.session.query(Course).filter(Course.id.in_(course_ids)).all()
        student_ids = Params.getsessionvar(Const.DASHBOARD_STUDENT_IDS, default=[])
        if not student_ids:
            students = db.session.query(Student).all()
            student_ids = [s.id for s in students]
        else:
            students = db.session.query(Student).filter(Student.id.in_(student_ids)).all()
        jsonstartdate = Params.getsessionvar(Const.DASHBOARD_STARTDATE, default=[2000, 1, 1])
        startdate = DTime.datetimedecode(jsonstartdate)
        jsonenddate = Params.getsessionvar(Const.DASHBOARD_ENDDATE, default=[2100, 1, 1])
        enddate = DTime.datetimedecode(jsonenddate)
        # prepare forms and questions too
        forms = db.session.query(Form).filter(
            Form.course_id.in_(course_ids),
            Form.lastentrydt >= startdate,
            Form.lastentrydt <= enddate
        ).order_by(Form.id).all()
        questions = db.session.query(Question).filter(
            Question.course_id.in_(course_ids)
        ).order_by(Question.id).all()
        # create instance loaded with data
        instance = cls(courses_list=courses, students_list=students, startdate=startdate, enddate=enddate,
                       forms_list=forms, questions_list=questions)
        return instance

    def querynumanswers(self) -> List[NumAnswer]:
        res = list()
        form_ids = [f.id for f in self.forms_list]
        student_ids = [s.id for s in self.students_list]
        questions = [q for q in self.questions_list if q.isint == Const.DBTRUE]
        question_ids = [q.id for q in questions]
        answers = db.session.query(Answer).filter(
            Answer.form_id.in_(form_ids),
            Answer.student_id.in_(student_ids),
            Answer.question_id.in_(question_ids)
        ).order_by(Answer.question_id)
        #
        for question in questions:
            grades = [int(answer.text) for answer in answers.filter(Answer.question_id == question.id)]
            gradecount = len(grades)
            grademax = 0
            gradesum = 0
            for grade in grades:
                grademax = grade if grade > grademax else grademax
                gradesum += grade
            gradeaverage = gradesum / gradecount if gradecount > 0 else math.nan
            res.append(NumAnswer(questiontext=question.text, grades=grades,
                                 max=grademax, count=gradecount, average=gradeaverage))
        return res

    def querytextanswers(self) -> List[TextAnswer]:
        res = list()
        form_ids = [f.id for f in self.forms_list]
        student_ids = [s.id for s in self.students_list]
        questions = [q for q in self.questions_list if q.isint == Const.DBFALSE]
        question_ids = [q.id for q in questions]
        answers = db.session.query(Answer).filter(
            Answer.form_id.in_(form_ids),
            Answer.student_id.in_(student_ids),
            Answer.question_id.in_(question_ids)
        ).order_by(Answer.question_id)
        #
        # see example https://github.com/sloria/textblob-fr

        for question in questions:
            polvalues = list()
            subvalues = list()
            texts = [answer.text for answer in answers.filter(Answer.question_id == question.id)]
            for text in texts:
                blob = TextBlob(text, pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
                qsentiment = blob.sentiment
                polvalues.append(qsentiment[0])
                subvalues.append(qsentiment[1])
            res.append(TextAnswer(questiontext=question.text, polarities=polvalues,
                                  subjectivities=subvalues))
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
