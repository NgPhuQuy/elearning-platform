from datetime import datetime
from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app import db


class EnrollmentStatus(MyEnum):
    IN_PROGRESS = "Đang học"
    COMPLETED = "Hoàn thành"
    FAILED = "Chưa đạt"


class Enrollment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    progress = Column(Integer, default=0)
    price = Column(Integer, default=0)
    completed_date = Column(DateTime)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.IN_PROGRESS)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    lesson_progresses = relationship("LessonProgress", backref="enrollment", cascade="all, delete-orphan", lazy=True)
    scores = relationship("Score", backref="enrollment", cascade="all, delete-orphan", lazy=True)


class LessonProgress(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"))
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"))
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    last_watched_at = Column(DateTime)
    lesson = relationship("Lesson")

