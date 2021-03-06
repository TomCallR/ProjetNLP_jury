from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email


class InitForm(FlaskForm):
    submit = SubmitField("Initialiser la base")


class CourseCreateForm(FlaskForm):
    label = StringField(
        label="Intitulé",
        validators=[DataRequired(message="Saisissez un intitulé")]
    )
    startdate = DateField(
        label="Date de début (Y-m-d)",
        # format='%d/%m/%Y', does not work
        validators=[DataRequired(message="Saisissez une date de début")]
    )
    enddate = DateField(
        label="Date de fin (Y-m-d)",
        # format='%d/%m/%Y', does not work
        validators=[DataRequired(message="Saisissez une date de fin")]
    )
    fileid = StringField(
        label="Id du fichier associé (réponses aux questionnaires)",
        validators=[DataRequired(message="Saisissez l'id' du fichier")]
    )
    submit = SubmitField("Ajouter")


class CourseDeleteForm(FlaskForm):
    course = SelectField(
        label="Formation",
        # coerce=int,
        validators=[DataRequired(message="Sélectionnez une formation")]
    )
    submit = SubmitField("Supprimer")


class StudentCreateForm(FlaskForm):
    lastname = StringField(
        label="Nom de famille",
        validators=[DataRequired(message="Saisissez un nom de famille")]
    )
    firstname = StringField(
        label="Prénom",
        validators=[DataRequired(message="Saisissez un prénom")]
    )
    email = StringField(
        label="Email",
        validators=[DataRequired(message="Saisissez un email"),
                    Email(message="Email incorrect")]
    )
    course = SelectField(
        label="Formation",
        validators=[DataRequired(message="Sélectionnez une formation")]
    )
    submit = SubmitField("Ajouter")


class StudentDeleteForm(FlaskForm):
    student = SelectField(
        label="Etudiant",
        # coerce=int,
        validators=[DataRequired(message="Sélectionnez un étudiant")]
    )
    submit = SubmitField("Supprimer")


class SpreadsheetSelect(FlaskForm):
    enddate = DateField(
        label="Fin de formation postérieure au",
        validators=[DataRequired(message="Saisissez une date")]
    )
    submit = SubmitField("Sélectionner")


class SheetsSelect(FlaskForm):
    daysnochange = IntegerField(
        label="Nombre de jours sans modification",
        validators=[DataRequired(message="Saisissez un nombre de jours")]
    )
    submit = SubmitField("Mettre à jour")


class DashboardForm(FlaskForm):
    courses = SelectMultipleField(
        label="Formations"
    )
    startdate = DateField(
        label="Date de début"
    )
    enddate = DateField(
        label="Date de fin"
    )
    students = SelectMultipleField(
        label="Etudiants"
    )
    submit = SubmitField("Analyser")
