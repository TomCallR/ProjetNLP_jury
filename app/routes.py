from flask import flash, render_template, request, url_for, redirect

from app import app
from app.database.dbutils import DbCourse
from app.database.models import Course
from app.forms import CourseCreateForm, CourseDeleteForm


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/collect")
def collect():
    return render_template("collect.html")


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
    # form.courseid.choices = [(course.id, course.label + " [" + course.startdate + " - " +
    #                           course.enddate + "]") for course in courses_list]
    form.courseid.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {course.startdate} au " \
                      f"{str(course.startdate)}, fichier {course.spreadsheet}"
        form.courseid.choices.append((str(course.id), displaytext))
    if form.validate_on_submit():
        success, message = DbCourse.delete(
            courseid=form.courseid.data)
        flash(message)
        if success:
            return redirect("/courses")
    return render_template("course_delete.html", form=form)


@app.route("/students")
def students():
    return render_template("students.html")
