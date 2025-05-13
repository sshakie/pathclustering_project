from data.py.geocoder import get_coords_from_geocoder
from flask_restful import abort, Resource, reqparse
from data.sql.__all_models import CourierRelations
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from flask_login import current_user
from flask import jsonify
import random

project_parser = reqparse.RequestParser()
project_parser.add_argument('name', required=True, type=str)
project_parser.add_argument('icon', type=str)
project_parser.add_argument('invite_link', type=str)

put_project_parser = reqparse.RequestParser()
put_project_parser.add_argument('name', type=str)
put_project_parser.add_argument('icon', type=str)
put_project_parser.add_argument('invite_link', type=str)
put_project_parser.add_argument('storage', type=str)


class ProjectsResource(Resource):
    def get(self, project_id):
        # Проверка авторизирован ли пользователь
        if current_user.is_authenticated:
            abort_if_project_not_found(project_id)

            session = create_session()
            try:
                project = session.get(Project, project_id)
                if project.admin_id != current_user.id:  # Если проект не принадлежит вам, то выдаем ошибку
                    abort(403, message=f"This is not your project")
                return jsonify({'project': project.to_dict(only=('id', 'name', 'icon'))})
            finally:
                session.close()
        # Иначе выводим ошибку
        abort(401, message=f"You're not logged in")

    def delete(self, project_id):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_project_not_found(project_id)

                session = create_session()
                try:
                    project = session.get(Project, project_id)
                    if project.admin_id != current_user.id:  # Если проект не принадлежит вам, то выдаем ошибку
                        abort(403, message=f"This is not your project")

                    session.delete(project)
                    for i in session.query(Order).filter(
                            Order.project_id == project_id).all():  # Удаление заказов, привязанных к проекту
                        session.delete(i)

                    session.commit()
                    return jsonify({'success': 'deleted!'})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def put(self, project_id):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_project_not_found(project_id)
                args = put_project_parser.parse_args()  # Получаем все аргументы, которые передали

                session = create_session()
                try:
                    project = session.get(Project, project_id)
                    if project.admin_id != current_user.id:  # Если проект не принадлежит вам, то выдаем ошибку
                        abort(403, message=f"This is not your project")

                    # Редактируем проект
                    if args['name']:
                        project.name = args.name
                    if args['icon']:
                        project.icon = args.icon
                    if args['invite_link']:
                        project.invite_link = args.invite_link
                    if args['storage']:  # Изменение местоположение склада
                        try:
                            project.set_depot_coords(get_coords_from_geocoder(args.storage))
                        except Exception:
                            abort(404, message=f"This address isn't exists or invalid")

                    session.commit()
                    return jsonify({'success': 'edited!'})
                finally:
                    session.close()
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


class ProjectsListResource(Resource):
    def get(self):
        # Проверка авторизирован ли пользователь
        if current_user.is_authenticated:
            session = create_session()
            try:
                # Выдача проектов роли
                if current_user.status == 'admin':
                    projects = session.query(Project).filter(Project.admin_id == current_user.id).all()
                else:
                    prj_ids = session.query(CourierRelations).filter(
                        CourierRelations.courier_id == current_user.id).all()
                    projects = [session.get(Project, i.project_id) for i in prj_ids]
                return jsonify({'projects': [i.to_dict(only=('id', 'name', 'icon', 'admin_id')) for i in projects]})
            finally:
                session.close()
        # Иначе выводим ошибку
        abort(401, message=f"You're not logged in")

    def post(self):
        # Проверка подходит ли человек
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                args = project_parser.parse_args()  # Получаем все аргументы, которые передали

                session = create_session()
                try:
                    # Добавляем проект
                    project = Project(name=args['name'], admin_id=current_user.id)
                    if args['icon']:
                        project.icon = args['icon']

                    # Создаем реферальную ссылку, если она не передана
                    if args['invite_link']:
                        project.invite_link = args['invite_link']
                    else:
                        project.invite_link = ''.join(
                            ['0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'[random.randint(1, 61)] for
                             i in range(11)])

                    session.add(project)
                    session.commit()
                    return jsonify({'success': 'created!', 'id': project.id, 'icon': project.icon})
                finally:
                    session.close()
            # Иначе выводим ошибки
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


def abort_if_project_not_found(project_id):  # Проверка на существование такого проекта
    session = create_session()
    if not session.get(Project, project_id):
        abort(404, message=f'Project {project_id} not found')
    session.close()
