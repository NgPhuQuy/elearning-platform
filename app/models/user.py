from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from models.base import BaseModel


class User(BaseModel, UserMixin):
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    avatar = Column(String(255), default='')
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(255), nullable=False)

    teacher_profile = relationship("Teacher", backref="user", uselist=False, lazy=True)


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False, unique=True)

    courses = relationship("Course", backref="teacher", lazy=True)