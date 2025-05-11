from data.py.geocoder import get_coords_from_geocoder
from data.blanks.orderform import is_right_phone_number
from flask_restful import abort, Resource, reqparse
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from data.sql.__all_models import User
from flask_login import current_user
from wtforms import ValidationError
from flask import jsonify

from data.sql.models.user_relations import UserRelations

order_parser = reqparse.RequestParser()
order_parser.add_argument('phone', required=True, type=str)
order_parser.add_argument('name', required=True, type=str)
order_parser.add_argument('address', required=True, type=str)
order_parser.add_argument('project_id', required=True, type=int)
order_parser.add_argument('price', type=int)
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
        if current_user.is_authenticated:
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.get(Project, order.project_id)
            if project.admin_id == current_user.id:
                session.close()
                return jsonify(
                    {'order': order.to_dict(
                        only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'comment', 'analytics_id',
                              'who_delivers'))})
            session.close()
            abort(403, message=f"This is not your order")
        abort(401, message=f"You're not logged in")

    def delete(self, order_id):
        if current_user.is_authenticated:
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.query(Project).filter(Project.id == order.project_id).first()
            if project.admin_id == current_user.id:
                session.delete(order)
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            session.close()
            abort(403, message=f"This is not your order")
        abort(401, message=f"You're not logged in")

    def put(self, order_id):
        if current_user.is_authenticated:
            abort_if_order_not_found(order_id)
            session = create_session()
            order = session.get(Order, order_id)
            project = session.query(Project).filter(Project.id == order.project_id).first()
            if project.admin_id == current_user.id:
                args = put_order_parser.parse_args()
                if args['phone']:
                    try:
                        is_right_phone_number('', args['phone'])
                        order.phone = args.phone
                    except ValidationError:
                        abort(400, message=f"Wrong phone number format")
                if args['name']:
                    order.name = args.name
                if args['address']:
                    try:
                        order.set_coords(get_coords_from_geocoder(args.address))
                        order.address = args.address
                    except Exception:
                        abort(404, message=f"This address isn't exists or invalid")
                if args['price']:
                    order.price = args.price
                if args['comment']:
                    order.comment = args.comment
                if args['analytics_id']:
                    order.analytics_id = args.analytics_id
                if args['who_delivers']:
                    checking = session.query(User).filter(User.id == args['who_delivers']).all()
                    ur = session.query(UserRelations).filter(
                        UserRelations.courier_id == args['who_delivers']).first()
                    if checking:
                        if ur.admin_id == current_user.id:
                            order.who_delivers = args.who_delivers
                        else:
                            abort(400, message=f"This is not your courier")
                    else:
                        abort(404, message=f"User.who_delivers.id is not found")
                session.commit()
                session.close()
                return jsonify({'success': 'edited!'})
            session.close()
            abort(403, message=f"This is not your order")
        abort(401, message=f"You're not logged in")


class OrdersListResource(Resource):
    def get(self):
        if current_user.is_authenticated:
            session = create_session()
            projects = session.query(Project).filter(Project.admin_id == current_user.id).all()
            orders = [session.query(Order).filter(Order.project_id == i).all() for i in projects]
            session.close()
            return jsonify({'orders':
                [i.to_dict(
                    only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'comment', 'analytics_id', 'who_delivers'))
                    for i in orders]})
        abort(401, message=f"You're not logged in")

    def post(self):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                args = order_parser.parse_args()
                session = create_session()
                project = session.query(Project).filter(Project.id == args['project_id']).first()
                if project:
                    order = Order(phone=args['phone'], name=args['name'], address=args['address'],
                                  project_id=args['project_id'])
                    try:
                        order.set_coords(get_coords_from_geocoder(args['address']))
                    except Exception:
                        abort(400, message=f"This address isn't exists or invalid")
                    if args['price']:
                        order.price = args['price']
                    if args['comment']:
                        order.comment = args['comment']
                    if args['analytics_id']:
                        order.analytics_id = args['analytics_id']
                    if args['who_delivers']:
                        order.who_delivers = args['who_delivers']
                    if project.admin_id == current_user.id:
                        session.add(order)
                        session.commit()
                        session.close()
                        return jsonify({'success': 'created!'})
                    session.close()
                abort(404, message=f"This project is not exists")
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


def abort_if_order_not_found(order_id):
    session = create_session()
    order = session.get(Order, order_id)
    if not order:
        abort(404, message=f'Order {order_id} not found')
    session.close()
