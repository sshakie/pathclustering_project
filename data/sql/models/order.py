from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
import sqlalchemy, datetime


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    phone = sqlalchemy.Column(sqlalchemy.String, index=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    longitude = sqlalchemy.Column(sqlalchemy.Float)
    latitude = sqlalchemy.Column(sqlalchemy.Float)
    who_delivers = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'), default=-1)
    analytics_id = sqlalchemy.Column(sqlalchemy.String)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    def set_coords(self, data):
        if isinstance(data, str):
            data = list(reversed(list(map(float, data.split(',')))))
            self.longitude = data[0]
            self.latitude = data[1]

        elif isinstance(data, tuple) or isinstance(data, list):
            self.longitude = data[0]
            self.latitude = data[1]

    def get_coords(self):
        return self.longitude, self.latitude
