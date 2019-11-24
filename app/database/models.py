from app import db


# One course to many students and to many forms (one form per week at most)
class Course(db.Model):
    __tablename__ = "Courses"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(80), nullable=False)
    startdate = db.Column(db.DateTime, nullable=False)
    enddate = db.Column(db.DateTime, nullable=False)
    fileid = db.Column(db.String(200), nullable=False, unique=True)
    filename = db.Column(db.String(120), nullable=False)        # TODO allow blank string
    filetz = db.Column(db.String(40), nullable=False)

    students = db.relationship("Student", back_populates="course")
    questions = db.relationship("Question", back_populates="course")
    forms = db.relationship("Form", back_populates="course")

    @property
    def __repr__(self):
        return "<Course {} {}>".format(self.id, self.label)


# Student
class Student(db.Model):
    __tablename__ = "Students"

    id = db.Column(db.Integer, primary_key=True)
    lastname = db.Column(db.String(80), nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    course_id = db.Column(db.Integer, db.ForeignKey("Courses.id"), nullable=False)

    course = db.relationship("Course", back_populates="students")
    answers = db.relationship("Answer", back_populates="student")

    def __repr__(self):
        return "<Student {} {}>".format(self.id, self.email)


# One form corresponds to one sheet in a spreadsheet
# It collects the answers for one week from the students in one course
# One form is in a many to one database.relationship with a Course
class Form(db.Model):
    __tablename__ = "Forms"

    id = db.Column(db.Integer, primary_key=True)
    sheetid = db.Column(db.Integer, nullable=False, unique=True)
    sheetlabel = db.Column(db.String(80), nullable=False)
    lastentrydt = db.Column(db.DateTime, nullable=False)
    lastreaddt = db.Column(db.DateTime, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("Courses.id"), nullable=False)

    course = db.relationship("Course", back_populates="forms")
    answers = db.relationship("Answer", back_populates="form")

    def __repr__(self):
        return "<Sheet {} {}>".format(self.id, self.sheetlabel)


# Questions for each course (many to one)
# Question type is in fact answer type : grade (1 to 5), choice (non numeric), text
# Question type is inferred by the app
class Question(db.Model):
    __tablename__ = "Questions"

    id = db.Column(db.Integer, primary_key=True)
    isint = db.Column(db.String(1), nullable=False)      # Y for integer, N for text
    text = db.Column(db.String(200), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("Courses.id"), nullable=False)

    course = db.relationship("Course", back_populates="questions")
    answers = db.relationship("Answer", back_populates="question")

    def __repr__(self):
        return "<Question {} {}>".format(self.id, self.text)


# Answer : one answer per student per form (=> per week) per question
class Answer(db.Model):
    __tablename__ = "Answers"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.String(1000), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey("Forms.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("Students.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("Questions.id"), nullable=False)

    student = db.relationship("Student", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")
    form = db.relationship("Form", back_populates="answers")

    def __repr__(self):
        return f"<Answer {self.id} {self.timestamp} {self.text}>"


# Parameter : stores user preferred values for some parameters, no link to other classes
class Parameter(db.Model):
    __tablename__ = "Parameters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    value = db.Column(db.String(1000), nullable=True)
