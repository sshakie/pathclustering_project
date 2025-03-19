from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import *


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Остаться в системе')
    submit = SubmitField('Войти')
