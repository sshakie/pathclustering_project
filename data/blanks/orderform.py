from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import SubmitField



class OrderImportForm(FlaskForm):
    xls_file = FileField('data', validators=[FileAllowed(['xls', 'xlsx'], 'Только Excel файлы')])
    submit = SubmitField('Импорт')
