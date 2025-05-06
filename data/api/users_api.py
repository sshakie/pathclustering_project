from flask_restful import abort, Resource, reqparse
from data.sql.__all_models import CourierRelations
from data.sql.__all_models import UserRelations
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import User
from flask_login import current_user
from flask import jsonify

user_parser = reqparse.RequestParser()
user_parser.add_argument('name', required=True, type=str)
user_parser.add_argument('email', required=True, type=str)
user_parser.add_argument('password', required=True, type=str)
user_parser.add_argument('telegram_tag', type=str)
user_parser.add_argument('project_id', type=str)

put_user_parser = reqparse.RequestParser()
put_user_parser.add_argument('name', type=str)
put_user_parser.add_argument('email', type=str)
put_user_parser.add_argument('password', type=str)
put_user_parser.add_argument('telegram_tag', type=str)
put_user_parser.add_argument('is_ready', type=bool)


class UsersResource(Resource):
    def get(self, user_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                user = session.query(User).get(user_id)
                session.close()
                return jsonify(
                    {'user': user.to_dict(only=('id', 'name', 'email', 'telegram_tag', 'status'))})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def delete(self, user_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                session = create_session()
                session.delete(session.query(User).get(user_id))
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def put(self, user_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_user_not_found(user_id)
                args = put_user_parser.parse_args()
                session = create_session()
                user = session.query(User).get(user_id)
                if args['name']:
                    user.name = args.name
                if args['telegram_tag']:
                    if '@' not in args['telegram_tag']:
                        user.telegram_tag = f'@{args['telegram_tag']}'
                    else:
                        user.telegram_tag = args['telegram_tag']
                if args['email']:
                    user.email = args.email
                if args['password']:
                    user.set_password(args['password'])
                if 'is_ready' in args:
                    prj = session.query(CourierRelations).filter(CourierRelations.courier_id == user_id).first()
                    prj.is_ready = args['is_ready']
                session.commit()
                session.close()
                return jsonify({'success': 'edited!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


class UsersListResource(Resource):
    def get(self):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                session = create_session()
                projects = session.query(Project).filter(Project.admin_id == current_user.id).all()  ########
                users = session.query(User).all()
                return jsonify({'users': [i.to_dict(only=('id', 'name', 'email', 'telegram_tag', 'status'))
                                          for i in users]})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def post(self):
        if not current_user.is_authenticated:
            args = user_parser.parse_args()
            session = create_session()
            if args['project_id']:  # проверка существует ли проект
                project = session.get(Project, args['project_id'])
                if not project:
                    abort(404, message=f"This project isn't exists")

            if '@' not in args['email'] or '.' not in args['email']:  # проверка правильная ли почта
                abort(400, message=f"Email isn't correct")

            user = User(name=args['name'], email=args['email'])
            if args['telegram_tag']:
                if '@' not in args['telegram_tag']:  # редактируем поле, если написано не по-формату
                    user.telegram_tag = f'@{args['telegram_tag']}'
                else:
                    user.telegram_tag = args['telegram_tag']
            if not args['project_id']:  # проверка принадлежности пользователя, иначе - админ
                user.status = 'admin'
            user.set_password(args['password'])
            session.add(user)
            session.commit()
            user_id = user.id
            if args['project_id']:  # добавление в отношения
                project.couriers.append(user)
                session.add(UserRelations(admin_id=project.admin_id, courier_id=user_id))
            session.commit()
            session.close()
            return jsonify({'success': 'created!', 'user_id': user_id})
        abort(403, message=f"You have already created an account")


def abort_if_user_not_found(user_id):
    session = create_session()
    if not session.get(User, user_id):
        abort(404, message=f'User {user_id} not found')
    session.close()
