from wtforms import StringField, IntegerField, BooleanField, SubmitField, TelField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class OrderForm(FlaskForm):
    name = StringField('Имя получателя', validators=[DataRequired()])
    phone = TelField('Номер телефона', validators=[DataRequired()]) # TODO: Подумать над валидацией номера телефонв
    address = StringField('Адрес отправления', validators=[DataRequired()])
    analytics_id = StringField('Айди заказа (если есть)')
    price = IntegerField('Стоимость')
    is_delivered = BooleanField('Доставлено')
    submit = SubmitField('Создать')
