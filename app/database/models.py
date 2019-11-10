from app import db


# One course to many students and to many forms (one form per week at most)
class Course(db.Model):
    __tablename__ = 'Courses'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(80), unique=True, nullable=False)
    startdate = db.Column(db.Date, nullable=False)
    enddate = db.Column(db.Date, nullable=False)
    spreadsheet = db.Column(db.String(120), unique=True, nullable=False)

    students = db.relationship('Student', back_populates='course')
    questions = db.relationship('Question', back_populates='course')
    forms = db.relationship('Form', back_populates='course')

    def __repr__(self):
        return '<Course {} {}>'.format(self.id, self.label)


# Student
class Student(db.Model):
    __tablename__ = 'Students'

    id = db.Column(db.Integer, primary_key=True)
    lastname = db.Column(db.String(80), nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    mail = db.Column(db.String(80), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Courses.id'))

    course = db.relationship('Course', back_populates='students')
    answers = db.relationship('Answer', back_populates='student')

    def __repr__(self):
        return '<Student {} {} {}>'.format(self.id, self.firstname, self.lastname)


# One form corresponds to one sheet in a spreadsheet
# It collects the answers for one week from the students in one course
# One form is in a many to one database.relationship with a Course
class Form(db.Model):
    __tablename__ = 'Forms'

    id = db.Column(db.Integer, primary_key=True)
    sheetid = db.Column(db.String(80), nullable=False)
    sheetlabel = db.Column(db.String(80))
    lastentrydate = db.Column(db.Date)
    lastreaddate = db.Column(db.Date)
    course_id = db.Column(db.Integer, db.ForeignKey('Courses.id'))

    course = db.relationship('Course', back_populates='forms')
    answers = db.relationship('Answer', back_populates='form')

    def __repr__(self):
        return '<Sheet {} {}>'.format(self.id, self.label)


# Questions for each course (many to one)
# Question type is in fact answer type : grade (1 to 5), choice (non numeric), text
# Question type is inferred by the app
class Question(db.Model):
    __tablename__ = 'Questions'

    id = db.Column(db.Integer, primary_key=True)
    answertype = db.Column(db.Integer)
    text = db.Column(db.String(200), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('Courses.id'))

    course = db.relationship('Course', back_populates='questions')
    answers = db.relationship('Answer', back_populates='question')

    def __repr__(self):
        return '<Question {} {}>'.format(self.id, self.text)


# Answer : one answer per student per form (=> per week) per question
class Answer(db.Model):
    __tablename__ = 'Answers'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.String(1000))
    form_id = db.Column(db.Integer, db.ForeignKey('Forms.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('Students.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('Questions.id'))

    student = db.relationship('Student', back_populates='answers')
    question = db.relationship('Question', back_populates='answers')
    form = db.relationship('Form', back_populates='answers')

    def __repr__(self):
        return '<Answer {} {} {}>'.format(self.id, self.horodb.Dateur, self.reponse)
