from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class ProjectForm(FlaskForm):
    name = StringField('Название проекта', validators=[DataRequired()])
    submit = SubmitField('Создать')
