from data.db_session import SqlAlchemyBase
import sqlalchemy
import datetime


class Orders(SqlAlchemyBase):
    __tablename__ = 'orders'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    address = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('users.id'))
    city = sqlalchemy.Column(sqlalchemy.String)
    goods = sqlalchemy.Column(sqlalchemy.String)
    start_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    # scheduled_date = sqlalchemy.Column(sqlalchemy.DateTime)
    scheduled_date = sqlalchemy.Column(sqlalchemy.String, default='-')
    is_delivered = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
