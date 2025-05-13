from data.py.serialize import unpack_orders_xls, create_couriers_excel, create_orders_excel
from flask_login import LoginManager, logout_user, current_user, login_user
from data.api.projects_api import ProjectsResource, ProjectsListResource
from data.api.courier_relations_api import CourierRelationsListResource
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
lm = LoginManager()

with open('data/config', encoding='UTF-8') as file:  # API-ключ для карт
    api_key = file.read().split('\n')[0].split()[1]


def main():
    # Подготовка к работе
    app.config['SECRET_KEY'] = 'my_promises'
    global_init('data/sql/pathclustering.db')

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
    if not session.query(User).filter(User.name == 'admin').first():  # создаем админа, если sql только создался
        user = User(name='admin', email='admin@admin.py', status='admin')
        user.set_password('admin')
        session.add(user)
        session.commit()
    session.close()
    pass


@lm.user_loader  # загрузка данных пользователя
def load_user(user_id):
    session = create_session()
    try:
        return session.get(User, user_id)
    finally:
        session.close()


@app.route('/projects', methods=['GET', 'POST'])
def show_projects():
    """Роут для показа проектов"""
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        projects = requests.get(f'{request.host_url}api/projects', cookies=request.cookies).json()['projects']
        return render_template('projects.html', projects=projects)
    return redirect('/login')


@app.route('/')
def homepage():  # Переадресация на "главную страницу"
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        return redirect('/projects')
    return redirect('/login')


