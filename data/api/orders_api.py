from flask_restful import abort, Resource, reqparse
from data.sql.db_session import create_session
from data.sql.__all_models import Order
from flask_login import current_user
from flask import jsonify

order_parser = reqparse.RequestParser()
order_parser.add_argument('phone', required=True, type=str)
order_parser.add_argument('name', required=True, type=str)
order_parser.add_argument('address', required=True, type=str)
order_parser.add_argument('price', type=str)
order_parser.add_argument('analytics_id', type=str)
order_parser.add_argument('who_delivers', type=int)
order_parser.add_argument('apikey', type=str)

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
            if order_id.isdigit():
                order = session.query(Order).get(order_id)
            else:
                order = session.query(Order).filter(Order.analytics_id == order_id).first()
            session.close()
            return jsonify(
                {'order': order.to_dict(
                    only=('id', 'phone', 'name', 'address', 'price', 'analytics_id', 'who_delivers'))})
        abort(401, message=f"You're not logged in")

    def delete(self, order_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_order_not_found(order_id)
                session = create_session()
                session.delete(session.query(Order).get(order_id))
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def put(self, order_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_order_not_found(order_id)
                args = put_order_parser.parse_args()
                session = create_session()
                order = session.query(Order).get(order_id)
                if 'phone' in args:
                    order.phone = args.phone
                if 'name' in args:
                    order.name = args.name
                if 'address' in args:
                    order.address = args.address
                if 'price' in args:
                    order.price = args.price
                if 'analytics_id' in args:
                    order.analytics_id = args.analytics_id
                if 'who_delivers' in args:
                    order.who_delivers = args.who_delivers
                session.close()
                return jsonify({'success': 'edited!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


class OrdersListResource(Resource):
    def get(self):
        if current_user.is_authenticated:
            session = create_session()
            orders = session.query(Order).filter(Order.who_delivers == current_user.id).all()
            session.close()
            return jsonify({'orders':
                [i.to_dict(
                    only=('id', 'phone', 'name', 'address', 'price', 'analytics_id', 'who_delivers'))
                    for i in orders]})
        abort(401, message=f"You're not logged in")

    def post(self):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                args = order_parser.parse_args()
                session = create_session()
                order = Order(phone=args['phone'], name=args['name'], address=args['address'])
                if 'price' in args:
                    order.price = args['price']
                if 'analytics_id' in args:
                    order.analytics_id = args['analytics_id']
                if 'who_delivers' in args:
                    order.who_delivers = args['who_delivers']
                session.add(order)
                session.commit()
                session.close()
                return jsonify({'success': 'created!'})

            abort(403, message=f"You're not admin")

        else:  # TODO: Переделать апи
            args = order_parser.parse_args()
            if 'apikey' in args:
                if args['apikey'] == '123':
                    session = create_session()
                    order = Order(phone=args['phone'], name=args['name'], address=args['address'])
                    if 'price' in args:
                        order.price = args['price']
                    if 'analytics_id' in args:
                        order.analytics_id = args['analytics_id']
                    if 'who_delivers' in args:
                        order.who_delivers = args['who_delivers']
                    session.add(order)
                    session.commit()
                    session.close()
                    return jsonify({'success': 'created!'})

        abort(401, message=f"You're not logged in")


def abort_if_order_not_found(order_id):
    session = create_session()
    if order_id.isdigit():
        order = session.query(Order).get(order_id)
    else:
        order = session.query(Order).filter(Order.analytics_id == order_id).first()
    if not order:
        abort(404, message=f'Order {order_id} not found')
    session.close()
