from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
from sqlalchemy import orm
import sqlalchemy


class UserRelations(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'user_relations'

    courier_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id', ondelete='CASCADE'),
                                   primary_key=True, unique=True)
    admin_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id', ondelete='CASCADE'),
                                 primary_key=True)

    courier = orm.relationship('User', foreign_keys=[courier_id])
    admin = orm.relationship('User', foreign_keys=[admin_id])
