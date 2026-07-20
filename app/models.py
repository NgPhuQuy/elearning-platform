import hashlib
from datetime import datetime
from enum import Enum as MyEnum

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref

from app import db, app


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    created_date = Column(DateTime, default=datetime.now())
    updated_date = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    is_active = Column(Boolean, default=True)


class User(BaseModel, UserMixin):
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    avatar = Column(String(255), default='')
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(255), nullable=False)
    teacher_profile = relationship("Teacher", backref="user", uselist=False, lazy=True)


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False, unique=True)

    courses = relationship("Course", backref="teacher", lazy=True)


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


class PostCate(BaseModel):
    posts = relationship("Post", backref="category", lazy=True)


class Post(BaseModel):
    title = Column(String(255), nullable=False)
    content = Column(String(255), nullable=False)
    image = Column(String(500), default="")
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    category_id = Column(Integer, ForeignKey(PostCate.id), nullable=False)
    comments = relationship("Comment", backref="post", lazy=True)
    reactions = relationship("ReactionPost", backref="post", lazy=True)
    user = relationship("User", backref="posts")


class Comment(BaseModel):
    content = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    post_id = Column(Integer, ForeignKey(Post.id), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('comment.id'), nullable=True)
    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref=backref("parent_comment", remote_side="Comment.id"), lazy=True)
    reactions = relationship("ReactionComment", backref="comment", lazy=True)


class ReactionType(MyEnum):
    LIKE = "LIKE"
    LOVE = "LOVE"
    HAHA = "HAHA"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"


class ReactionPost(BaseModel):
    type = Column(Enum(ReactionType), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    post_id = Column(Integer, ForeignKey(Post.id), nullable=False)
    user = relationship("User", backref="reaction_posts")


class ReactionComment(BaseModel):
    type = Column(Enum(ReactionType), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    comment_id = Column(Integer, ForeignKey(Comment.id), nullable=False)
    user = relationship("User", backref="reaction_comments")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
        password = hashlib.sha256(b'123').hexdigest()
        admin = User(username='admin', password=password, first_name="", last_name="", email='', phone='')
        db.session.add(admin)
        #
        # teacher_user1 = User(username='teacher01', password=password,
        #                      first_name='Nguyen', last_name='An', email='an.teacher@gmail.com',
        #                      phone='0911111111')
        #
        # teacher_user2 = User(username='teacher02', password=password,
        #                      first_name='Tran', last_name='Binh', email='binh.teacher@gmail.com',
        #                      phone='0922222222')
        #
        # user1 = User(
        #     username='user01',
        #     password=password,
        #     first_name='Le',
        #     last_name='Nam',
        #     email='nam@gmail.com',
        #     phone='0933333333'
        # )
        #
        # user2 = User(
        #     username='user02',
        #     password=password,
        #     first_name='Pham',
        #     last_name='Hoa',
        #     email='hoa@gmail.com',
        #     phone='0944444444'
        # )
        #
        # db.session.add_all([user1, user2, teacher_user1, teacher_user2])
        # db.session.commit()
        #
        # teacher1 = Teacher(user_id=teacher_user1.id,
        #                    note="Giảng viên lập trình Python và Flask")
        #
        # teacher2 = Teacher(user_id=teacher_user2.id,
        #                    note="Giảng viên Java Spring Boot")
        #
        # db.session.add_all([teacher1, teacher2])
        #
        # db.session.commit()
        #
        # cate1 = PostCate(name="Công nghệ")
        #
        # cate2 = PostCate(name="Lập trình")
        #
        # cate3 = PostCate(name="Hỏi đáp")
        #
        # cate4 = PostCate(name="Chia sẻ kinh nghiệm")
        #
        # db.session.add_all([cate1, cate2, cate3, cate4])
        #
        # db.session.commit()
