import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Table,Enum
from sqlalchemy.orm import relationship,backref
from enum import Enum as MyEnum
from app import db, app


class BaseModel(db.Model):
    __abstract__ = True
    id =Column(Integer, primary_key=True)
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

class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    note = Column(String(255), default="")
    courses = relationship("Course", backref="teacher", lazy=True)
    user = relationship("User", backref="teacher")
class PostCate(BaseModel):
    posts = relationship("Post", backref="category", lazy=True)

class Post(BaseModel):
    title = Column(String(255), nullable=False)
    content = Column(String(255), nullable=False)
    teacher_id = Column(Integer,ForeignKey(Teacher.id),nullable=False)
    category_id = Column(Integer,ForeignKey(PostCate.id),nullable=False)
    comments = relationship("Comment",backref="post",lazy=True)
    reactions = relationship("ReactionPost",backref="post",lazy=True)

class Comment(BaseModel):
    content = Column(String(255), nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    post_id = Column(Integer,ForeignKey(Post.id),nullable=False)
    parent_comment_id = Column(Integer,ForeignKey('comment.id'),nullable=True)
    user = relationship("User")
    replies = relationship("Comment",backref=backref("parent_comment",remote_side="Comment.id"),lazy=True)
    reactions = relationship("ReactionComment",backref="comment",lazy=True)

class ReactionType(MyEnum):
    LIKE = "LIKE"
    LOVE = "LOVE"
    HAHA = "HAHA"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"

class ReactionPost(BaseModel):
    type = Column(Enum(ReactionType),nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    post_id = Column(Integer,ForeignKey(Post.id), nullable=False)
    user = relationship("User")

class ReactionComment(BaseModel):
    type = Column(Enum(ReactionType),nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    comment_id = Column(Integer, ForeignKey(Comment.id),nullable=False)
    user = relationship("User")



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
        # password = hashlib.sha256(b'123').hexdigest()
        # admin = User(username = 'admin', password = password,first_name="",last_name="", email = '', phone='')
        # db.session.add(admin)
        # db.session.commit()