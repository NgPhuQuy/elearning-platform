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

    @property
    def activate(self):
        return self.is_active

    @activate.setter
    def activate(self, val):
        self.is_active = bool(val)


class LessonType(MyEnum):
    VIDEO = "Video"
    NONE = "Chưa chọn"
    DOCUMENT = "Doc"


class VideoContent:
    def __init__(self, lesson_id=None, video_url="", duration=0):
        self.lesson_id = lesson_id
        self.video_url = video_url
        self.duration = duration


class DocContent:
    def __init__(self, lesson_id=None, content_text="", file_url="", file_ext=""):
        self.lesson_id = lesson_id
        self.content_text = content_text
        self.file_url = file_url
        self.file_ext = file_ext


class Lesson(BaseModel):
    name = Column(String(100), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"))
    description = Column(String(255))
    file_url = Column(String(500))
    content = Column(Text)

    def __init__(self, **kwargs):
        video_content = kwargs.pop("video_content", None)
        doc_content = kwargs.pop("doc_content", None)
        les_type = kwargs.pop("type", None)
        super().__init__(**kwargs)
        if les_type is not None:
            self._type = les_type
        if video_content is not None:
            self.file_url = getattr(video_content, "video_url", str(video_content))
            self._type = LessonType.VIDEO
        elif doc_content is not None:
            self.file_url = getattr(doc_content, "file_url", "")
            self.content = getattr(doc_content, "content_text", str(doc_content))
            self._type = LessonType.DOCUMENT

    @property
    def type(self):
        return getattr(
            self,
            "_type",
            LessonType.VIDEO if self.file_url else (LessonType.DOCUMENT if self.content else LessonType.NONE),
        )

    @type.setter
    def type(self, val):
        self._type = val

    @property
    def video_content(self):
        if self.file_url:
            return VideoContent(lesson_id=self.id, video_url=self.file_url)
        return None

    @video_content.setter
    def video_content(self, val):
        if val is not None:
            self.file_url = getattr(val, "video_url", str(val))
            self._type = LessonType.VIDEO

    @property
    def doc_content(self):
        if self.content or self.file_url:
            return DocContent(lesson_id=self.id, content_text=self.content or "", file_url=self.file_url or "")
        return None

    @doc_content.setter
    def doc_content(self, val):
        if val is not None:
            self.content = getattr(val, "content_text", str(val))
            if hasattr(val, "file_url") and val.file_url:
                self.file_url = val.file_url
            self._type = LessonType.DOCUMENT


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
