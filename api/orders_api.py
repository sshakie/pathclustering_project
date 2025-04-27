from flask_restful import abort, Resource, reqparse
from data.db_session import create_session
from data.__all_models import Order
from flask import jsonify

order_parser = reqparse.RequestParser()
order_parser.add_argument('phone', required=True, type=str)
order_parser.add_argument('name', required=True, type=str)
order_parser.add_argument('address', required=True, type=str)
order_parser.add_argument('price', type=str)
order_parser.add_argument('analytics_id', type=str)

put_order_parser = reqparse.RequestParser()
put_order_parser.add_argument('phone', type=str)
put_order_parser.add_argument('name', type=str)
put_order_parser.add_argument('address', type=str)
put_order_parser.add_argument('price', type=str)
put_order_parser.add_argument('analytics_id', type=str)


class OrdersResource(Resource):
    def get(self, order_id):
        abort_if_order_not_found(order_id)
        session = create_session()
        order = session.query(Order).get(order_id)
        session.close()
        return jsonify({'order': order.to_dict()})

    def delete(self, order_id):
        abort_if_order_not_found(order_id)
        session = create_session()
        session.delete(session.query(Order).get(order_id))
        session.commit()
        session.close()
        return jsonify({'success': 'deleted!'})

    def put(self, order_id):
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
        session.close()
        return jsonify({'success': 'edited!'})


class OrdersListResource(Resource):
    def get(self):
        session = create_session()
        orders = session.query(Order).all()
        session.close()
        return jsonify({'orders': [i.to_dict() for i in orders]})

    def post(self):
        args = order_parser.parse_args()
        session = create_session()
        order = Order(phone=args['phone'], name=args['name'], address=args['address'])
        if 'price' in args:
            order.price = args['price']
        if 'analytics_id' in args:
            order.price = args['analytics_id']
        session.add(order)
        session.commit()
        session.close()
        return jsonify({'success': 'created!'})


def abort_if_order_not_found(user_id):
    session = create_session()
    order = session.query(Order).get(user_id)
    if not order:
        abort(404, message=f'Order {user_id} not found')
    session.close()
