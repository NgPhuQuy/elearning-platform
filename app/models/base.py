from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app import db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)


class NamedModel(BaseModel):
    __abstract__ = True
    name = Column(String(255), nullable=True)

