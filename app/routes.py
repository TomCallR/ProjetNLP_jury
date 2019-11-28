from datetime import datetime, timedelta, date, MINYEAR

import pandas as pd
from flask import flash, render_template, url_for, redirect
from plotnine import *

from app import app, db
from app.database.dbutils import DbCourse, DbStudent, DbForm, DbParam, Db, ParamName
from app.database.models import Course, Student
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect, InitForm, DashboardForm


@app.route("/")
@app.route("/index")
def index():
    success = Db.exists()
    if not success:
        return redirect(url_for("basesetup"))
    return render_template("index.html")


@app.route("/base_setup", methods=["GET", "POST"])
def basesetup():
    form = InitForm()
    if form.validate_on_submit():
        try:
            db.create_all()
            message = f"Succès : La base a été initialisée"
        except Exception as ex:
            message = f"Erreur : Impossible d'initialiser la base"
        flash(message)
        return redirect(url_for("index"))
    else:
        success = Db.exists()
        if success:
            return redirect(url_for("index"))
        return render_template("base_setup.html", form=form)


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
            fileid=form.fileid.data
        )
        flash(message)
        if success:
            return redirect(url_for("courses"))
    return render_template("course_create.html", form=form)


@app.route("/course/delete", methods=["GET", "POST"])
def course_delete():
    courses_list = db.session.query(Course).all()
    form = CourseDeleteForm()
    form.course.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {course.startdate.date()} au " \
                      f"{course.enddate.date()}, fichier {course.filename}"
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
                      f"{str(course.startdate)}, fichier {course.filename}"
        form.course.choices.append((str(course.id), displaytext))
    if form.validate_on_submit():
        success, message = DbStudent.insert(
            lastname=form.lastname.data,
            firstname=form.firstname.data,
            email=form.email.data,
            course_id=form.course.data
        )
        flash(message)
        if success:
            return redirect(url_for("students"))
    return render_template("student_create.html", form=form)


@app.route("/student/delete", methods=["GET", "POST"])
def student_delete():
    students_list = db.session.query(Student).order_by(
        Student.course_id, Student.email
    )
    form = StudentDeleteForm()
    form.student.choices = []
    for student in students_list:
        displaytext = f"Etudiant(e) {student.email}, en formation {student.course.label}"
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
    form = SpreadsheetSelect()
    if form.validate_on_submit():
        newmaxdelta = (datetime.now().date() - form.enddate.data)
        success = DbParam.setparam(name=ParamName.MAX_DELTA_TO_ENDDATE.value,
                                   value=str(newmaxdelta.days))
        if not success:
            flash(f"Erreur : La date de fin de formation choisie n'a pas été sauvegardée")
        return redirect(url_for("sheets"))
    else:
        success, maxdelta = DbParam.getparam(name=ParamName.MAX_DELTA_TO_ENDDATE.value)
        if not success:
            maxdelta = "35"
        minenddate = datetime.now() - timedelta(days=int(maxdelta))
        form.enddate.data = minenddate
        spreadsheets_list = DbForm.queryspreadsheets(minenddate=form.enddate.data)
    return render_template("spreadsheets.html", courses=spreadsheets_list, form=form)


@app.route("/sheets", methods=["GET", "POST"])
def sheets():
    # TODO améliorer apparence de col check
    form = SheetsSelect()
    success, maxdelta = DbParam.getparam(name=ParamName.MAX_DELTA_TO_ENDDATE.value)
    if success:
        minenddate = datetime.now() - timedelta(days=int(maxdelta))
        if form.validate_on_submit():
            # Saving number of days for friendiness, failure unimportant
            DbParam.setparam(name=ParamName.MAX_DAYS_SHEET_NOT_CHANGED.value,
                             value=str(form.daysnochange.data))
            success = DbForm.updateall(minenddate=minenddate,
                                       daysnochange=form.daysnochange.data)
            if not success:
                flash("Attention : Des erreurs dans la mise à jour, certaines réponses n'ont pas été mises à jour")
            return redirect(url_for("sheets"))
        else:
            success, dbdaysnochange = DbParam.getparam(name=ParamName.MAX_DAYS_SHEET_NOT_CHANGED.value)
            if not success:
                dbdaysnochange = "15"
            daysnochange = int(dbdaysnochange)
            form.daysnochange.data = daysnochange
            sheets_list = DbForm.querysheets(minenddate=minenddate,
                                             daysnochange=form.daysnochange.data)
    else:
        flash("Erreur : Echec de la prise en compte de la date de fin de formation")
        return redirect(url_for("spreadsheets"))
    return render_template("sheets.html", gforms=sheets_list, form=form)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    form = DashboardForm()
    if form.validate_on_submit():
        val = "" if form.courses.data is None else ",".join(form.courses.data)
        success = DbParam.setparam(name=ParamName.COURSES_FOR_DASHBOARD.value, value=val)
        if not success:
            flash("Erreur : Sélection de formations perdue")
        val = "" if form.students.data is None else ",".join(form.students.data)
        success = DbParam.setparam(name=ParamName.STUDENTS_FOR_DASHBOARD.value, value=val)
        if not success:
            flash("Erreur : Sélection d'étudiants perdue")
        val = "" if form.startdate.data is None else form.startdate.data
        success = DbParam.setparam(name=ParamName.STARTDATE_FOR_DASHBOARD.value, value=val)
        if not success:
            flash("Erreur : Sélection de date de départ perdue")
        val = "" if form.enddate.data is None else form.enddate.data
        success = DbParam.setparam(name=ParamName.ENDDATE_FOR_DASHBOARD.value, value=val)
        if not success:
            flash("Erreur : Sélection de date de départ perdue")
        return redirect(url_for("dashboard_analyze"))

    else:
        form.courses.choices = []
        form.students.choices = []
        for course in db.session.query(Course).all():
            displaytext = f"{course.label} du {course.startdate.date()} au " \
                          f"{course.enddate.date()}, fichier {course.filename}"
            form.courses.choices.append((str(course.id), displaytext))
        for student in db.session.query(Student).all():
            displaytext = f"{student.firstname} {student.lastname} (email {student.email}, " \
                          f"formation {student.course.label}"
            form.students.choices.append((str(student.id), displaytext))
        form.startdate.data = date(year=MINYEAR, month=1, day=1)
        form.enddate.data = date(year=2025, month=12, day=31)
    return render_template("dashboard.html", form=form)


@app.route("/dashboard/analyze")
def dashboard_analyze():
    data1 = pd.DataFrame({
        'poids': [10, 20, 30, 40, 50],
        'taille': [1, 2, 4, 8, 16]
    })
    graph1 = (ggplot(data1) + geom_bar(aes(x="taille")))
    graph1.save(filename="graph1.png", path="app/static", width=3, height=3)
    return render_template("dashboard_analyze.html", graph=graph1)
