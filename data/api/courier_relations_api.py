from flask_restful import abort, Resource, reqparse
from data.sql.__all_models import CourierRelations
from data.sql.__all_models import UserRelations
from data.sql.db_session import create_session
from data.sql.__all_models import Project
from data.sql.__all_models import User
from flask_login import current_user
from flask import jsonify

cr_parser = reqparse.RequestParser()
cr_parser.add_argument('project_id', required=True, type=int)
cr_parser.add_argument('courier_id', required=True, type=int)


class CourierRelationsListResource(Resource):
    def post(self):
        if current_user.is_authenticated:
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
                ur = session.query(UserRelations).filter(UserRelations.courier_id == args['courier_id']).first()
                if ur.admin_id != current_user.id:
                    abort(403, message=f"This isn't your courier")
                cr = session.query(CourierRelations).filter(CourierRelations.courier_id == args['courier_id']).all()
                if [i for i in cr if i.project_id == args['project_id']]:
                    abort(403, message=f"CourierRelations between project and courier already exists")
                session.add(CourierRelations(courier_id=args['courier_id'], project_id=args['project_id']))
                session.commit()
                session.close()
                return jsonify({'success': 'created!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")

    def delete(self):
        if current_user.is_authenticated:
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
                ur = session.query(UserRelations).filter(UserRelations.courier_id == args['courier_id']).first()
                if ur.admin_id != current_user.id:
                    abort(403, message=f"This isn't your courier")
                cr = session.query(CourierRelations).filter(CourierRelations.courier_id == args['courier_id']).all()
                spisok = [i for i in cr if i.project_id == args['project_id']]
                if not spisok:
                    abort(403, message=f"CourierRelations between project and courier doesn't exists")
                session.delete(spisok[0])
                session.commit()
                session.close()
                return jsonify({'success': 'deleted!'})
            abort(403, message=f"You're not admin")
        abort(401, message=f"You're not logged in")
