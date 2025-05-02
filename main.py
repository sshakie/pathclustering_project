from flask import Flask, render_template, redirect, request, flash, url_for
from flask_login import LoginManager, logout_user, current_user, login_user
from data.api.projects_api import ProjectsResource, ProjectsListResource
from data.api.orders_api import OrdersResource, OrdersListResource
from data.api.users_api import UsersResource, UsersListResource
from data.blanks.orderform import OrderForm, OrderImportForm
from data.sql.db_session import create_session, global_init
from data.blanks.registerform import RegisterForm
from data.xls.serialize import unpack_orders_xls
from data.blanks.loginform import LoginForm
from data.sql.models.user import User
from flask_restful import Api
import requests, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_promises'
global_init('data/sql/pathclustering.db')

lm = LoginManager()
lm.init_app(app)

api = Api(app)
api.add_resource(UsersListResource, '/api/users')
api.add_resource(UsersResource, '/api/users/<int:user_id>')
api.add_resource(OrdersListResource, '/api/orders')
api.add_resource(OrdersResource, '/api/orders/<order_id>')
api.add_resource(ProjectsListResource, '/api/projects')
api.add_resource(ProjectsResource, '/api/projects/<project_id>')

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
        return session.get(User, user_id)
    finally:
        session.close()


@app.route('/current_project', methods=['GET', 'POST'])
def homepage():
    if current_user.is_authenticated:
        courier_data = {'courier_1': {'name': 'Иван Иванов', 'phone': '+79991234567'},
                        'courier_2': {'name': 'Мария Смирнова', 'phone': '+79997654321'}}

        courier_orders = {
            'no_courier': [{'id': 4, 'address': "Адресс_тест", 'price': "1537 руб.", 'coords': [52.592398, 39.504709],
                            'analytics_id': "arf137 Заказ без курьера"}],
            'courier_1': [
                {'id': 1, 'address': "ул. Катукова, вл51", 'price': "1537 руб.", 'coords': [52.592348, 39.504789],
                 'analytics_id': "arf137"},
                {'id': 2, 'address': "пр. Сержанта Кувшинова, 5", 'price': "17 руб.", 'coords': [52.599012, 39.517621],
                 'analytics_id': "bhg036"}],
            'courier_2': [
                {'id': 3, 'address': "ул. Вершишева д.51", 'price': "191 руб.", 'coords': [52.605003, 39.535107],
                 'analytics_id': "abc012"}]}

        # project = requests.get('http://127.0.0.1:5000/api/projects/' + str(project_id), cookies=request.cookies).json()
        #
        # courier_orders = {}
        # courier_data = {}
        #
        # for order_id in project['orders']:
        #     order = requests.get('http://127.0.0.1:5000/api/orders/<order_id>' + str(order_id), cookies=request.cookies).json()
        #     order_dict = order.to_dict(only=('id', 'address', 'price', 'analytics_id'))
        #     order_dict['coords'] = order.get_coords()
        #     courier_orders[order['who_delivers']] = courier_orders.get(order['who_delivers'], []) + [order_dict]
        #
        # for courier_id in project['couriers']:
        #     courier = requests.get('http://127.0.0.1:5000/api/users/' + str(courier_id), cookies=request.cookies).json()
        #     courier_data[courier_id] = courier.to_dict(only=('id', 'name'))

        add_order_form = OrderForm()
        import_order_form = OrderImportForm()
        if request.method == 'POST':
            form_name = request.form.get('form_name')
            if form_name == 'add_order':
                if add_order_form.validate_on_submit():
                    data = {'phone': add_order_form.phone.data,
                            'name': add_order_form.name.data,
                            'address': add_order_form.address.data,
                            'analytics_id': add_order_form.analytics_id.data,
                            'price': add_order_form.price.data}
                    requests.post('http://127.0.0.1:5000/api/orders', json=data, cookies=request.cookies)
                    return redirect(url_for('homepage'))
                else:
                    return render_template('homepage.html',
                                           add_order_form=add_order_form,
                                           import_order_form=import_order_form,
                                           courier_data=courier_data,
                                           courier_orders=courier_orders)
            elif form_name == 'import_orders' and import_order_form.validate_on_submit():
                xls = import_order_form.xls_file.data
                unpack_orders_xls(xls)
        else:
            return render_template('homepage.html',
                                   add_order_form=add_order_form,
                                   import_order_form=import_order_form,
                                   courier_data=courier_data,
                                   courier_orders=courier_orders)
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
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)
