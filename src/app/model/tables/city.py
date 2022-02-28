from sqlalchemy import Column, Integer, String

from app.db import Db


class City(Db.Base):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
