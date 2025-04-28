from flask_restful import abort, Resource, reqparse
from data.db_session import create_session
from flask_login import current_user
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
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                user = session.query(User).get(user_id)
                session.close()
                return jsonify({'user': user.to_dict(only=('id', 'name', 'email', 'status'))})
            abort(404, message=f"You're not admin")
        abort(404, message=f"You're not logged in")

    def delete(self, user_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                session.delete(session.query(User).get(user_id))
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            abort(404, message=f"You're not admin")
        abort(404, message=f"You're not logged in")

    def put(self, user_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
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
            abort(404, message=f"You're not admin")
        abort(404, message=f"You're not logged in")


class UsersListResource(Resource):
    def get(self):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                session = create_session()
                users = session.query(User).all()
                return jsonify({'users': [i.to_dict(only=('id', 'name', 'email', 'status')) for i in users]})
            abort(404, message=f"You're not admin")
        abort(404, message=f"You're not logged in")

    def post(self):
        if not current_user.is_authenticated or current_user.status == 'admin':
            args = user_parser.parse_args()
            session = create_session()
            user = User(name=args['name'], email=args['email'], status=args['status'])
            user.set_password(args['password'])
            session.add(user)
            session.commit()
            session.close()
            return jsonify({'success': 'created!'})
        abort(404, message=f"You have already created an account")


def abort_if_user_not_found(user_id):
    session = create_session()
    user = session.query(User).get(user_id)
    if not user:
        abort(404, message=f'User {user_id} not found')
    session.close()
