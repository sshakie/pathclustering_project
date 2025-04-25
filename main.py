from flask_login import LoginManager, logout_user, current_user, login_user
from data.db_session import create_session, global_init
from flask import Flask, render_template, redirect
from blanks.registerform import RegisterForm
from blanks.loginform import LoginForm
from data.user import User

app = Flask(__name__)
lm = LoginManager()

app.config['SECRET_KEY'] = 'my_promises'

lm.init_app(app)
global_init('static/sql.db')

db_sess = create_session()
if not db_sess.query(User).filter(User.name == 'admin').first():
    # api создание
    pass
db_sess.close()


@lm.user_loader
def load_user(user_id):
    return create_session().query(User).get(user_id)


@app.route('/')
def homepage():
    if current_user.is_authenticated:
        return render_template('homepage.html')
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect('/orders')
        db_sess.close()
        return render_template('login.html', message='Неправильные данные', form=form)
    return render_template('login.html', title='Вход в аккаунт', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            return render_template('register.html', message='Данная почта уже зарегистрирована, попробуйте войти.',
                                   form=form)

        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=form.remember_me.data)
        db_sess.close()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run()
