from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired

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
    spreadsheet = StringField(
        label="Nom du fichier associé (réponses aux formulaires)",
        validators=[DataRequired(message="Saisissez le nom du fichier")]
    )
    submit = SubmitField("Ajouter")


class CourseDeleteForm(FlaskForm):

    courseid = SelectField(
        label="Formation",
        # coerce=int,
        validators=[DataRequired(message="Choisissez une formation")]
    )
    submit = SubmitField("Supprimer")
