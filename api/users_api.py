from flask_restful import abort, Resource, reqparse
from data.db_session import create_session
from data.__all_models import User
from flask import jsonify

user_parser = reqparse.RequestParser()
user_parser.add_argument('name', required=True, type=str)
user_parser.add_argument('email', required=True, type=str)
user_parser.add_argument('password', required=True, type=str)
user_parser.add_argument('status', default='delivery', type=str)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument('name', type=str)
put_user_parser.add_argument('email', type=str)
put_user_parser.add_argument('password', type=str)
put_user_parser.add_argument('status', default='delivery', type=str)


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        session = create_session()
        user = session.query(User).get(user_id)
        session.close()
        return jsonify({'user': user.to_dict()})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        session = create_session()
        session.delete(session.query(User).get(user_id))
        session.commit()
        session.close()
        return jsonify({'success': 'deleted!'})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        args = put_user_parser.parse_args()
        session = create_session()
        user = session.query(User).get(user_id)
        if 'name' in args:
            user.name = args.name
        if 'status' in args:
            user.status = args.status
        if 'email' in args:
            user.email = args.email
        if 'password' in args:
            user.set_password(args['password'])
        session.close()
        return jsonify({'success': 'edited!'})


class UsersListResource(Resource):
    def get(self):
        session = create_session()
        users = session.query(User).all()
        session.close()
        return jsonify({'users': [i.to_dict() for i in users]})

    def post(self):
        args = user_parser.parse_args()
        session = create_session()
        user = User(name=args['name'], email=args['email'], status=args['status'])
        user.set_password(args['password'])
        session.add(user)
        session.commit()
        session.close()
        return jsonify({'success': 'created!'})


def abort_if_user_not_found(user_id):
    session = create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f'User {user_id} not found')
    session.close()
