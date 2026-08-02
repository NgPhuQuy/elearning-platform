import hashlib
from datetime import datetime
from enum import Enum as MyEnum

from flask_login import UserMixin
from sqlalchemy import DECIMAL, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import app, db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)


class User(BaseModel, UserMixin):
    username = Column(String(255), unique=True)
    password = Column(String(255))
    google_sub = Column(String(255), unique=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    avatar = Column(String(255), default="")
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(255))
    teacher_profile = relationship("Teacher", backref="user", uselist=False, lazy=True)
    bio = Column(String(255), default="")
    enrollments = relationship("Enrollment", backref="user", lazy=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Admin(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    admin = relationship("User", backref="admin", uselist=False, lazy=True)
    note = Column(String(255), default="")


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    note = Column(String(255), default="")
    courses = relationship(
        "Course",
        backref="teacher",
        lazy=True,
    )


class Chapter(BaseModel):
    description = Column(Text)
    order = Column(Integer, default=1)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    lessons = relationship("Lesson", backref="chapter", cascade="all, delete-orphan", lazy="selectin")
    tests = relationship("Test", backref="chapter", cascade="all, delete-orphan", lazy="selectin")


class Category(BaseModel):
    course_category = relationship("CourseCategory", backref="category", lazy=True)


class CourseCategory(db.Model):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)


class CourseLevel(MyEnum):
    BASIC = "Cơ bản"
    INTERMEDIATE = "Trung cấp"
    ADVANCED = "Nâng cao"


class Course(BaseModel):
    is_sale = Column(Boolean, default=True)
    price = Column(Integer, nullable=False, default=0)
    activate = Column(Boolean, nullable=False, default=False)
    description = Column(String(1000), nullable=False)
    image = Column(String(500), nullable=False, default="")
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=False)
    chapters = relationship("Chapter", backref="course", cascade="all, delete-orphan", lazy="selectin")
    course_category = relationship("CourseCategory", backref="course", cascade="all, delete-orphan", lazy=True)
    level = Column(Enum(CourseLevel), nullable=False, default=CourseLevel.BASIC)
    enrollment = relationship("Enrollment", backref="course", cascade="all, delete-orphan", lazy=True)
    tests = relationship("Test", backref="course", cascade="all, delete-orphan", lazy=True)


class LessonType(MyEnum):
    VIDEO = "Video"
    NONE = "Chưa chọn"
    DOCUMENT = "Doc"


class VideoContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"), primary_key=True)
    video_url = Column(String(500), nullable=False)
    duration = Column(Integer, default=0)


class DocContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"), primary_key=True)
    content_text = Column(Text)
    file_url = Column(String(500))
    file_ext = Column(String(20))


class Lesson(BaseModel):
    type = Column(Enum(LessonType), nullable=False, default=LessonType.NONE)
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
    video_content = relationship("VideoContent", backref="lesson", uselist=False, cascade="all, delete-orphan")
    doc_content = relationship("DocContent", backref="lesson", uselist=False, cascade="all, delete-orphan")


class CourseOutcome(BaseModel):
    content = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    course = relationship("Course", backref=backref("outcomes", cascade="all, delete-orphan"))


class EnrollmentStatus(MyEnum):
    IN_PROGRESS = "Đang học"
    COMPLETED = "Hoàn thành"
    FAILED = "Chưa đạt"


class Enrollment(BaseModel):
    progress = Column(Integer, default=0)
    price = Column(Integer, nullable=False, default=0)
    completed_date = Column(DateTime)
    status = Column(Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.IN_PROGRESS)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)

    lesson_progresses = relationship("LessonProgress", backref="enrollment", cascade="all, delete-orphan", lazy=True)
    scores = relationship("Score", backref="enrollment", cascade="all, delete-orphan", lazy=True)


class LessonProgress(BaseModel):
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lesson.id", ondelete="CASCADE"), nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    last_watched_at = Column(DateTime, nullable=True)

    lesson = relationship("Lesson")

    __table_args__ = (
        db.UniqueConstraint("enrollment_id", "lesson_id", name="uix_progress_per_enrollment_lesson"),
    )


