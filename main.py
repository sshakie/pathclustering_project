from data.py.serialize import unpack_orders_xls, create_couriers_excel, create_orders_excel
from flask_login import LoginManager, logout_user, current_user, login_user
from data.api.courier_relations_api import CourierRelationsListResource
from data.api.projects_api import ProjectsResource, ProjectsListResource
from flask import Flask, render_template, redirect, request, jsonify
from data.api.orders_api import OrdersResource, OrdersListResource
from data.api.users_api import UsersResource, UsersListResource
from data.sql.models.courier_relations import CourierRelations
from data.sql.db_session import create_session, global_init
from data.sql.models.user_relations import UserRelations
from data.blanks.orderform import OrderImportForm
from data.blanks.registerform import RegisterForm
from data.sql.models.project import Project
from data.blanks.loginform import LoginForm
from data.py.clustering import clustering
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
api.add_resource(OrdersResource, '/api/orders/<int:order_id>')
api.add_resource(ProjectsListResource, '/api/projects')
api.add_resource(ProjectsResource, '/api/projects/<project_id>')
api.add_resource(CourierRelationsListResource, '/api/courier_relations')

session = create_session()
if not session.query(User).filter(User.name == 'admin').first(): # создаем админа, если sql только создался
    user = User()
    user.name = 'admin'
    user.email = 'admin@admin.py'
    user.set_password('admin')
    user.status = 'admin'
    session.add(user)
    session.commit()
session.close()


@lm.user_loader # загрузка данных о пользователе
def load_user(user_id):
    session = create_session()
    try:
        return session.get(User, user_id)
    finally:
        session.close()


@app.route('/projects', methods=['GET', 'POST'])
def show_projects():
    """Роут для показа проектов"""
    if current_user.is_authenticated:
        projects = requests.get(f'{request.host_url}api/projects', cookies=request.cookies).json()['projects']
        return render_template('projects.html', projects=projects)
    return redirect('/login')


@app.route('/')
def homepage(): # перебрасываем с этой ссылки, так как не используется
    if current_user.is_authenticated:
        return redirect('/projects')
    return redirect('/login')


