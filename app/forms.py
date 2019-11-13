from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email

from app.database.models import Course


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
    spreadsheet = StringField(                                                    # TODO allow null first
        label="Nom du fichier associé (réponses aux formulaires)",
        validators=[DataRequired(message="Saisissez le nom du fichier")]
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
    mail = StringField(
        label="Adresse mail",
        validators=[DataRequired(message="Saisissez une adresse mail"),
                    Email(message="Adresse mail incorrecte")]
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
