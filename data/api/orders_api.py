from data.sql.models.user_relations import UserRelations
from data.py.geocoder import get_coords_from_geocoder
from flask_restful import abort, Resource, reqparse
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from data.sql.__all_models import User
from flask_login import current_user
from wtforms import ValidationError
from flask import jsonify
import re

order_parser = reqparse.RequestParser()
order_parser.add_argument('phone', required=True, type=str)
order_parser.add_argument('name', required=True, type=str)
order_parser.add_argument('address', required=True, type=str)
order_parser.add_argument('project_id', required=True, type=int)
order_parser.add_argument('price', type=int, default=0)
order_parser.add_argument('comment', type=str)
order_parser.add_argument('analytics_id', type=str)
order_parser.add_argument('who_delivers', type=int)

put_order_parser = reqparse.RequestParser()
put_order_parser.add_argument('phone', type=str)
put_order_parser.add_argument('name', type=str)
put_order_parser.add_argument('address', type=str)
put_order_parser.add_argument('price', type=int)
put_order_parser.add_argument('comment', type=str)
put_order_parser.add_argument('analytics_id', type=str)
put_order_parser.add_argument('who_delivers', type=int)


class OrdersResource(Resource):
    def get(self, order_id):
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.get(Project, order.project_id)
            if project.admin_id == current_user.id:
                session.close()
                return jsonify({'order': order.to_dict(
                    only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'comment', 'analytics_id',
                          'who_delivers'))})
            session.close()
            abort(403, message="This is not your order")
        abort(401, message="You're not logged in")

    def delete(self, order_id):
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.query(Project).filter(Project.id == order.project_id).first()
            if project.admin_id == current_user.id:  # Проверяем, принадлежит проект пользователю
                session.delete(order)
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            session.close()
            abort(403, message="This is not your order")
        abort(401, message="You're not logged in")

    def put(self, order_id):
        # Обновление заказа
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.query(Project).filter(Project.id == order.project_id).first()
            if project.admin_id == current_user.id:
                args = put_order_parser.parse_args()
                # Проверяем наличие не обяхательных аргументов в парсере
                if args['phone']:
                    try:
                        is_right_phone_number(args['phone'])  # Валидация телефона
                        order.phone = args.phone
                    except ValidationError:
                        abort(400, message="Wrong phone number format")
                if args['name']:
                    order.name = args.name
                if args['address']:
                    try:
                        order.set_coords(get_coords_from_geocoder(args.address))  # Установка координат
                        order.address = args.address
                    except Exception:
                        abort(404, message="This address isn't exists or invalid")
                if args['price']:
                    order.price = args.price
                if args['comment']:
                    order.comment = args.comment
                if args['analytics_id']:
                    order.analytics_id = args['analytics_id']
                if args['who_delivers']:
                    # Проверка курьера
                    checking = session.query(User).filter(User.id == args['who_delivers']).all()
                    ur = session.query(UserRelations).filter(UserRelations.courier_id == args['who_delivers']).first()
                    if checking:
                        if ur.admin_id == current_user.id:
                            order.who_delivers = args['who_delivers']
                        else:
                            abort(400, message="This is not your courier")
                    else:
                        abort(404, message="User.who_delivers.id is not found")
                session.commit()
                session.close()
                return jsonify({'success': 'edited!'})
            session.close()
            abort(403, message="This is not your order")
        abort(401, message="You're not logged in")


# Класс для списка заказов и создания новых
class OrdersListResource(Resource):
    def get(self):
        """Получение всех заказов, связанных с проектами текущего админа"""
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            session = create_session()
            try:
                projects = session.query(Project).filter(Project.admin_id == current_user.id).all()
                orders = []
                for project in projects:
                    orders.extend(session.query(Order).filter(Order.project_id == project.id).all())
                return jsonify({'orders': [
                    i.to_dict(only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'comment', 'analytics_id',
                                    'who_delivers'))
                    for i in orders]})
            finally:
                session.close()
        abort(401, message="You're not logged in")

    def post(self):
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            if current_user.status == 'admin':
                args = order_parser.parse_args()
                session = create_session()
                project = session.query(Project).filter(Project.id == args['project_id']).first()
                if project:
                    try:
                        is_right_phone_number(args['phone'])  # Проверка телефона
                    except ValidationError:
                        abort(400, message="Wrong phone number format")

                    order = Order(
                        phone=args['phone'],
                        name=args['name'],
                        address=args['address'],
                        project_id=args['project_id']
                    )

                    # Получение координат по адресу
                    try:
                        order.set_coords(get_coords_from_geocoder(args['address']))
                    except Exception:
                        abort(400, message="This address isn't exists or invalid")

                    # Установка необязательных полей
                    if args['price']:
                        order.price = args['price']
                    if args['comment']:
                        order.comment = args['comment']
                    if args['analytics_id']:
                        order.analytics_id = args['analytics_id']
                    if args['who_delivers']:
                        order.who_delivers = args['who_delivers']

                    # Проверка, принадлежит ли проект текущему пользователю
                    if project.admin_id == current_user.id:
                        session.add(order)
                        session.commit()
                        order_id = order.id
                        session.close()
                        return jsonify({'success': 'created!', 'order_id': order_id})
                    session.close()
                abort(404, message="This project is not exists")
            abort(403, message="You're not admin")
        abort(401, message="You're not logged in")


# Проверка наличия заказа по ID
def abort_if_order_not_found(order_id):
    session = create_session()
    order = session.get(Order, order_id)
    if not order:
        abort(404, message=f'Order {order_id} not found')
    session.close()


# Проверка корректности формата номера телефона
def is_right_phone_number(number):
    s = number
    remainder = ''
    if s.startswith('+7'):
        remainder = s[2:]
    elif s.startswith('8'):
        remainder = s[1:]
    else:
        raise ValidationError('Телефон должен начинаться с +7 или 8')

    remainder = re.sub(r'[ -]', '', remainder)  # Удаление пробелов и дефисов

    if re.match(r'^\(\d{3}\)', remainder):  # Обработка формата с кодом в скобках
        remainder = re.sub(r'\(', '', remainder, 1)
        remainder = re.sub(r'\)', '', remainder, 1)

    if not re.match(r'^\d{10}$', remainder):  # Должно остаться ровно 10 цифр
        raise ValidationError('Неверный формат телефона')
