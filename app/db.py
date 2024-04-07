from sqlmodel import Session, SQLModel, create_engine

from app.settings import settings

engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG_MODE)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
