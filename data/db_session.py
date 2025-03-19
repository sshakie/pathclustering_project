import sqlalchemy
from sqlalchemy.orm import *

SqlAlchemyBase = declarative_base()
factory = None


def global_init(db_file):
    global factory
    if factory:
        return

    if not db_file or not db_file.strip():
        raise Exception('Необходимо указать файл базы данных.')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sqlalchemy.create_engine(conn_str, echo=False)
    factory = sessionmaker(bind=engine)

    from data.all_modules import User, Orders
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global factory
    return factory()
