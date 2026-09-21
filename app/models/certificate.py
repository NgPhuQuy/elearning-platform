from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship

from app.models.base import BaseModel


class Certificate(BaseModel):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"), unique=True, nullable=False)
    issued_date = Column(DateTime, default=datetime.now)

    course = relationship("Course", backref="certificates")
    enrollment = relationship("Enrollment", backref=backref("certificate", uselist=False))
