from datetime import timedelta, date, MINYEAR

from flask import flash, render_template, url_for, redirect

from app import app, db
from app.database.dbutils import DbCourse, DbStudent, DbForm, DbParam
from app.database.models import Course, Student
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect, InitForm


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    form = InitForm()  # TODO make generate conditional on existence
    if form.validate_on_submit():
        try:
            db.create_all()
            message = f"Succès : La base a été générée"
        except Exception as ex:
            message = f"Erreur : Impossible de générer la base. Exception :\n{ex}"
        flash(message)
        return redirect(url_for("dashboard"))
    return render_template("index.html", form=form)


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


@app.route("/spreadsheets", methods=["GET", "POST"])
def spreadsheets():
    # TODO améliorer apparence de col check
    # TODO améliorer apparence si None data
    form = SpreadsheetSelect()
    if form.validate_on_submit():
        newmaxdelta = (date.today() - form.enddate.data)
        success, message = DbParam.setparam(name="MAX_DELTA_TO_ENDDATE",
                                            value=str(newmaxdelta.days))
        return redirect(url_for("sheets"))
    else:
        maxdelta = DbParam.getparam(name="MAX_DELTA_TO_ENDDATE")
        minenddate = date.today() - timedelta(days=int(maxdelta))
        form.enddate.data = minenddate
        spreadsheets_list = DbForm.queryspreadsheets(minenddate=form.enddate.data)
    return render_template("spreadsheets.html", courses=spreadsheets_list, form=form)


@app.route("/sheets", methods=["GET", "POST"])
def sheets():
    form = SheetsSelect()
    maxdelta = DbParam.getparam(name="MAX_DELTA_TO_ENDDATE")
    minenddate = date.today() - timedelta(days=int(maxdelta))
    if form.validate_on_submit():
        success, messages = DbForm.update(minenddate=minenddate,
                                          daysnochange=form.daysnochange.data)
        for message in messages:
            flash(message)
        success, message = DbParam.setparam(name="MAX_DAYS_SHEET_NOT_CHANGED",      #TODO s'assurer que success est bon
                                            value=str(form.daysnochange.data))
        return redirect(url_for("sheets"))
    else:
        dbdaysnochange = DbParam.getparam(name="MAX_DAYS_SHEET_NOT_CHANGED")
        daysnochange = int(dbdaysnochange)
        form.daysnochange.data = daysnochange
        sheets_list = DbForm.querysheets(minenddate=minenddate,
                                         daysnochange=form.daysnochange.data)
    return render_template("sheets.html", gforms=sheets_list, form=form)
#TODO pb les onglets inconnus en base ne sont pas listés
