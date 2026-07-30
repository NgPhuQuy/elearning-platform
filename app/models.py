import hashlib
from datetime import datetime
from enum import Enum as MyEnum

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import app, db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_date = Column(DateTime, default=datetime.now())
    updated_date = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)


class User(BaseModel, UserMixin):
    username = Column(String(255), unique=True)
    password = Column(String(255))
    google_sub = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    avatar = Column(String(255), default="")
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(255))
    teacher_profile = relationship("Teacher", backref="user", uselist=False, lazy=True)
    bio = Column(String(255), default="")
    enrollment = relationship("Enrollment", backref="user", lazy=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    note = Column(String(255), default="")
    courses = relationship(
        "Course",
        backref="teacher",
        lazy=True,
    )


class Chapter(BaseModel):
    description = Column(Text)

    order = Column(Integer, default=1)

    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)

    lessons = relationship("Lesson", backref="chapter", cascade="all, delete-orphan", lazy=True)


class Category(BaseModel):
    course_category = relationship("CourseCategory", backref="category", lazy=True)


class CourseCategory(db.Model):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"), primary_key=True)


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

    chapters = relationship("Chapter", backref="course", cascade="all, delete-orphan", lazy=True)
    course_category = relationship("CourseCategory", backref="course", cascade="all, delete-orphan", lazy=True)
    level = Column(Enum(CourseLevel), nullable=False, default=CourseLevel.BASIC)
    enrollment = relationship("Enrollment", backref="course", cascade="all, delete-orphan", lazy=True)


class LessonType(MyEnum):
    VIDEO = "Video"
    NONE = "Chưa chọn"
    DOCUMENT = "Doc"


class VideoContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id"), primary_key=True)
    video_url = Column(String(500), nullable=False)
    duration = Column(Integer, default=0)


class DocContent(db.Model):
    lesson_id = Column(Integer, ForeignKey("lesson.id"), primary_key=True)
    content_text = Column(Text)
    file_url = Column(String(500))
    file_ext = Column(String(20))


class Lesson(BaseModel):
    type = Column(Enum(LessonType), nullable=False, default=LessonType.NONE)
    chapter_id = Column(Integer, ForeignKey("chapter.id"), nullable=False)
    description = Column(String(255), nullable=False)
    video_content = relationship("VideoContent", backref="lesson", uselist=False, cascade="all, delete-orphan")
    doc_content = relationship("DocContent", backref="lesson", uselist=False, cascade="all, delete-orphan")


class CourseOutcome(BaseModel):
    content = Column(String(255), nullable=False)

    course_id = Column(Integer, ForeignKey("course.id"), nullable=False)

    course = relationship("Course", backref="outcomes")


class EnrollmentStatus(MyEnum):
    IN_PROGRESS = "Đang học"
    COMPLETED = "Hoàn thành"
    FAILED = "Chưa đạt"


class Enrollment(db.Model):
    progress = Column(Integer, default=0)
    price = Column(Integer, nullable=False, default=0)
    completed_date = Column(DateTime)
    status = Column(Enum(EnrollmentStatus), nullable=False, default=EnrollmentStatus.IN_PROGRESS)
    created_date = Column(DateTime, nullable=False, default=datetime.now(), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, primary_key=True)


class PostCate(BaseModel):
    description = Column(String(255), nullable=True)
    posts = relationship("Post", secondary="post_category", back_populates="categories", lazy=True)


class Post(BaseModel):
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image = Column(String(500), default="")
    view_count = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    categories = relationship("PostCate", secondary="post_category", back_populates="posts", lazy=True)
    comments = relationship("Comment", backref="post", cascade="all, delete-orphan", lazy=True)
    reactions = relationship("ReactionPost", backref="post", cascade="all, delete-orphan", lazy=True)
    user = relationship("User", backref="posts")


class PostCategory(db.Model):
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("post_cate.id", ondelete="CASCADE"), primary_key=True)


class Comment(BaseModel):
    content = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)
    post_id = Column(Integer, ForeignKey(Post.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comment.id"))
    replies = relationship("Comment", backref=backref("parent", remote_side="Comment.id"))
    reactions = relationship("ReactionComment", backref="comment", cascade="all, delete-orphan")
    user = relationship("User", backref="comments")


class VoteType(MyEnum):
    UP = 1
    DOWN = -1


class ReactionPost(db.Model):
    id = Column(Integer, primary_key=True)
    vote_type = Column(Enum(VoteType), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    post_id = Column(Integer, ForeignKey(Post.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)


class ReactionComment(db.Model):
    id = Column(Integer, primary_key=True)
    vote_type = Column(Enum(VoteType), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    comment_id = Column(Integer, ForeignKey(Comment.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)


class ApplicationStatus(MyEnum):
    PENDING = "Chờ duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


class TeacherApplication(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

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


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.commit()
        password = hashlib.sha256(b"11111111").hexdigest()
        admin = User(
            username="admin", password=password, first_name="Nguyen Tran Ad", last_name="Min", email="", phone=""
        )
        db.session.add(admin)

        teacher_user1 = User(
            username="teacher01",
            password=password,
            first_name="Nguyen",
            last_name="An",
            email="an.teacher@gmail.com",
            phone="0911111111",
        )

        teacher_user2 = User(
            username="teacher02",
            password=password,
            first_name="Tran",
            last_name="Binh",
            email="binh.teacher@gmail.com",
            phone="0922222222",
        )

        user1 = User(
            username="user01",
            password=password,
            first_name="Le",
            last_name="Nam",
            email="nam@gmail.com",
            phone="0933333333",
        )

        user2 = User(
            username="user02",
            password=password,
            first_name="Pham",
            last_name="Hoa",
            email="hoa@gmail.com",
            phone="0944444444",
        )

        db.session.add_all([user1, user2, teacher_user1, teacher_user2])
        db.session.commit()

        teacher1 = Teacher(user_id=teacher_user1.id, note="Giảng viên lập trình Python và Flask")

        teacher2 = Teacher(user_id=teacher_user2.id, note="Giảng viên Java Spring Boot")

        db.session.add_all([teacher1, teacher2])
        db.session.commit()

        cate1 = PostCate(name="Công nghệ")
        cate2 = PostCate(name="Lập trình")
        cate3 = PostCate(name="Hỏi đáp")
        cate4 = PostCate(name="Chia sẻ kinh nghiệm")

        db.session.add_all([cate1, cate2, cate3, cate4])
        cate1 = Category(name="Lập trình")
        cate2 = Category(name="Thiết kế")
        cate3 = Category(name="Marketing")
        cate4 = Category(name="Kinh doanh")
        cate5 = Category(name="Ngoại ngữ")
        cate6 = Category(name="Data Science")
        cate7 = Category(name="Trí tuệ nhân tạo")
        cate8 = Category(name="An ninh mạng")
        cate9 = Category(name="Phát triển Web")
        cate10 = Category(name="Phát triển Mobile")

        db.session.add_all([cate1, cate2, cate3, cate4, cate5, cate6, cate7, cate8, cate9, cate10])

        db.session.commit()
