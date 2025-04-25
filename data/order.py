from sqlalchemy_serializer import SerializerMixin
from data.db_session import SqlAlchemyBase
import sqlalchemy, datetime


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    phone = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    analytics_id = sqlalchemy.Column(sqlalchemy.String, unique=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
