import os
import unittest
from datetime import datetime

from app import app, db
from app.database.models import Course, Student

TEST_DB = "test.db"
PRIVATEDIR = "D:/Git/ProjetNLP_jury/private"


class BasicTests(unittest.TestCase):

    # executed prior to each test
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(PRIVATEDIR, TEST_DB)
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

        self.assertEqual(app.debug, False)

    # executed after each test
    def tearDown(self):
        pass

    def test_index_page(self):
        response = self.app.get("/", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_new_course_page(self):
        response = self.app.post("/course/create",
                                 data=dict(label="Data Analyst",
                                           startdate=datetime(year=2019, month=3, day=18).date(),
                                           enddate=datetime(year=2019, month=12, day=3).date(),
                                           fileid="1f9UU0D9B55Yv4s8qNGx_rLBE9C6vXxSdnjE3Wjvrm7A"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200, msg="Formation DA créée")
        response = self.app.post("/course/create",
                                 data=dict(label="Java",
                                           startdate=datetime(year=2019, month=2, day=4).date(),
                                           enddate=datetime(year=2019, month=7, day=2).date(),
                                           fileid="1JIPYREs3XuzdOYIPD8SbUrnz0hz4MIpDL8EbHsPwd2k"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200, msg="Formation Java créée")
        response = self.app.post("/course/create",
                                 data=dict(label="Anglais",
                                           startdate=datetime(year=2019, month=9, day=2).date(),
                                           enddate=datetime(year=2020, month=1, day=31).date(),
                                           fileid="1TuyCIispLGANs1rxzXqrsPdzK_Rn9Qis5XHD2zxLms0"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200, msg="Formation Anglais créée")

    def test_new_student_page(self):
        response = self.app.post("/course/create",
                                 data=dict(label="Data Analyst",
                                           startdate=datetime(year=2019, month=3, day=18).date(),
                                           enddate=datetime(year=2019, month=12, day=3).date(),
                                           fileid="1f9UU0D9B55Yv4s8qNGx_rLBE9C6vXxSdnjE3Wjvrm7A"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.app.post("/course/create",
                                 data=dict(label="Java",
                                           startdate=datetime(year=2019, month=2, day=4).date(),
                                           enddate=datetime(year=2019, month=7, day=2).date(),
                                           fileid="1JIPYREs3XuzdOYIPD8SbUrnz0hz4MIpDL8EbHsPwd2k"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = self.app.post("/course/create",
                                 data=dict(label="Anglais",
                                           startdate=datetime(year=2019, month=9, day=2).date(),
                                           enddate=datetime(year=2020, month=1, day=31).date(),
                                           fileid="1TuyCIispLGANs1rxzXqrsPdzK_Rn9Qis5XHD2zxLms0"),
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        dacourse = db.session.query(Course).filter(Course.label == "Data Analyst").first()
        courseid = dacourse.id
        students = list()
        students.append(Student(lastname='Un', firstname='Jean', email='e1@gmail.com', course_id=courseid))
        students.append(Student(lastname='Deux', firstname='Claire', email='e2@gmail.com', course_id=courseid))
        students.append(Student(lastname='Trois', firstname='Pierre', email='e3@gmail.com', course_id=courseid))
        students.append(Student(lastname='Quatre', firstname='Sophie', email='e4@gmail.com', course_id=courseid))
        students.append(Student(lastname='Cinq', firstname='Jacques', email='e5@gmail.com', course_id=courseid))
        students.append(Student(lastname='Six', firstname='Christelle', email='e6@gmail.com', course_id=courseid))
        students.append(Student(lastname='Sept', firstname='Laurent', email='e7@gmail.com', course_id=courseid))
        students.append(Student(lastname='Huit', firstname='Lucile', email='e8@gmail.com', course_id=courseid))
        students.append(Student(lastname='Neuf', firstname='Nicolas', email='e9@gmail.com', course_id=courseid))
        students.append(Student(lastname='Dix', firstname='Anne', email='e10@gmail.com', course_id=courseid))
        students.append(Student(lastname='Onze', firstname='Matthieu', email='e11@gmail.com', course_id=courseid))
        students.append(Student(lastname='Douze', firstname='Sébastien', email='e12@gmail.com', course_id=courseid))
        dacourse = db.session.query(Course).filter(Course.label == "Anglais").first()
        courseid = dacourse.id
        students.append(Student(lastname='Smith', firstname='Adam', email='adam@gmail.com', course_id=courseid))
        students.append(Student(lastname='Hayek', firstname='Friedrich', email='friedrich@gmail.com', course_id=courseid))
        students.append(Student(lastname='Keynes', firstname='John', email='john@gmail.com', course_id=courseid))
        students.append(Student(lastname='Marx', firstname='Karl', email='karl@gmail.com', course_id=courseid))
        for student in students:
            response = self.app.post("/student/create",
                                     data=dict(lastname=student.lastname,
                                               firstname=student.firstname,
                                               email=student.email,
                                               course=str(student.course_id)),
                                     follow_redirects=True)
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