@app.route('/projects/<int:project_id>', methods=['GET', 'POST', 'PUT'])
def show_project(project_id):
    """Главная страница, где происходит работа логиста с заказами"""
    if current_user.is_authenticated:
        session = create_session()
        project = session.get(Project, project_id)
        if current_user.status == 'admin':
            if not project or session.get(Project, project_id).admin_id != current_user.id:
                return redirect('/projects')
        else:
            checking = session.query(CourierRelations).filter(CourierRelations.project_id == project_id).all()
            if not project or not [i for i in checking if i.courier_id == current_user.id]:
                return redirect('/projects')

        ###### Собираем всё нужное сначала для курьера, чтобы отобразить ему страницу ######
        courier_orders = {}  # Данные о заказах в формате ключ - id курьера, значение - список заказов

        # заполнение courier_orders
        for order in session.query(Order).filter(Order.project_id == project.id).all():
            order_dict = order.to_dict(only=('id', 'address', 'price', 'analytics_id', 'name', 'phone', 'comment'))
            order_dict['coords'] = order.get_coords()
            deliver = order.who_delivers if order.who_delivers != -1 else 'no_courier'
            courier_orders[str(deliver)] = courier_orders.get(str(deliver), []) + [order_dict]

        if current_user.status != 'admin':
            return render_template('courier_homepage.html',
                                   courier_orders=courier_orders[str(current_user.id)] if str(current_user.id) in courier_orders else [],
                                   icon_id=project.icon,
                                   project_depot=[project.longitude, project.latitude])


        ###### Дальше собираем данные, которые нужны уже логисту ######
        courier_data = {}  # данные о курьерах в формате ключ - id курьера, значение - словарь с полями из бд

        # заполнение courier_data
        for courier in project.couriers:
            courier_data[str(courier.id)] = courier.to_dict(only=('id', 'name', 'telegram_tag', 'color'))

        couriers_d = []
        for i in session.query(UserRelations).filter(UserRelations.admin_id == current_user.id).all():
            b = session.get(User, i.courier_id).to_dict(only=('id', 'name', 'telegram_tag', 'color'))
            b['project_id'] = [i.project_id for i in
                               session.query(CourierRelations).filter(CourierRelations.courier_id == b['id']).all()]
            couriers_d.append(b)

        import_order_form = OrderImportForm()
        if request.method == 'POST':
            content_type = request.headers.get('Content-Type', '')
            if 'xls_file' in request.files:
                file = request.files['xls_file']
                if file.filename != '':
                    try:
                        success = unpack_orders_xls(file, project_id, request.cookies)
                        if not success:
                            response = jsonify({
                                'status': 'error',
                                'message': 'Ошибка при обработке файла. Проверьте формат данных.'
                            })
                            response.status_code = 400
                            return response

                        # Успешный ответ без содержимого
                        return '', 204
                    except Exception as e:
                        response = jsonify({
                            'status': 'error',
                            'message': f'Ошибка импорта: {str(e)}'
                        })
                        response.status_code = 500
                        return response

            elif 'application/json' in content_type:
                # Обработка запроса на кластеризацию
                data = request.get_json()
                if data and data.get('start_clustering'):
                    try:
                        project = session.get(Project, project_id)
                        clusters = clustering(
                            orders_list=list(session.query(Order).filter(
                                Order.project_id == project.id).all()),
                            num_couriers=len([i for i in couriers_d if project_id in i['project_id']]),
                            depot_coords=project.get_depot_coords())
                    except ValueError:
                        return jsonify({'status': 'error',
                                        'message': 'Ошибка. Возможно, нет свободных заказов или курьеров'}), 400
                    try:
                        ready_couriers = [i for i in couriers_d if project_id in i['project_id']]
                        for cluster in clusters.keys():
                            for order_id in clusters[cluster]:
                                requests.put(f'{request.host_url}api/orders/{order_id}',
                                             json={'who_delivers': ready_couriers[int(cluster) - 1]['id']},
                                             cookies=request.cookies)

                        return jsonify({'status': 'clustering successfully'}), 200
                    except IndexError:
                        return jsonify({'status': 'error',
                                        'message': 'Ошибка. Возможно, нет курьеров'}), 400


                elif data.get('action', '') == 'export':
                    # обработка запроса на экспорт
                    if data['type'] == 'couriers':
                        one_file = True if data['data']['format'] == 'single' else False

                        couriers = data['data']['selectedCouriers'] if data['data']['selectedCouriers'] \
                            else data['data']['allCouriers']

                        return create_couriers_excel(project_id, couriers, one_file)
                    elif data['type'] == 'orders':
                        return create_orders_excel(project_id)
        # Если метод не POST рендерим страницу
        return render_template('homepage.html',
                               import_form=import_order_form,
                               courier_data=courier_data,
                               courier_orders=courier_orders,
                               icon_id=project.icon,
                               invite_link=project.invite_link,
                               courier_ready=[i for i in couriers_d if project_id in i['project_id']],
                               courier_not_ready=[i for i in couriers_d if project_id not in i['project_id']],
                               project_depot=[project.longitude, project.latitude])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Роут для обработки формы логина"""
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


@app.route('/register/<invite_link>', methods=['GET', 'POST'])
def invite_register(invite_link):
    """Роут - приглашение курьеров по ссылке логиста"""
    if current_user.is_authenticated:
        return redirect('/')

    session = create_session()
    project = session.query(Project).filter(Project.invite_link == invite_link).first()
    if not project:
        return render_template('error_page.html', error_code=404)
    admin = session.get(User, project.admin_id)
    form = RegisterForm()
    if form.validate_on_submit():
        if session.query(User).filter(User.email == form.email.data).first():
            session.close()
            return render_template('register.html', message='Данная почта уже зарегистрирована, попробуйте войти.',
                                   form=form, admin_name=admin.name)
        user_id = requests.post(f'{request.host_url}api/users', json={'name': form.name.data,
                                                                         'email': form.email.data,
                                                                         'telegram_tag': form.telegram_tag.data,
                                                                         'password': form.password.data,
                                                                         'project_id': project.id}).json()
        login_user(session.get(User, user_id['user_id']), remember=form.remember_me.data)
        session.close()
        return redirect('/')
    session.close()
    return render_template('register.html', title='Присоединение к проекту', form=form, admin_name=admin.name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователей"""
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        session = create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            session.close()
            return render_template(
                'register.html',
                message='Данная почта уже зарегистрирована, попробуйте войти.',
                form=form)

        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.telegram_tag = form.telegram_tag.data
        user.set_password(form.password.data)
        user.status = 'admin'
        session.add(user)
        session.commit()
        login_user(user, remember=form.remember_me.data)
        session.close()
        return redirect('/')
    return render_template('register.html', title='Стать логистом', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.route('/test')
def test():
    # ТЕСТ ПРОЕКТ - КУРЬЕРЫ
    print(requests.post(f'{request.host_url}api/projects',
                        json={'name': 'test', 'admin_id': 1}, cookies=request.cookies).json())
    print(requests.post(f'{request.host_url}api/users',
                        json={'name': 'Samantha Wood', 'email': 'samantha_wood1@mail.ru', 'password': '123',
                              'telegram_tag': '@dropmeapart03', 'project_id': 1}).json())
    print(requests.post(f'{request.host_url}api/users',
                        json={'name': 'Roger Di', 'email': 'roger_di1@mail.ru', 'admin_id': 1,
                              'password': '123'}).json())
    print(requests.post(f'{request.host_url}api/users',
                        json={'name': 'Dave Carlson', 'email': 'dave_carlson1@mail.ru', 'password': '123',
                              'telegram_tag': '@captain1928', 'project_id': 1}).json())
    print(requests.post(f'{request.host_url}api/orders',
                        json={'name': 'Jone', 'phone': '+79009897520', 'address': 'Lipetsk, ul. Moskovskaya, 92',
                              'project_id': 1, 'price': 1512, 'comment': 'бобер мне снес квартиру', 'who_delivers': 2}, cookies=request.cookies).json())
    session = create_session()
    session.query(User).filter(User.id == 2).first().color = '#7F7F7F'
    session.query(User).filter(User.id == 3).first().color = '#AA00FF'
    session.query(User).filter(User.id == 4).first().color = '#FF6A00'
    session.commit()
    session.close()
    return redirect('/projects')


if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(threaded=True)
