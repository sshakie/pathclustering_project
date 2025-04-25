from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource

from data import db_session
from data.all_modules import Users

class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = db_session.create_session()
        user = session.query(Users).get(user_id)
        return jsonify({'user': user.to_dict()})

    def post(self):
        pass # TODO: Сделать добавление пользователей

    def delete(self):
        pass # TODO: Сделать удаление пользователей

    def put(self):
        pass # TODO: Сделать изменение пользователей


def abort_if_user_not_found(user_id):
    session = db_session.create_session()
    user = session.query(Users).get(user_id)
    if not user:
        session.close()
        abort(404, message=f"User {user_id} not found")
    else:
        session.close()