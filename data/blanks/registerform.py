from wtforms import StringField, EmailField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class RegisterForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=20)])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    telegram_tag = StringField('Телеграм тег')
    remember_me = BooleanField('Остаться в системе')
    submit = SubmitField('Создать')
