from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy


class OrderRelations(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'order_relations'

    order_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('orders.id'), primary_key=True, unique=True,
                                 ondelete='CASCADE')
    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id'), primary_key=True,
                                   ondelete='CASCADE')

    order = orm.relationship('Order', foreign_keys=[order_id])
    project = orm.relationship('Project', foreign_keys=[project_id])
