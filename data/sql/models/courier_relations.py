from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
import sqlalchemy


class CourierRelations(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'courier_relations'

    courier_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id', ondelete='CASCADE'),
                                   primary_key=True)
    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id', ondelete='CASCADE'),
                                   primary_key=True)
