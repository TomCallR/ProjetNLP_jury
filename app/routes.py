import json
import os
from datetime import datetime, timedelta, time

import pandas as pd
from flask import flash, render_template, url_for, redirect, session
from plotnine import *

from app import app, db, params
from app.database.dbutils import DbCourse, DbStudent, DbForm, DbParam, Db, ParamName, Dashboard
from app.database.models import Course, Student
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect, InitForm, DashboardForm
from app.params import DateEncoder


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
    # TODO check dates coherent
    form = DashboardForm()
    form.courses.choices = []
    form.students.choices = []
    for course in db.session.query(Course).all():
        displaytext = f"{course.label} du {course.startdate.date()} au " \
                      f"{course.enddate.date()}, fichier {course.filename}"
        form.courses.choices.append((str(course.id), displaytext))
    for student in db.session.query(Student).all():
        displaytext = f"{student.firstname} {student.lastname} (email {student.email}, " \
                      f"formation {student.course.label})"
        form.students.choices.append((str(student.id), displaytext))
    if form.validate_on_submit():
        session["DASHBOARD_COURSE_IDS"] = [int(x) for x in form.courses.data]
        session["DASHBOARD_STUDENT_IDS"] = [int(x) for x in form.students.data]
        session["DASHBOARD_STARTDATE"] = form.startdate.data
        session["DASHBOARD_STARTDATE"] = json.dumps(form.startdate.data, cls=DateEncoder)
        session["DASHBOARD_ENDDATE"] = json.dumps(form.enddate.data, cls=DateEncoder)
        # datetime not json serializable
        # sdate = form.startdate.data
        # session["DASHBOARD_STARTDATE"] = (sdate.year, sdate.month, sdate.day)
        # edate = form.enddate.data
        # session["DASHBOARD_ENDDATE"] = (edate.year, edate.month, edate.day)
        return redirect(url_for("dashboard_analyze"))
    else:
        form.startdate.data = params.getmindate()
        form.enddate.data = params.getmaxdate()
    return render_template("dashboard.html", form=form)


@app.route("/dashboard/analyze")
def dashboard_analyze():
    graphpaths = list()
    dashbrd = Dashboard.querycriteria()
    answerstats = dashbrd.queryanswers()
    curtime = datetime.now(tz=None)
    suffix = f"{curtime.hour}{curtime.minute}{curtime.second}"
    for qindex, answerstat in enumerate(answerstats):
        data = pd.DataFrame({"x": answerstat.grades})
        title = Dashboard.wraptext(text=answerstat.questiontext, maxlen=50)
        gradegraph = (ggplot(data) +
                      coord_cartesian(xlim=(0, 6)) +
                      geom_bar(aes(x="x")) +
                      labs(x="note", y="fréquence", title=title))
        graphname = f"graph{qindex}_{suffix}.jpg"
        gradegraph.save(filename=graphname, path=app.static_folder, width=5, height=5)
        graphpaths.append(graphname)
    # delete old graphs : cf https://stackabuse.com/python-list-files-in-a-directory/
    with os.scandir(app.static_folder) as entries:
        for entry in entries:
            if entry.is_file() and entry.name[0:5] == "graph" and not entry.name.endswith(f"_{suffix}.jpg"):
                os.remove(os.path.join(app.static_folder, entry.name))
    return render_template("dashboard_analyze.html", dashboard=dashbrd, graphpaths=graphpaths)
