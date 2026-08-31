from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import db
from app.models.base import BaseModel


class Category(BaseModel):
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
    is_sale = Column(Boolean, default=True)
    price = Column(Integer, default=0)
    activate = Column(Boolean, default=False)
    description = Column(String(1000))
    image = Column(String(500), default="")
    teacher_id = Column(Integer, ForeignKey("teacher.id"))
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


class LessonType(MyEnum):
    VIDEO = "Video"
    NONE = "Chưa chọn"
    DOCUMENT = "Doc"


class VideoContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"), primary_key=True)
    video_url = Column(String(500))
    duration = Column(Integer, default=0)


class DocContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"), primary_key=True)
    content_text = Column(Text)
    file_url = Column(String(500))
    file_ext = Column(String(20))


class Lesson(BaseModel):
    type = Column(Enum(LessonType), default=LessonType.NONE)
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"))
    description = Column(String(255))
    video_content = relationship("VideoContent", backref="lesson", uselist=False, cascade="all, delete-orphan")
    doc_content = relationship("DocContent", backref="lesson", uselist=False, cascade="all, delete-orphan")


class CourseOutcome(BaseModel):
    content = Column(String(255))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    course = relationship("Course", backref=backref("outcomes", cascade="all, delete-orphan"))


class Chapter(BaseModel):
    description = Column(Text)
    order = Column(Integer, default=1)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    lessons = relationship("Lesson", backref="chapter", cascade="all, delete-orphan", lazy="selectin")
    tests = relationship("Test", backref="chapter", cascade="all, delete-orphan", lazy="selectin")
