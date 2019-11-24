from datetime import datetime, timedelta, date, MINYEAR

from flask import flash, render_template, url_for, redirect

from app import app, db
from app.database.dbutils import DbCourse, DbStudent, DbForm, DbParam, Db
from app.database.models import Course, Student
from app.forms import CourseCreateForm, CourseDeleteForm, StudentCreateForm, StudentDeleteForm, SpreadsheetSelect, \
    SheetsSelect, InitForm


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
            fileid=form.fileid.data
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
                      f"{str(course.startdate)}, fichier {course.now()}"
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
        success = DbParam.setparam(name="MAX_DELTA_TO_ENDDATE",
                                   value=str(newmaxdelta.days))
        if not success:
            flash(f"Erreur : La date de fin de formation choisie n'a pas été sauvegardée")
        return redirect(url_for("sheets"))
    else:
        success, maxdelta = DbParam.getparam(name="MAX_DELTA_TO_ENDDATE")
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
    success, maxdelta = DbParam.getparam(name="MAX_DELTA_TO_ENDDATE")
    if success:
        minenddate = datetime.now() - timedelta(days=int(maxdelta))
        if form.validate_on_submit():
            # Saving number of days for friendiness, failure unimportant
            DbParam.setparam(name="MAX_DAYS_SHEET_NOT_CHANGED",
                             value=str(form.daysnochange.data))
            success = DbForm.updateall(minenddate=minenddate,
                                       daysnochange=form.daysnochange.data)
            if not success:
                flash("Attention : Des erreurs dans la mise à jour, certaines réponses n'ont pas été mises à jour")
            return redirect(url_for("sheets"))
        else:
            success, dbdaysnochange = DbParam.getparam(name="MAX_DAYS_SHEET_NOT_CHANGED")
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
#TODO pb les onglets inconnus en base ne sont pas listés
