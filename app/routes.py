import datetime

from flask import flash, render_template, request, url_for, redirect

from app import app
from app.database.dbutils import DbCourse, DbStudent, DbForm
from app.database.models import Course, Student, Form
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, GformsUpdate


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


@app.route("/gforms")
def gforms():
    today = datetime.date.today()
    anteriorday = today - datetime.timedelta(days=35.0)
    gforms_list = Form.query.filter(Form.course.has(Course.enddate >= anteriorday))
    gforms_list = gforms_list.filter(Form.course.has(Course.startdate <= today))
    gforms_list = gforms_list.filter(Form.course.has(Course.spreadsheet.__ne__(None)))
    gforms_list = gforms_list.order_by(Form.course_id, Form.lastentrydate).all()
    form = GformsUpdate()

    if form.validate_on_submit():
        success, message = DbForm.update(
            startdate=form.startdate.data)
        flash(message)
        if success:
            return redirect("/students")
    return render_template("gforms.html", gforms=gforms_list, form=form)

## POUR CONTINUER : relire, pour les formations avec les 3 critères ci-dessus :
## les onglets nouveaux, les onglets pourlesquels lastendtrydate >= lastreaddate - 35 jours
## + lire aussi pour les formations dont un jour au moins est postérieur ou égal à la date saisie


# @app.route("/gforms/old")
# def gforms_old():
#     return render_template("gforms_old.html")
