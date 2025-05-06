from flask_restful import abort, Resource, reqparse
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import Order
from flask_login import current_user
from flask import jsonify

project_parser = reqparse.RequestParser()
project_parser.add_argument('name', required=True, type=str)
project_parser.add_argument('icon', type=str)
project_parser.add_argument('invite_link', type=str)

put_project_parser = reqparse.RequestParser()
put_project_parser.add_argument('name', type=str)
put_project_parser.add_argument('icon', type=str)
put_project_parser.add_argument('invite_link', type=str)


class ProjectsResource(Resource):
    def get(self, project_id):
        if current_user.is_authenticated:
            abort_if_project_not_found(project_id)
            session = create_session()
            project = session.get(Project, project_id)
            session.close()
            if project.admin_id != current_user.id:
                abort(403, message=f"This is not your project")
            return jsonify(
                {'project': project.to_dict(
                    only=('id', 'name', 'icon', 'couriers'))})
        abort(401, message=f"You're not logged in")

    def delete(self, project_id):
        if current_user.is_authenticated:
            abort_if_project_not_found(project_id)
            session = create_session()
            project = session.get(Project, project_id)
            if not project:
                abort(403, message=f"This project isn't exists")
            if project.admin_id != current_user.id:
                abort(403, message=f"This is not your project")
            session.delete(project)

            for i in session.query(Order).filter(Order.project_id == project_id).all(): # удаление заказов, привязанных к проекту
                session.delete(i)
            session.commit()
            session.close()
            return jsonify({'success': 'deleted!'})
        abort(401, message=f"You're not logged in")

    def put(self, project_id):
        if current_user.is_authenticated:
            if current_user.status == 'admin':
                abort_if_project_not_found(project_id)
                args = put_project_parser.parse_args()
                session = create_session()
                project = session.get(Project, project_id)
                if 'name' in args:
                    project.name = args.name
                if 'icon' in args:
                    project.icon = args.icon
                if 'invite_link' in args:
                    project.invite_link = args.invite_link
                session.close()
                return jsonify({'success': 'edited!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")


class ProjectsListResource(Resource):
    def get(self):
        if current_user.is_authenticated:
            session = create_session()
            projects = session.query(Project).filter(Project.admin_id == current_user.id).all()
            session.close()
            return jsonify({'projects': [i.to_dict(
                only=('id', 'name', 'icon')) for i in projects]})
        abort(401, message=f"You're not logged in")

    def post(self):
        if current_user.is_authenticated:
            try:
                args = project_parser.parse_args()
                session = create_session()
                project = Project(name=args['name'], admin_id=current_user.id)
                if 'icon' in args:
                    project.icon = args['icon']
                if 'invite_link' in args:
                    project.invite_link = args['invite_link']
                session.add(project)
                session.commit()
                return jsonify({'success': 'created!', 'id': project.id, 'icon': project.icon})
            finally:
                session.close()
        abort(401, message=f"You're not logged in")


def abort_if_project_not_found(project_id):
    session = create_session()
    if not session.get(Project, project_id):
        abort(404, message=f'Project {project_id} not found')
    session.close()
