from datetime import datetime
from enum import Enum as MyEnum

from flask_login import UserMixin
from sqlalchemy import DECIMAL, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import db


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
    email = Column(String(255), unique=True)
    phone = Column(String(255))
    teacher_profile = relationship("Teacher", backref="user", uselist=False, lazy=True)
    bio = Column(String(255), default="")
    enrollments = relationship("Enrollment", backref="user", lazy=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Admin(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    admin = relationship("User", backref="admin", uselist=False, lazy=True)
    note = Column(String(255), default="")


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    note = Column(String(255), default="")
    courses = relationship("Course", backref="teacher", lazy=True)


class Conversation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    title = Column(String(255))
    image = Column(String(500), default="")
    is_group = Column(Boolean, default=False)
    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan", lazy=True)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy=True)


class ConversationMember(db.Model):
    conversation_id = Column(Integer, ForeignKey("conversation.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    joined_date = Column(DateTime, default=datetime.now)
    last_read = Column(DateTime)
    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User", backref="conversation_members")


class Message(BaseModel):
    content = Column(Text)
    attachment = Column(String(500))
    is_edited = Column(Boolean, default=False)
    conversation_id = Column(Integer, ForeignKey("conversation.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", backref="messages")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan", lazy=True)


class MessageReaction(BaseModel):
    emoji = Column(String(20))
    message_id = Column(Integer, ForeignKey("message.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    message = relationship("Message", back_populates="reactions")
    user = relationship("User", backref="message_reactions")


class Chapter(BaseModel):
    description = Column(Text)
    order = Column(Integer, default=1)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
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
    price = Column(Integer, default=0)
    activate = Column(Boolean, default=False)
    description = Column(String(1000))
    image = Column(String(500), default="")
    teacher_id = Column(Integer, ForeignKey("teacher.id"))
    chapters = relationship("Chapter", backref="course", cascade="all, delete-orphan", lazy="selectin")
    course_category = relationship("CourseCategory", backref="course", cascade="all, delete-orphan", lazy=True)
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


class Test(BaseModel):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"))
    duration = Column(Integer, default=0)
    max_attempts = Column(Integer, default=1)
    questions = relationship("Question", backref="test", cascade="all, delete-orphan", lazy="selectin")
    scores = relationship("Score", backref="test", cascade="all, delete-orphan", lazy=True)


class Question(BaseModel):
    test_id = Column(Integer, ForeignKey("test.id", ondelete="CASCADE"))
    content = Column(Text)
    answers = relationship("Answer", backref="question", cascade="all, delete-orphan", lazy="selectin")


class Answer(BaseModel):
    question_id = Column(Integer, ForeignKey("question.id", ondelete="CASCADE"))
    content = Column(String(500))
    is_correct = Column(Boolean, default=False)


class Score(db.Model):
    id = Column(Integer, primary_key=True)
    enrollment_id = Column(Integer, ForeignKey("enrollment.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("test.id", ondelete="CASCADE"))
    attempt_number = Column(Integer, default=1)
    score_value = Column(DECIMAL(10, 2))
    is_passed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    __table_args__ = (db.UniqueConstraint("enrollment_id", "test_id", "attempt_number", name="uix_score_per_attempt"),)


class PostCate(BaseModel):
    description = Column(String(255))
    posts = relationship("Post", secondary="post_category", back_populates="categories", lazy="selectin")


class Post(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    title = Column(String(255))
    content = Column(Text)
    image = Column(String(500), default="")
    view_count = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    categories = relationship("PostCate", secondary="post_category", back_populates="posts", lazy="selectin")
    comments = relationship("Comment", backref="post", cascade="all, delete-orphan", lazy="selectin")
    reactions = relationship("ReactionPost", backref="post", cascade="all, delete-orphan", lazy="selectin")
    user = relationship("User", backref="posts")


class PostCategory(db.Model):
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("post_cate.id", ondelete="CASCADE"), primary_key=True)


class Comment(BaseModel):
    content = Column(Text)
    is_accepted = Column(Boolean, default=False)
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
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
    vote_type = Column(Enum(VoteType))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    created_date = Column(DateTime, default=datetime.now)


class ReactionPost(Reactable):
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uix_vote_per_user_post"),)


class ReactionComment(Reactable):
    comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"))
    __table_args__ = (db.UniqueConstraint("user_id", "comment_id", name="uix_vote_per_user_comment"),)


class ApplicationStatus(MyEnum):
    PENDING = "Chờ duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


class TeacherApplication(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    workplace = Column(String(255))
    degree = Column(String(50))
    major = Column(String(255))
    bio = Column(String(500))
    expertise = Column(String(500))
    experience = Column(String(50))
    teach_style = Column(String(20))
    linkedin = Column(String(255))
    website = Column(String(255))
    id_card_file = Column(String(500))
    degree_file = Column(String(500))
    cv_file = Column(String(500))
    extra_cert_file = Column(String(500))
    video_file = Column(String(500))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
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


class Payment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now)
    updated_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    order_id = Column(String(50), unique=True)
    request_id = Column(String(50))
    momo_trans_id = Column(String(50))
    amount = Column(Integer)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    pay_type = Column(String(50))
    paid_at = Column(DateTime)
    invoice_sent = Column(Boolean, default=False)
    user = relationship("User", backref="payments")
    course = relationship("Course", backref="payments")