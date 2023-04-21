from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

import pickle
import urllib.parse

from .settings import MARIADB_USER, MARIADB_PASSWORD


class Base(DeclarativeBase):
    pass


class Demotivator(Base):
    __tablename__ = "demotivators"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(50))
    is_temp: Mapped[bool] = mapped_column(default=True)
    is_private: Mapped[bool] = mapped_column(default=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    friends: Mapped[bytes] = mapped_column(default=pickle.dumps(list()))
    created_count: Mapped[int] = mapped_column(default=0)
    state: Mapped[int] = mapped_column(default=0)
    create_mode: Mapped[int] = mapped_column(default=0)


engine = create_engine(
    f"mysql+pymysql://{MARIADB_USER}:{urllib.parse.quote_plus(MARIADB_PASSWORD)}@localhost/demiurge", echo=True)
if not database_exists(engine.url):
    create_database(engine.url)

Base.metadata.create_all(engine)