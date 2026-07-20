from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app import db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
