from flask_restful import abort, Resource, reqparse
from data.sql.__all_models import CourierRelations
from data.sql.__all_models import UserRelations
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from data.sql.__all_models import User
from flask_login import current_user
from flask import jsonify

cr_parser = reqparse.RequestParser()
cr_parser.add_argument('project_id', required=True, type=int)
cr_parser.add_argument('courier_id', required=True, type=int)


class CourierRelationsListResource(Resource):
    def post(self):
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            if current_user.status == 'admin':
                args = cr_parser.parse_args()
                session = create_session()
                project = session.get(Project, args['project_id'])
                courier = session.get(User, args['courier_id'])

                if not project:
                    abort(404, message=f'Project {args["project_id"]} not found')

                if not courier:
                    abort(404, message=f'User {args["courier_id"]} not found')

                if project.admin_id != current_user.id:
                    abort(403, message=f"This isn't your project")

                # Проверяем, принадлежит ли указанный курьер текущему админу
                ur = session.query(UserRelations).filter(UserRelations.courier_id == args['courier_id']).first()
                if ur.admin_id != current_user.id:
                    abort(403, message=f"This isn't your courier")

                # Проверяем, существует ли уже связь между этим курьером и проектом
                cr = session.query(CourierRelations).filter(CourierRelations.courier_id == args['courier_id']).all()
                if [i for i in cr if i.project_id == args['project_id']]:
                    abort(403, message=f"CourierRelations between project and courier already exists")

                # Создаём новую связь между курьером и проектом
                session.add(CourierRelations(courier_id=args['courier_id'], project_id=args['project_id']))
                session.commit()
                session.close()
                return jsonify({'success': 'created!'})

            abort(403, message=f"You're not admin")  # Пользователь не админ — доступ запрещён
        abort(401, message=f"You're not logged in")  # Пользователь не авторизован — доступ запрещён


    def delete(self):
        if current_user.is_authenticated:  # Проверяем, авторизован ли пользователь
            if current_user.status == 'admin':  # Проверяем, является ли пользователь админом
                args = cr_parser.parse_args()
                session = create_session()
                project = session.get(Project, args['project_id'])
                courier = session.get(User, args['courier_id'])

                # Проверки на существование проекта и курьера
                if not project:
                    abort(404, message=f'Project {args["project_id"]} not found')
                if not courier:
                    abort(404, message=f'User {args["courier_id"]} not found')

                if project.admin_id != current_user.id:  # Проверяем, принадлежит ли проект текущему админу
                    abort(403, message=f"This isn't your project")

                # Проверяем, принадлежит ли курьер текущему админу
                # Ищем все связи курьера с проектами и оставляем только те, что относятся к нужному проекту
                ur = session.query(UserRelations).filter(UserRelations.courier_id == args['courier_id']).first()
                if ur.admin_id != current_user.id:
                    abort(403, message=f"This isn't your courier")
                cr = session.query(CourierRelations).filter(CourierRelations.courier_id == args['courier_id']).all()
                spisok = [i for i in cr if i.project_id == args['project_id']]

                # Если такой связи нет, вернуть ошибку
                if not spisok:
                    abort(403, message=f"CourierRelations between project and courier doesn't exists")
                for i in session.query(Order).filter(Order.who_delivers == spisok[0].courier_id).all():
                    i.who_delivers = -1  # -1 означает что заказ никому не назначен

                # Удаляем связь курьера с проектом
                session.delete(spisok[0])
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})

            abort(403, message=f"You're not admin")  # Пользователь не админ — отказ в доступе
        abort(401, message=f"You're not logged in")  # Пользователь не авторизован — отказ в доступе
