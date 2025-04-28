from flask_login import LoginManager, logout_user, current_user, login_user
from pymupdf import message

from api.orders_api import OrdersResource, OrdersListResource
from api.users_api import UsersResource, UsersListResource
from blanks.orderform import OrderForm
from data.db_session import create_session, global_init
from flask import Flask, render_template, redirect, request
from blanks.registerform import RegisterForm
from blanks.loginform import LoginForm
from flask_restful import Api
from data.user import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_promises'
global_init('static/sql.db')

lm = LoginManager()
lm.init_app(app)

api = Api(app)
api.add_resource(UsersListResource, '/api/users')
api.add_resource(UsersResource, '/api/users/<int:user_id>')
api.add_resource(OrdersListResource, '/api/orders')
api.add_resource(OrdersResource, '/api/orders/<order_id>')

session = create_session()
if not session.query(User).filter(User.name == 'admin').first():
    user = User()
    user.name = 'admin'
    user.email = 'admin@admin.py'
    user.set_password('admin')
    user.status = 'admin'
    session.add(user)
    session.commit()
session.close()


@lm.user_loader
def load_user(user_id):
    session = create_session()
    try:
        return session.query(User).get(user_id)
    finally:
        session.close()



@app.route('/', methods=['GET', 'POST'])
def homepage():
    if current_user.is_authenticated:
        form = OrderForm()
        if request.method == 'GET':
            return render_template('homepage.html', add_order_form=form)
        if form.validate_on_submit():
            print(form.data)
            return render_template('homepage.html', add_order_form=form)
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        session = create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session.close()
            return redirect('/')
        session.close()
        return render_template('login.html', message='Неправильные данные', form=form)
    return render_template('login.html', title='Вход в аккаунт', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        session = create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            session.close()
            return render_template('register.html', message='Данная почта уже зарегистрирована, попробуйте войти.',
                                   form=form)

        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        login_user(user, remember=form.remember_me.data)
        session.close()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run()
