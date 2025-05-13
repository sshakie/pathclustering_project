from flask_restful import abort, Resource, reqparse
from data.sql.__all_models import CourierRelations
from data.sql.__all_models import UserRelations
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from data.sql.__all_models import User
from flask_login import current_user
from flask import jsonify
import random

user_parser = reqparse.RequestParser()
user_parser.add_argument('name', required=True, type=str)
user_parser.add_argument('email', required=True, type=str)
user_parser.add_argument('password', required=True, type=str)
user_parser.add_argument('telegram_tag', type=str)
user_parser.add_argument('project_id')
user_parser.add_argument('admin_id')

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument('name', type=str)
put_user_parser.add_argument('email', type=str)
put_user_parser.add_argument('password', type=str)
put_user_parser.add_argument('telegram_tag', type=str)


class UsersResource(Resource):
    def get(self, user_id):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                try:
                    relation = session.query(UserRelations).filter(UserRelations.courier_id == user_id).first()
                    if relation.admin_id != current_user.id:  # Если курьер не принадлежит вам, то выдаем ошибку
                        abort(403, message=f"This is not your worker")

                    user = session.query(User).get(user_id)
                    return jsonify({'user': user.to_dict(only=('id', 'name', 'email', 'telegram_tag', 'status'))})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def delete(self, user_id):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                try:
                    relation = session.query(UserRelations).filter(UserRelations.courier_id == user_id).first()
                    if relation.admin_id != current_user.id:  # Если курьер не принадлежит вам, то выдаем ошибку
                        abort(403, message=f"This is not your worker")

                    for i in session.query(Order).filter(
                            Order.who_delivers == user_id).all():  # Удаляем у заказов курьера
                        i.who_delivers = -1

                    session.delete(session.query(User).get(user_id))
                    session.delete(session.query(UserRelations).filter(UserRelations.courier_id == user_id).first())
                    session.commit()
                    return jsonify({'success': 'deleted!'})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def put(self, user_id):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                args = put_user_parser.parse_args() # Получаем все аргументы, которые передали

                session = create_session()
                try:
                    relation = session.query(UserRelations).filter(UserRelations.courier_id == user_id).first()
                    if relation.admin_id != current_user.id:  # Если курьер не принадлежит вам, то выдаем ошибку
                        abort(403, message=f"This is not your worker")

                    # Изменяем данные
                    user = session.query(User).get(user_id)
                    if args['name']:
                        user.name = args.name
                    if args['email']:
                        user.email = args.email
                    if args['password']:
                        user.set_password(args['password'])
                    if args['telegram_tag']:
                        # Если написан тег не так, как мы хотим, то меняем
                        if '@' not in args['telegram_tag']:
                            user.telegram_tag = f'@{args['telegram_tag']}'
                        else:
                            user.telegram_tag = args['telegram_tag']

                    session.commit()
                    return jsonify({'success': 'edited!'})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


class UsersListResource(Resource):
    def get(self):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                session = create_session()
                try:
                    projects = session.query(Project).filter(Project.admin_id == current_user.id).all()

                    # Ищем тех, кто принадлежит вам
                    cr = session.query(CourierRelations).filter(CourierRelations.project_id == i.id).all()
                    return jsonify({'projects': {
                        i.id: [ii.to_dict(only=('id', 'name', 'email', 'telegram_tag', 'status')) for ii in cr]} for i
                        in projects})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def post(self):
        # Проверка авторизирован ли пользователь
        if not current_user.is_authenticated:
            args = user_parser.parse_args()  # Получаем все аргументы, которые передали

            session = create_session()
            try:
                ###################################
                ##### Проверки для project_id #####
                ###################################
                if args['project_id']:
                    if args['project_id'].isdigit():  # Если получили один айди
                        project = [session.get(Project, int(args['project_id']))]

                    elif type(args['project_id']) == list:  # Если же получили список айди
                        try:
                            project = [session.get(Project, i) for i in args['project_id']]
                        except Exception:
                            abort(400, message=f"Invalid data type in project_id.list")

                    # Иначе выводим ошибку
                    else:
                        abort(400, message=f"Invalid project_id data type")

                    if not project:  # Если проект не существует, то выводим ошибку
                        abort(404, message=f"This project isn't exists")

                    admin_ids = set([i.admin_id for i in project])
                    if len(admin_ids) != 1:  # Если у айди полученного проектов не одни и те же админы
                        abort(400, message=f"Projects can only have the same admin")

                if '@' not in args['email'] or '.' not in args['email']:  # проверка правильная ли почта
                    abort(400, message=f"Email isn't correct")

                if args['admin_id'] and args['project_id']:
                    if admin_ids[0] != args['admin_id']:
                        abort(400, message=f"Admin_id and admin_id in args project(s) aren't the same")

                ###################################

                # Создаем аккаунт
                user = User(name=args['name'], email=args['email'])
                if args['telegram_tag']:
                    # Если написан тег не так, как мы хотим, то меняем
                    if '@' not in args['telegram_tag']:
                        user.telegram_tag = f'@{args['telegram_tag']}'
                    else:
                        user.telegram_tag = args['telegram_tag']

                # Если пользователь не принадлежит никому (проекту и логисту), то он сам логист
                if not args['project_id'] and not args['admin_id']:
                    user.status = 'admin'

                # Продолжаем настраивать
                user.color = random.choice(
                    ['#FF6A00', '#AA00FF', '#D45564', '#31AF7D', '#BE8737', '#7F7F7F', '#698239'])
                user.set_password(args['password'])
                session.add(user)
                session.commit()

                user_id = user.id
                if args['project_id']:  # Если есть связь с проектом, то добавляем связи
                    for i in project:
                        i.couriers.append(user)

                    if not args['admin_id']:
                        session.add(UserRelations(admin_id=project[0].admin_id, courier_id=user_id))

                if args['admin_id']:  # Если есть связь с логистом, то добавляем
                    session.add(UserRelations(admin_id=args['admin_id'], courier_id=user_id))

                session.commit()
                session.close()
                return jsonify({'success': 'created!', 'user_id': user_id})
            finally:
                session.close()
        # Иначе выводим ошибку
        abort(403, message=f"You have already created an account")


def abort_if_user_not_found(user_id):  # Проверка на существование такого пользователя
    session = create_session()
    try:
        if not session.get(User, user_id):
            abort(404, message=f'User {user_id} not found')
    finally:
        session.close()
