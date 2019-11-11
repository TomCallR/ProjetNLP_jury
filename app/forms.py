from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, ValidationError

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

    # @staticmethod
    # def validate_label(self, label):
    #     course = Course.query.filter_by(label=label.data).first()
    #     if course is not None:
    #         raise ValidationError('Erreur : Une formation avec le même intitulé existe déjà')
    #
    # def validate_enddate(self, enddate):
    #     if self.startdate and not enddate.data > self.startdate.data:
    #         raise ValidationError('Erreur : La date de début est postérieure à la date de fin')
    #
    # @staticmethod
    # def validate_spreadsheet(self, spreadsheet):
    #     sheet = Course.query.filter_by(spreadsheet=spreadsheet.data).first()
    #     if sheet is not None:
    #         raise ValidationError("Erreur : Une formation avec le même fichier associé existe déjà")


class CourseDeleteForm(FlaskForm):

    courseid = SelectField(
        label="Formation",
        coerce=int
    )
    submit = SubmitField("Supprimer")