from datetime import date
from operator import or_

from app import db
from app.database.models import Course, Student, Form, Question, Answer


class DbCourse:
    @classmethod
    def insert(cls, label: str, startdate: date, enddate: date, spreadsheet: str):
        # checks dates coherent
        success = startdate <= enddate
        message = "Erreur : La date de début est postérieure à la date de fin" if not success else ""
        # check neither label nor spreadsheet already exists in Courses
        success = Course.query.filter_by(label=label).count() == 0
        message = "Erreur : Une formation avec le même intitulé existe déjà" if not success else ""
        success = Course.query.filter_by(spreadsheet=spreadsheet).count() == 0
        message = "Erreur : Une formation avec le même fichier associé existe déjà" if not success else ""
        if success:
            newcourse = Course(label=label, startdate=startdate, enddate=enddate, spreadsheet=spreadsheet)
            db.session.add(newcourse)
            db.session.commit()
        return success, message

    @classmethod
    def delete(cls, courseid: str):
        coursetodel = Course.query.get(int(courseid))
        success = coursetodel is not None
        message = "Erreur : Formation inexistante" if not success else ""
        if success:
            success = len(coursetodel.students) == 0
            message = "Erreur : Des élèves sont liés à cette formation" if not success else ""
        if success:
            success = len(coursetodel.forms) == 0
            message = "Erreur : Des formulaires sont liés à cette formation" if not success else ""
        if success:
            success = len(coursetodel.questions) == 0
            message = "Erreur : Des questions sont liées à cette formation" if not success else ""
        if success:
            db.session.delete(coursetodel)
            db.session.commit()
        return success, message
