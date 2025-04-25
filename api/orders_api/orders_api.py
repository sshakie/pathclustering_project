from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource

from data import db_session
from data.all_modules import Orders


class OrderResource(Resource):
    def get(self, order_id):
        abort_if_order_not_found(order_id)
        session = db_session.create_session()
        order = session.query(Orders).get(order_id)
        return jsonify({'order': order.to_dict()})

    def post(self):
        pass  # TODO: Сделать добавление заказов

    def delete(self):
        pass  # TODO: Сделать удаление заказов

    def put(self):
        pass  # TODO: Сделать изменение заказов


def abort_if_order_not_found(order_id):
    session = db_session.create_session()
    order = session.query(Orders).get(order_id)
    if not order:
        session.close()
        abort(404, message=f"Order {order_id} not found")
    else:
        session.close()