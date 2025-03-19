from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *


class OrderForm(FlaskForm):
    address = StringField('Адрес отправления', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    goods = SelectMultipleField('Доставляемые товары', validators=[DataRequired()])
    scheduled_date = StringField('Назначить дату и время доставки')
    # scheduled_date = DateTimeField('Назначить дату и время доставки')
    is_delivered = BooleanField('Доставлено')
    submit = SubmitField('Добавить')
