import datetime

from flask import flash, render_template, request, url_for, redirect

from app import app
from app.database.dbutils import DbCourse, DbStudent, DbForm
from app.database.models import Course, Student, Form
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/courses", methods=["GET"])
def courses():
    courses_list = Course.query.all()
    return render_template("courses.html", courses=courses_list)


@app.route("/course/create", methods=["GET", "POST"])
def course_create():
    form = CourseCreateForm()
    if form.validate_on_submit():
        success, message = DbCourse.insert(
            label=form.label.data,
            startdate=form.startdate.data,
            enddate=form.enddate.data,
            spreadsheet=form.spreadsheet.data
        )
        flash(message)
        if success:
            return redirect(url_for("courses"))
    return render_template("course_create.html", form=form)


@app.route("/course/delete", methods=["GET", "POST"])
def course_delete():
    courses_list = Course.query.all()
    form = CourseDeleteForm()
    form.course.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {course.startdate} au " \
                      f"{str(course.startdate)}, fichier {course.spreadsheet}"
        form.course.choices.append((str(course.id), displaytext))
    if form.validate_on_submit():
        success, message = DbCourse.delete(
            courseid=form.course.data)
        flash(message)
        if success:
            return redirect("/courses")
    return render_template("course_delete.html", form=form)


@app.route("/students", methods=["GET"])
def students():
    students_list = Student.query.all()
    return render_template("students.html", students=students_list)


@app.route("/student/create", methods=["GET", "POST"])
def student_create():
    courses_list = Course.query.all()
    form = StudentCreateForm()
    form.course.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {course.startdate} au " \
                      f"{str(course.startdate)}, fichier {course.spreadsheet}"
        form.course.choices.append((str(course.id), displaytext))
    if form.validate_on_submit():
        success, message = DbStudent.insert(
            lastname=form.lastname.data,
            firstname=form.firstname.data,
            mail=form.mail.data,
            course_id=form.course.data
        )
        flash(message)
        if success:
            return redirect(url_for("students"))
    return render_template("student_create.html", form=form)


@app.route("/student/delete", methods=["GET", "POST"])
def student_delete():
    students_list = Student.query.order_by(Student.course.label,
                                           Student.lastname,
                                           Student.firstname).all()
    form = StudentDeleteForm()
    form.student.choices = []
    for student in students_list:
        displaytext = f"{student.lastname} {str(student.firstname)}, " \
                      f"mail {student.mail}, en formation {student.course.label}"
        form.student.choices.append((str(student.id), displaytext))
    if form.validate_on_submit():
        success, message = DbStudent.delete(
            studentid=form.student.data)
        flash(message)
        if success:
            return redirect("/students")
    return render_template("student_delete.html", form=form)


@app.route("/spreadsheets")
def spreadsheets():
    # TODO améliorer apparence de col check
    # TODO améliorer apparence si None data
    form = SpreadsheetSelect()
    spreadsheets_list = DbForm.queryspreadsheets(minenddate=form.enddate.data)
    if form.validate_on_submit():
        # save selection for next screen
        return redirect(url_for("sheets"))
    return render_template("spreadsheets.html", courses=spreadsheets_list, form=form)


@app.route("/sheets")
def sheets():
    form = SheetsSelect()
    sheets_list = DbForm.querysheets()
    if form.validate_on_submit():
        success, message = DbForm.update()
        flash(message)
        if success:
            return redirect(url_for("sheets"))
    return render_template("sheets.html")
