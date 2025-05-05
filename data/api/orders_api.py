from data.api.geocoder_api import get_coords_from_geocoder
from flask_restful import abort, Resource, reqparse
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from flask_login import current_user
from flask import jsonify

order_parser = reqparse.RequestParser()
order_parser.add_argument('phone', required=True, type=str)
order_parser.add_argument('name', required=True, type=str)
order_parser.add_argument('address', required=True, type=str)
order_parser.add_argument('project_id', required=True, type=str)
order_parser.add_argument('price', type=str)
order_parser.add_argument('analytics_id', type=str)
order_parser.add_argument('who_delivers', type=int)

put_order_parser = reqparse.RequestParser()
put_order_parser.add_argument('phone', type=str)
put_order_parser.add_argument('name', type=str)
put_order_parser.add_argument('address', type=str)
put_order_parser.add_argument('price', type=str)
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
                        only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'analytics_id',
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
                if 'phone' in args:
                    order.phone = args.phone
                if 'name' in args:
                    order.name = args.name
                if 'address' in args:
                    order.address = args.address
                    order.set_coords(get_coords_from_geocoder(args.address))
                if 'price' in args:
                    order.price = args.price
                if 'analytics_id' in args:
                    order.analytics_id = args.analytics_id
                if 'who_delivers' in args:
                    order.who_delivers = args.who_delivers
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
                    only=('id', 'phone', 'name', 'address', 'project_id', 'price', 'analytics_id', 'who_delivers'))
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
                    order.set_coords(get_coords_from_geocoder(args['address']))
                    if 'price' in args:
                        order.price = args['price']
                    if 'analytics_id' in args:
                        order.analytics_id = args['analytics_id']
                    if 'who_delivers' in args:
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
