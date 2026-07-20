from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app import db
from models.base import BaseModel


class Category(BaseModel):
    course_category = relationship("CourseCategory", backref="category", lazy=True)


class CourseCategory(db.Model):
    course_id = Column(Integer, ForeignKey('course.id', ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), primary_key=True)


class Course(BaseModel):
    description = Column(String(255), nullable=False)
    image = Column(String(500), default="")
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=False)

    lessons = relationship("Lesson", backref="course", lazy=True)
    course_category = relationship("CourseCategory", backref="course", cascade="all, delete-orphan", lazy=True)


class Lesson(BaseModel):
    description = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), primary_key=True)