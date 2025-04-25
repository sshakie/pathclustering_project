from data.db_session import create_session
from flask_restful import abort, Resource
from data.__all_models import Order
from flask import jsonify


class OrderResource(Resource):
    def get(self, order_id):
        abort_if_order_not_found(order_id)
        db_sess = create_session()
        order = db_sess.query(Order).get(order_id)
        return jsonify({'order': order.to_dict()})

    def post(self):
        pass  # TODO: Сделать добавление заказов

    def delete(self):
        pass  # TODO: Сделать удаление заказов

    def put(self):
        pass  # TODO: Сделать изменение заказов


def abort_if_order_not_found(order_id):
    session = create_session()
    order = session.query(Order).get(order_id)
    if not order:
        abort(404, message=f'Order {order_id} not found')
    session.close()
