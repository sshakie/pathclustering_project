from data.db_session import create_session
from flask_restful import abort, Resource
from data.__all_models import User
from flask import jsonify


class UserResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        return jsonify({'user': user.to_dict()})

    def post(self):
        pass  # TODO: Сделать добавление пользователей

    def delete(self):
        pass  # TODO: Сделать удаление пользователей

    def put(self):
        pass  # TODO: Сделать изменение пользователей


def abort_if_user_not_found(user_id):
    session = create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f'User {user_id} not found')
    session.close()
