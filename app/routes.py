import os
from datetime import datetime, timedelta

import matplotlib
import pandas as pd
from flask import flash, render_template, url_for, redirect, session
from plotnine import *

from app import app, db
from app.apputils import Const, Params, DTime
from app.database.dbutils import DbCourse, DbStudent, DbForm, Db, Dashboard
from app.database.models import Course, Student
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect, InitForm, DashboardForm

# https://stackoverflow.com/questions/27147300/matplotlib-tcl-asyncdelete-async-handler-deleted-by-the-wrong-thread
matplotlib.use("Agg")


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
    courses_list = db.session.query(Course).order_by(Course.startdate).all()
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
    courses_list = db.session.query(Course).order_by(Course.startdate).all()
    form = CourseDeleteForm()
    form.course.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {DTime.formatdate(course.startdate)} au " \
                      f"{DTime.formatdate(course.enddate)}, fichier {course.filename}"
        form.course.choices.append((str(course.id), displaytext))
    if form.validate_on_submit():
        success, message = DbCourse.delete(courseid=form.course.data)
        flash(message)
        if success:
            return redirect("/courses")
    return render_template("course_delete.html", form=form)


@app.route("/students", methods=["GET"])
def students():
    students_list = db.session.query(Student).order_by(
        Student.course_id, Student.lastname, Student.firstname
    ).all()
    return render_template("students.html", students=students_list)


@app.route("/student/create", methods=["GET", "POST"])
def student_create():
    courses_list = db.session.query(Course).all()
    form = StudentCreateForm()
    form.course.choices = []
    for course in courses_list:
        displaytext = f"{course.label} du {DTime.formatdate(course.startdate)} au " \
                      f"{DTime.formatdate(course.enddate)}, fichier {course.filename}"
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
        Student.course_id, Student.lastname, Student.firstname
    )
    form = StudentDeleteForm()
    form.student.choices = []
    for student in students_list:
        displaytext = f"Etudiant(e) {student.firstname} {student.lastname} (email {student.email}, " \
                      f"formation {student.course.label})"
        form.student.choices.append((str(student.id), displaytext))
    if form.validate_on_submit():
        success, message = DbStudent.delete(studentid=form.student.data)
        flash(message)
        if success:
            return redirect("/students")
    return render_template("student_delete.html", form=form)


@app.route("/spreadsheets", methods=["GET", "POST"])
def spreadsheets():
    # TODO améliorer apparence de col check
    form = SpreadsheetSelect()
    if form.validate_on_submit():
        if form.enddate.data is None:
            flash("Erreur : Aucune date choisie, utilisation d'une valeur par défaut")
        else:
            delta = (datetime.now().date() - form.enddate.data)
            newmaxdays = DTime.timedelta2days(delta)
            session[Const.MAX_DAYS_TO_ENDDATE] = newmaxdays
        return redirect(url_for("sheets"))
    else:
        maxdays = Params.getsessionvar(name=Const.MAX_DAYS_TO_ENDDATE,
                                       default=Const.DEFAULT_DAYS_TO_ENDDATE)
        minenddate = datetime.now() - timedelta(days=int(maxdays))
        form.enddate.data = minenddate
        okcourses = DbCourse.querycourses(minenddate=form.enddate.data)
    return render_template("spreadsheets.html", courses=okcourses, form=form)


