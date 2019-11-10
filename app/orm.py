from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship


Base = declarative_base()


# One course to many students and to many forms (one form per week at most)
class Course(Base):
    __tablename__ = 'Courses'

    id = Column(Integer, primary_key=True)
    label = Column(String(80), unique=True, nullable=False)
    startdate = Column(Date, nullable=False)
    enddate = Column(Date, nullable=False)
    spreadsheet = Column(String(120), unique=True, nullable=False)

    students = relationship('Student', back_populates='course')
    questions = relationship('Question', back_populates='course')
    forms = relationship('Form', back_populates='course')

    def __repr__(self):
        return '<Course {} {}>'.format(self.id, self.label)


# Student
class Student(Base):
    __tablename__ = 'Students'

    id = Column(Integer, primary_key=True)
    lastname = Column(String(80), nullable=False)
    firstname = Column(String(80), nullable=False)
    mail = Column(String(80), unique=True, nullable=False)
    course_id = Column(Integer, ForeignKey('Courses.id'))

    course = relationship('Course', back_populates='students')
    answers = relationship('Answer', back_populates='student')

    def __repr__(self):
        return '<Student {} {} {}>'.format(self.id, self.firstname, self.lastname)


# One form corresponds to one sheet in a spreadsheet
# It collects the answers for one week from the students in one course
# One form is in a many to one relationship with a Course
class Form(Base):
    __tablename__ = 'Forms'

    id = Column(Integer, primary_key=True)
    sheetid = Column(String(80), nullable=False)
    sheetlabel = Column(String(80))
    lastentrydate = Column(Date)
    lastreaddate = Column(Date)
    course_id = Column(Integer, ForeignKey('Courses.id'))

    course = relationship('Course', back_populates='forms')
    answers = relationship('Answer', back_populates='form')

    def __repr__(self):
        return '<Sheet {} {}>'.format(self.id, self.label)


# Questions for each course (many to one)
# Question type is in fact answer type : grade (1 to 5), choice (non numeric), text
# Question type is inferred by the app
class Question(Base):
    __tablename__ = 'Questions'

    id = Column(Integer, primary_key=True)
    type = Column(Integer)
    text = Column(String(200), unique=True, nullable=False)
    course_id = Column(Integer, ForeignKey('Courses.id'))

    course = relationship('Course', back_populates='questions')
    answers = relationship('Answer', back_populates='question')

    def __repr__(self):
        return '<Question {} {}>'.format(self.id, self.text)


# Answer : one answer per student per form (=> per week) per question
class Answer(Base):
    __tablename__ = 'Answers'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    text = Column(String(1000))
    student_id = Column(Integer, ForeignKey('Students.id'))
    question_id = Column(Integer, ForeignKey('Questions.id'))
    form_id = Column(Integer, ForeignKey('Forms.id'))

    student = relationship('Student', back_populates='answers')
    question = relationship('Question', back_populates='answers')
    form = relationship('Form', back_populates='answers')

    def __repr__(self):
        return '<Answer {} {} {}>'.format(self.id, self.horodateur, self.reponse)