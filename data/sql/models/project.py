from sqlalchemy_serializer import SerializerMixin
from data.sql.db_session import SqlAlchemyBase
import sqlalchemy, random


class Project(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'projects'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    icon = sqlalchemy.Column(sqlalchemy.Integer, default=random.randint(1, 4))
    admin_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    longitude = sqlalchemy.Column(sqlalchemy.Float)
    latitude = sqlalchemy.Column(sqlalchemy.Float)

    couriers = sqlalchemy.orm.relationship('User', secondary='courier_relations', backref='projects')
    invite_link = sqlalchemy.Column(sqlalchemy.String,
                                    default=''.join(['0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'[
                                                         random.randint(1, 61)] for i in range(11)]))

    def set_depot_coords(self, data):
        if isinstance(data, str):
            data = list(reversed(list(map(float, data.split(',')))))
            self.longitude = data[0]
            self.latitude = data[1]

        elif isinstance(data, tuple) or isinstance(data, list):
            self.longitude = data[0]
            self.latitude = data[1]

    def get_depot_coords(self):
        return self.longitude, self.latitude