@app.route("/sheets", methods=["GET", "POST"])
def sheets():
    # TODO améliorer apparence de col check
    form = SheetsSelect()
    maxdays = Params.getsessionvar(name=Const.MAX_DAYS_TO_ENDDATE,
                                   default=Const.DEFAULT_DAYS_TO_ENDDATE)
    minenddate = datetime.now() - timedelta(days=int(maxdays))
    if form.validate_on_submit():
        # Saving number of days for friendiness, failure unimportant
        if form.daysnochange.data is None:
            daysnochange = Params.getsessionvar(name=Const.MAX_DAYS_SHEET_UNCHANGED,
                                                default=Const.DEFAULT_DAYS_UNCHANGED)
            flash("Erreur : Aucune durée choisie, utilisation d'une valeur par défaut")
        else:
            session[Const.MAX_DAYS_SHEET_UNCHANGED] = form.daysnochange.data
            daysnochange = int(form.daysnochange.data)
        success = DbForm.updateall(minenddate=minenddate, daysnochange=daysnochange)
        if not success:
            flash("Attention : Des erreurs dans la mise à jour, certaines réponses non mises à jour")
        return redirect(url_for("sheets"))
    else:
        daysnochange = Params.getsessionvar(name=Const.MAX_DAYS_SHEET_UNCHANGED,
                                            default=Const.DEFAULT_DAYS_UNCHANGED)
        form.daysnochange.data = daysnochange
        oksheets = DbForm.queryforms(minenddate=minenddate, daysnochange=form.daysnochange.data)
    return render_template("sheets.html", gforms=oksheets, form=form)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    # TODO check dates coherent
    form = DashboardForm()
    form.courses.choices = []
    form.students.choices = []
    for course in db.session.query(Course).all():
        displaytext = f"{course.label} du {DTime.formatdate(course.startdate)} au " \
                      f"{DTime.formatdate(course.enddate)}, fichier {course.filename}"
        form.courses.choices.append((str(course.id), displaytext))
    for student in db.session.query(Student).all():
        displaytext = f"{student.firstname} {student.lastname} (email {student.email}, " \
                      f"formation {student.course.label})"
        form.students.choices.append((str(student.id), displaytext))
    if form.validate_on_submit():
        session["DASHBOARD_COURSE_IDS"] = [int(x) for x in form.courses.data]
        session["DASHBOARD_STUDENT_IDS"] = [int(x) for x in form.students.data]
        session["DASHBOARD_STARTDATE"] = DTime.datetimeencode(form.startdate.data)
        session["DASHBOARD_ENDDATE"] = DTime.datetimeencode(form.enddate.data)
        return redirect(url_for("dashboard_analyze"))
    else:
        form.startdate.data = DTime.min()
        form.enddate.data = DTime.max()
    return render_template("dashboard.html", form=form)


@app.route("/dashboard/analyze")
def dashboard_analyze():
    dashbrd = Dashboard.querycriteria()
    # display choices in a readonly form as a reminder
    form = DashboardForm()
    form.courses.render_kw = {"readonly": True}
    form.students.render_kw = {"readonly": True}
    form.startdate.render_kw = {"readonly": True}
    form.enddate.render_kw = {"readonly": True}
    form.courses.choices = []
    form.students.choices = []
    for course in dashbrd.courses_list:
        displaytext = f"{course.label} du {DTime.formatdate(course.startdate)} au " \
                      f"{DTime.formatdate(course.enddate)}, fichier {course.filename}"
        form.courses.choices.append((str(course.id), displaytext))
    for student in dashbrd.students_list:
        displaytext = f"{student.firstname} {student.lastname} (email {student.email}, " \
                      f"formation {student.course.label})"
        form.students.choices.append((str(student.id), displaytext))
    form.startdate.data = dashbrd.startdate.date()
    form.enddate.data = dashbrd.enddate.date()
    # prepare num graphs
    numgraphpaths = list()
    numanswers = dashbrd.querynumanswers()
    curtime = datetime.now(tz=None)
    suffix = f"{curtime.hour}{curtime.minute}{curtime.second}"
    for qindex, numanswer in enumerate(numanswers):
        data = pd.DataFrame({"x": numanswer.grades})
        title = Dashboard.wraptext(text=numanswer.questiontext, maxlen=50)
        gradegraph = (ggplot(data) +
                      coord_cartesian(xlim=(0, numanswer.max + 1)) +
                      geom_bar(aes(x="x")) +
                      labs(x="note", y="fréquence", title=title))
        graphname = f"graph_n{qindex}_{suffix}.jpg"
        gradegraph.save(filename=graphname, path=app.static_folder, width=5, height=5)
        numgraphpaths.append(graphname)
    # preapre text graphs
    textgraphpaths = list()
    textanswers = dashbrd.querytextanswers()
    for qindex, textanswers in enumerate(textanswers):
        data = pd.DataFrame({"x": textanswers.polarities, "y": textanswers.subjectivities})
        title = Dashboard.wraptext(text=textanswers.questiontext, maxlen=50)
        textgraph = (ggplot(data) +
                     coord_cartesian(xlim=(-1, 1), ylim=(0, 1)) +
                     geom_point(aes(x="x", y="y")) +
                     labs(x="polarité", y="subjectivité", title=title))
        graphname = f"graph_t{qindex}_{suffix}.jpg"
        textgraph.save(filename=graphname, path=app.static_folder, width=5, height=5)
        textgraphpaths.append(graphname)
    # delete old graphs : cf https://stackabuse.com/python-list-files-in-a-directory/
    with os.scandir(app.static_folder) as entries:
        for entry in entries:
            if entry.is_file():
                if entry.name.startswith("graph_") and not entry.name.endswith(f"_{suffix}.jpg"):
                    os.remove(os.path.join(app.static_folder, entry.name))
    return render_template("dashboard_analyze.html",
                           form=form,
                           numgraphpaths=numgraphpaths,
                           textgraphpaths=textgraphpaths)
