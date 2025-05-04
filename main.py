from flask_login import LoginManager, logout_user, current_user, login_user
from data.api.projects_api import ProjectsResource, ProjectsListResource
from flask import Flask, render_template, redirect, request, url_for
from data.api.orders_api import OrdersResource, OrdersListResource
from data.api.users_api import UsersResource, UsersListResource
from data.blanks.orderform import OrderForm, OrderImportForm
from data.sql.db_session import create_session, global_init
from data.blanks.registerform import RegisterForm
from data.xls.serialize import unpack_orders_xls
from data.sql.models.project import Project
from data.blanks.loginform import LoginForm
from data.sql.models.order import Order
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


@app.route('/projects', methods=['GET', 'POST'])
def show_projects():
    if current_user.is_authenticated:
        session = create_session()
        projects = [{'id': i.id, 'name': i.name, 'icon': i.icon, 'admin_id': i.admin_id} for i in
                    session.query(Project).filter(Project.admin_id == current_user.id).all()]
        return render_template('projects.html', projects=projects)
    return redirect('/login')


@app.route('/')
def homepage():
    if current_user.is_authenticated:
        return redirect('/projects')
    return redirect('/login')


@app.route('/projects/<int:project_id>', methods=['GET', 'POST'])
def show_project(project_id):
    if current_user.is_authenticated:
        session = create_session()
        if session.get(Project, project_id).admin_id != current_user.id:
            return redirect('/projects')

        project = session.get(Project, project_id)
        courier_orders = {}
        courier_data = {}

        if not (project.orders is None):
            for order_id in list(map(int, project.orders.split(','))):
                order = session.get(Order, order_id)
                order_dict = order.to_dict(only=('id', 'address', 'price', 'analytics_id'))
                order_dict['coords'] = order.get_coords()
                deliver = order.who_delivers if order.who_delivers is not None else 'no_courier'
                courier_orders[deliver] = courier_orders.get(deliver, []) + [order_dict]

        if not (project.couriers is None):
            for courier_id in list(map(int, project.couriers.split(','))):
                courier = session.get(User, courier_id)
                courier_data[courier_id] = courier.to_dict(only=('id', 'name'))
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