class Test(BaseModel):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"), nullable=True)
    duration = Column(Integer, default=0)
    max_attempts = Column(Integer, default=1)

    questions = relationship("Question", backref="test", cascade="all, delete-orphan", lazy="selectin")
    scores = relationship("Score", backref="test", cascade="all, delete-orphan", lazy=True)


class Question(BaseModel):
    test_id = Column(Integer, ForeignKey("test.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    answers = relationship("Answer", backref="question", cascade="all, delete-orphan", lazy="selectin")


class Answer(BaseModel):
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(500), nullable=False)
    is_correct = Column(Boolean, default=False)


class Score(db.Model):
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(Integer, ForeignKey("test.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1)
    score_value = Column(DECIMAL(10,2), nullable=False)
    is_passed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)

    __table_args__ = (
        db.UniqueConstraint(
            "enrollment_id", "test_id", "attempt_number", name="uix_score_per_attempt"
        ),
    )


class PostCate(BaseModel):
    description = Column(String(255), nullable=True)
    posts = relationship("Post", secondary="post_category", back_populates="categories", lazy="selectin")


class Post(BaseModel):
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image = Column(String(500), default="")
    view_count = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    categories = relationship("PostCate", secondary="post_category", back_populates="posts", lazy="selectin")
    comments = relationship("Comment", backref="post", cascade="all, delete-orphan", lazy="selectin")
    reactions = relationship("ReactionPost", backref="post", cascade="all, delete-orphan", lazy="selectin")
    user = relationship("User", backref="posts")


class PostCategory(db.Model):
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("post_cate.id", ondelete="CASCADE"), primary_key=True)


class Comment(BaseModel):
    content = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"))
    replies = relationship("Comment", backref=backref("parent", remote_side="Comment.id"))
    reactions = relationship("ReactionComment", backref="comment", cascade="all, delete-orphan", lazy="selectin")
    user = relationship("User", backref="comments")


class VoteType(MyEnum):
    UP = 1
    DOWN = -1


class Reactable(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    vote_type = Column(Enum(VoteType), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)


class ReactionPost(Reactable):
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), nullable=False)


class ReactionComment(Reactable):
    comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), nullable=False)


class ApplicationStatus(MyEnum):
    PENDING = "Chờ duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


class TeacherApplication(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)

    # Bước 1: thông tin cá nhân
    workplace = Column(String(255))
    degree = Column(String(50))
    major = Column(String(255), nullable=False)
    bio = Column(String(500), nullable=False)

    # Bước 2: hồ sơ chuyên môn
    expertise = Column(String(500))
    experience = Column(String(50))
    teach_style = Column(String(20))
    linkedin = Column(String(255))
    website = Column(String(255))

    # Bước 3: tài liệu xác minh
    id_card_file = Column(String(500), nullable=False)
    degree_file = Column(String(500), nullable=False)
    cv_file = Column(String(500), nullable=False)
    extra_cert_file = Column(String(500))
    video_file = Column(String(500))

    # Duyệt
    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.PENDING)
    reject_reason = Column(String(500))
    reviewed_by = Column(Integer, ForeignKey("user.id"))
    reviewed_at = Column(DateTime)

    user = relationship("User", foreign_keys="TeacherApplication.user_id", backref="teacher_applications")
    reviewer = relationship("User", foreign_keys="TeacherApplication.reviewed_by")


class PaymentStatus(MyEnum):
    PENDING = "Chờ thanh toán"
    SUCCESS = "Đã thanh toán"
    FAILED = "Thất bại"
    CANCELLED = "Đã hủy"


class Payment(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)

    order_id = Column(String(50), unique=True, nullable=False)
    request_id = Column(String(50), nullable=False)
    momo_trans_id = Column(String(50))

    amount = Column(Integer, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    pay_type = Column(String(50))
    paid_at = Column(DateTime)
    invoice_sent = Column(Boolean, default=False)

    user = relationship("User", backref="payments")
    course = relationship("Course", backref="payments")
