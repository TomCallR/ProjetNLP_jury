from datetime import date, datetime, MINYEAR, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Query

from app import db
from app.database.models import Course, Student, Form, Question, Answer


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
    def querysheets(cls) -> Query:
        deltadays = timedelta(days=15.0)
        # subquery answers
        groupedanswer = db.session.query(
            Answer.form_id.label("form_id"),
            func.count(Answer.id).label("answercount")
        ).group_by(Answer.form_id).subquery()
        # subquery Form
        joinedform = db.session.query(
            Form,
            groupedanswer
        ).outerjoin(
            groupedanswer,
            Form.id == groupedanswer.form_id
        ).subquery()
        # query joining Course, subquery joinedform
        res = db.session.query(
            Course,
            joinedform,
            ((joinedform.c.lastreaddate - joinedform.c.lastentrydate) <= deltadays).label("check")
        ).outerjoin(
            joinedform,
            Course.id == joinedform.c.course_id
        ).order_by(
            Course.startdate,
            joinedform.c.id
        )
        # res = db.session.query(
        #     Course,
        #     Form,
        #     groupedanswer,
        #     ((Form.lastreaddate - Form.lastentrydate) <= deltadays).label("check"),
        # ).outerjoin(
        #     Form,
        #     Course.id == Form.course_id
        # ).outerjoin(
        #     groupedanswer,
        #     Form.id == groupedanswer.form_id
        # ).order_by(
        #     Course.startdate,
        #     Form.id
        # )
        return res