@app.route('/projects/<int:project_id>', methods=['GET', 'POST', 'PUT'])
def show_project(project_id):
    """Главная страница, где происходит работа логиста с заказами"""
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        session = create_session()
        try:
            # Проверка существует такой проект или нет и владелец/участник ли человек (для двух ролей)
            project = session.get(Project, project_id)
            if current_user.status == 'admin':
                if not project or session.get(Project, project_id).admin_id != current_user.id:
                    return redirect('/projects')
            else:
                checking = session.query(CourierRelations).filter(CourierRelations.project_id == project_id).all()
                if not project or not [i for i in checking if i.courier_id == current_user.id]:
                    return redirect('/projects')

            ####################################################################################
            ###### Собираем всё нужное сначала для курьера, чтобы отобразить ему страницу ######
            ####################################################################################

            courier_orders = {}  # Данные о заказах в формате ключ - id курьера, значение - список заказов
            for order in session.query(Order).filter(Order.project_id == project.id).all():
                order_dict = order.to_dict(only=('id', 'address', 'price', 'analytics_id', 'name', 'phone', 'comment'))
                order_dict['coords'] = order.get_coords()
                order_courier = order.who_delivers if order.who_delivers != -1 else 'no_courier'
                courier_orders[str(order_courier)] = courier_orders.get(str(order_courier), []) + [order_dict]

            if current_user.status != 'admin':
                return render_template('courier_homepage.html',
                                       courier_orders=courier_orders[str(current_user.id)] if str(
                                           current_user.id) in courier_orders else [],
                                       icon_id=project.icon,
                                       project_depot=[project.longitude, project.latitude],
                                       api_key=api_key,
                                       link=request.host_url)

            ###############################################################
            ###### Дальше собираем данные, которые нужны уже логисту ######
            ###############################################################

            courier_data = {}  # данные о курьерах в формате ключ - id курьера, значение - словарь с полями из бд
            for courier in project.couriers:
                courier_data[str(courier.id)] = courier.to_dict(only=('id', 'name', 'telegram_tag', 'color'))

            couriers_d = []  # тоже данные о курьерах для вкладки карты/**курьеры**
            for relation in session.query(UserRelations).filter(UserRelations.admin_id == current_user.id).all():
                courier_info = session.get(User, relation.courier_id).to_dict(
                    only=('id', 'name', 'telegram_tag', 'color'))
                courier_info['project_id'] = [relation2.project_id for relation2 in
                                              session.query(CourierRelations).filter(
                                                  CourierRelations.courier_id == courier_info['id']).all()]
                couriers_d.append(courier_info)

            ready_couriers = [courier for courier in couriers_d if project_id in courier['project_id']]

            import_order_form = OrderImportForm()
            if request.method == 'POST':  # Если был отправлен какие-либо данные в формах
                content_type = request.headers.get('Content-Type', '')  # Для обработки запроса

                if 'xls_file' in request.files:  # Обработка запроса на импорт
                    try:
                        is_success = unpack_orders_xls(request.files['xls_file'], project_id, request.cookies,
                                                       request.host_url)
                        if not is_success:  # Если таблица имела ошибки / не подходит образцу
                            return jsonify(
                                {'status': 'error',
                                 'message': 'Ошибка при обработке файла. Проверьте формат данных.'}), 400

                        # Иначе подтверждаем работу
                        return jsonify({'status': 'importing successfully'}), 204
                    except Exception as e:
                        return jsonify({'status': 'error', 'message': f'{str(e)}'}), 500

                elif 'application/json' in content_type:  # Если пришёл другой запрос
                    data = request.get_json()

                    if data and data.get('start_clustering'):  # Если запрос на кластеризацию
                        try:
                            clusters = clustering(
                                orders_list=list(session.query(Order).filter(Order.project_id == project.id).all()),
                                num_couriers=len(ready_couriers),
                                depot_coords=project.get_depot_coords())

                            # Отдаем полученные кластеры курьеров в заказы
                            for cluster in clusters.keys():
                                for order_id in clusters[cluster]:
                                    requests.put(f'{request.host_url}api/orders/{order_id}',
                                                 json={'who_delivers': ready_couriers[int(cluster) - 1]['id']},
                                                 cookies=request.cookies)
                        except ValueError:
                            return jsonify({'status': 'error',
                                            'message': 'Ошибка. Возможно, нет свободных заказов или курьеров'}), 400
                        except IndexError:
                            return jsonify({'status': 'error', 'message': 'Ошибка. Возможно, нет курьеров'}), 400

                    elif data.get('action', '') == 'export':  # Если запрос на экспорт
                        if data['type'] == 'couriers':  # Если запросили экспортировать курьера(ов)
                            # Проверка нужно ли разбить в отдельные файлы курьеров
                            one_file = True if data['data']['format'] == 'single' else False
                            # Получаем каких именно курьеров пользователь хотел экспортировать в файл(ы)
                            data_for_export = data['data']['selectedCouriers'] if data['data']['selectedCouriers'] \
                                else data['data']['allCouriers']
                            return create_couriers_excel(project_id, data_for_export, one_file)

                        elif data['type'] == 'orders':  # Если запросили экспортировать заказ(ы)
                            return create_orders_excel(project_id)

            # Если нет никаких POST-запросов, то выводим
            return render_template('homepage.html',
                                   import_form=import_order_form,
                                   courier_data=courier_data,
                                   courier_orders=courier_orders,
                                   icon_id=project.icon,
                                   invite_link=project.invite_link,
                                   courier_ready=ready_couriers,
                                   courier_not_ready=[i for i in couriers_d if project_id not in i['project_id']],
                                   project_depot=[project.longitude, project.latitude],
                                   api_key=api_key,
                                   link=request.host_url)
        finally:
            session.close()
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Роут для обработки формы логина"""
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        return redirect('/')

    session = create_session()
    try:
        form = LoginForm()
        if form.validate_on_submit():  # Если заполнили все поля, то авторизируем
            user = session.query(User).filter(User.email == form.email.data).first()
            if not user or not user.check_password(
                    form.password.data):  # Если неправильно написаны данные, то отправляем ошибку
                return render_template('login.html', message='Неправильные данные', form=form)

            # Иначе авторизируем
            login_user(user, remember=form.remember_me.data)
            return redirect('/')

        # Иначе отображаем просто страницу
        return render_template('login.html', title='Вход в аккаунт', form=form)
    finally:
        session.close()


@app.route('/register/<invite_link>', methods=['GET', 'POST'])
def invite_register(invite_link):
    """Роут - приглашение курьеров по ссылке логиста"""
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        return redirect('/')

    session = create_session()
    try:
        project = session.query(Project).filter(Project.invite_link == invite_link).first()
        if not project:  # Проверка действительности такого айди приглашения
            return render_template('error_page.html', error_code=404)
        admin = session.get(User, project.admin_id)  # Для вывода имени приглашающего

        form = RegisterForm()
        if form.validate_on_submit():  # Если заполнены все поля, то регистрируем
            if session.query(User).filter(
                    User.email == form.email.data).first():  # Если уже зарегистрирована такая почта, то отправляем ошибку
                return render_template('register.html', message='Данная почта уже зарегистрирована, попробуйте войти.',
                                       form=form, admin_name=admin.name)

            # Создаем аккаунт
            user_id = requests.post(f'{request.host_url}api/users', json={'name': form.name.data,
                                                                          'email': form.email.data,
                                                                          'telegram_tag': form.telegram_tag.data,
                                                                          'password': form.password.data,
                                                                          'project_id': project.id})

            if user_id.status_code == 200:  # Если данные введены под формат
                login_user(session.get(User, user_id.json()['user_id']), remember=form.remember_me.data)
                return redirect('/')

            # Иначе пишем ошибку
            return render_template('register.html', title=f'Данные введены некорректно: {user_id.json()['message']}',
                                   form=form, admin_name=admin.name)

        # Иначе отображаем просто страницу
        return render_template('register.html', title='Присоединение к проекту', form=form, admin_name=admin.name)
    finally:
        session.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователей"""
    if current_user.is_authenticated:  # Проверка авторизирован ли человек
        return redirect('/')

    session = create_session()
    try:
        form = RegisterForm()
        if form.validate_on_submit():  # Если заполнены все поля, то регистрируем
            if session.query(User).filter(
                    User.email == form.email.data).first():  # Если уже зарегистрирована такая почта, то отправляем ошибку
                return render_template('register.html', form=form,
                                       message='Данная почта уже зарегистрирована, попробуйте войти')

            # Создаем аккаунт
            user_id = requests.post(f'{request.host_url}api/users', json={'name': form.name.data,
                                                                          'email': form.email.data,
                                                                          'telegram_tag': form.telegram_tag.data,
                                                                          'password': form.password.data})
            if user_id.status_code == 200:  # Если данные введены под формат
                login_user(session.get(User, user_id.json()['user_id']), remember=form.remember_me.data)
                return redirect('/')

            # Иначе пишем ошибку
            return render_template('register.html', form=form,
                                   message=f'Данные введены некорректно: {user_id.json()['message']}')
        return render_template('register.html', title='Стать логистом', form=form)
    finally:
        session.close()


@app.route('/logout')
def logout():  # Выход из аккаунта
    logout_user()
    return redirect('/login')


@app.route('/test')
def test():  # Создан для быстрого тестирования сайта
    if current_user.is_authenticated and current_user.status == 'admin':
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
                                  'project_id': 1, 'price': 1512, 'comment': 'бобер мне снес квартиру',
                                  'who_delivers': 2}, cookies=request.cookies).json())
        return redirect('/projects')
    return redirect('/')


if __name__ == '__main__':
    main()
    port = os.environ.get('PORT', 5015)
    app.run(threaded=True, host='0.0.0.0', port=port)
