from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy, random


class Project(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    icon = sqlalchemy.Column(sqlalchemy.Integer)
    admin_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    couriers = sqlalchemy.Column(sqlalchemy.String)
    orders = sqlalchemy.Column(sqlalchemy.String)

    admin = orm.relationship('User', lazy='joined')
