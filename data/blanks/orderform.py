from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import re


def is_right_phone_number(form, field):
    if isinstance(field, str):
        s = field
    else:
        s = field.data
    remainder = ''
    if s.startswith('+7'):
        remainder = s[2:]
    elif s.startswith('8'):
        remainder = s[1:]
    else:
        raise ValidationError('Телефон должен начинаться с +7 или 8')

    remainder = re.sub(r'[ -]', '', remainder)
    if re.match(r'^\(\d{3}\)', remainder):
        remainder = re.sub(r'\(', '', remainder, 1)
        remainder = re.sub(r'\)', '', remainder, 1)
    if not re.match(r'^\d{10}$', remainder):
        raise ValidationError('Неверный формат телефона')


class OrderForm(FlaskForm):
    name = StringField('имя получателя', validators=[DataRequired()])
    phone = StringField('номер телефона', validators=[DataRequired(), is_right_phone_number])
    address = StringField('адрес отправления', validators=[DataRequired()])
    analytics_id = StringField('айди заказа (если есть)')
    price = IntegerField('стоимость')
    submit = SubmitField('Создать')


class OrderImportForm(FlaskForm):
    xls_file = FileField('data', validators=[FileAllowed(['xls', 'xlsx'], 'Только Excel файлы')])
    submit = SubmitField('Импорт')
