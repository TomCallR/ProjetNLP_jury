from datetime import date
from operator import or_

from app import db
from app.database.models import Course, Student, Form, Question, Answer


class DbCourse:

    @classmethod
    def insert(cls, label: str, startdate: date, enddate: date, spreadsheet: str):
        # check fields all filled
        success = (label != "")
        message = "Erreur : L'intitulé n'est pas renseigné" if not success else ""
        if success:
            success = (startdate is not None)
            message = "Erreur : La date de début n'est pas renseignée" if not success else ""
        if success:
            success = (enddate is not None)
            message = "Erreur : La date de fin n'est pas renseignée" if not success else ""
        if success:
            success = (spreadsheet != "")
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
    def delete(cls, courseid: str):
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
            success = (coursetodel.students is not None)
            message = "Erreur : Des étudiants sont rattachés cette formation" if not success else ""
        if success:
            success = (coursetodel.questions is not None)
            message = "Erreur : Des questions sont liées à cette formation" if not success else ""
        if success:
            success = (coursetodel.forms is not None)
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
