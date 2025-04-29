from wtforms import StringField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class OrderForm(FlaskForm):
    name = StringField('Имя получателя', validators=[DataRequired()])
    phone = StringField('Номер телефона', validators=[DataRequired()])
    address = StringField('Адрес отправления', validators=[DataRequired()])
    analytics_id = StringField('Айди заказа (если есть)')
    price = IntegerField('Стоимость')
    is_delivered = BooleanField('Доставлено')
    submit = SubmitField('Создать')
