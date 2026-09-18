from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import db
from app.models.base import BaseModel


class Category(BaseModel):
    name = Column(String(100), nullable=False)
    course_category = relationship(
        "CourseCategory", backref="category", cascade="all, delete-orphan", lazy=True, overlaps="categories,courses"
    )
    courses = relationship(
        "Course",
        secondary="course_category",
        back_populates="categories",
        lazy=True,
        overlaps="course_category,category,course,courses",
    )


class CourseCategory(db.Model):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)


class CourseLevel(MyEnum):
    BASIC = "Cơ bản"
    INTERMEDIATE = "Trung cấp"
    ADVANCED = "Nâng cao"


class Course(BaseModel):
    name = Column(String(100), nullable=False)
    is_sale = Column(Boolean, default=True)
    price = Column(Integer, default=0)
    description = Column(Text)
    image = Column(String(255), default="")
    teacher_id = Column(Integer, ForeignKey("user.id"))
    chapters = relationship("Chapter", backref="course", cascade="all, delete-orphan", lazy="selectin")
    course_category = relationship(
        "CourseCategory", backref="course", cascade="all, delete-orphan", lazy=True, overlaps="categories,courses"
    )
    categories = relationship(
        "Category",
        secondary="course_category",
        back_populates="courses",
        lazy="selectin",
        overlaps="course_category,category,course,courses",
    )
    level = Column(Enum(CourseLevel), default=CourseLevel.BASIC)
    enrollments = relationship("Enrollment", backref="course", cascade="all, delete-orphan", lazy=True)
    tests = relationship("Test", backref="course", cascade="all, delete-orphan", lazy=True)


class Lesson(BaseModel):
    name = Column(String(100), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"))
    description = Column(String(255))
    file_url = Column(String(500))
    content = Column(Text)


class CourseOutcome(BaseModel):
    content = Column(String(255))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    course = relationship("Course", backref=backref("outcomes", cascade="all, delete-orphan"))


class Chapter(BaseModel):
    name = Column(String(100), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=1)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    lessons = relationship("Lesson", backref="chapter", cascade="all, delete-orphan", lazy="selectin")
    tests = relationship("Test", backref="chapter", cascade="all, delete-orphan", lazy="selectin")


class LessonProgress(BaseModel):
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"))
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"))
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    last_watched_at = Column(DateTime)
    lesson = relationship("Lesson")
