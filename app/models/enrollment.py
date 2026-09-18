from datetime import datetime
from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app import db
from app.models import BaseModel


class EnrollmentStatus(MyEnum):
    IN_PROGRESS = "Đang học"
    COMPLETED = "Hoàn thành"
    FAILED = "Chưa đạt"


class Enrollment(BaseModel):
    progress = Column(Integer, default=0)
    price = Column(Integer, default=0)
    completed_date = Column(DateTime)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.IN_PROGRESS)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    lesson_progresses = relationship("LessonProgress", backref="enrollment", cascade="all, delete-orphan", lazy=True)
    scores = relationship("Score", backref="enrollment", cascade="all, delete-orphan", lazy=True)
