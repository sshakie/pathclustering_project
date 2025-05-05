from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import create_engine

SqlAlchemyBase = declarative_base()
__factory = None


def global_init(db_file):
    global __factory
    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception('Необходимо указать файл базы данных.')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = create_engine(conn_str, echo=False)
    __factory = sessionmaker(bind=engine)

    from data.sql.__all_models import User, Order, UserRelations, Project, CourierRelations
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
