from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String

from app.db import Db


class User(Db.Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    other_name = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    birthday = Column(Date)
    city = Column(Integer, ForeignKey('city.id'), index=True)
    additional_info = Column(String)
    is_admin = Column(Boolean)
    password_hash = Column(String)
