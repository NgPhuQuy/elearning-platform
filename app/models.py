import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Table,Enum,Text
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
    posts = relationship("Post",backref="author",lazy=True)
    comments = relationship("Comment",backref="author",lazy=True)

class PostCate(BaseModel):
    __tablename__ = "post_cate"

    description = Column(String(255),nullable=True)
    posts = relationship("Post", backref="category", lazy=True)

class Post(BaseModel):
    __tablename__ = "post"

    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    image = Column(String(500))
    view_count = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    category_id = Column(Integer,ForeignKey(PostCate.id),nullable=False)
    comments = relationship("Comment",backref="post",cascade="all, delete-orphan",lazy=True)
    reactions = relationship("ReactionPost",backref="post",cascade="all, delete-orphan",lazy=True)


class Comment(BaseModel):
    __tablename__ = "comment"

    content = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)
    post_id = Column(Integer,ForeignKey(Post.id),nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    parent_comment_id = Column(Integer,ForeignKey("comment.id"))
    replies = relationship("Comment", backref=backref("parent",remote_side="Comment.id"))
    reactions = relationship("ReactionComment",backref="comment",cascade="all, delete-orphan")

class VoteType(MyEnum):
    UP = 1
    DOWN = -1

class ReactionPost(db.Model):
    __tablename__ = "reaction_post"

    id = Column(Integer, primary_key=True)
    vote_type = Column(Enum(VoteType),nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    post_id = Column(Integer,ForeignKey(Post.id),nullable=False)
    created_date = Column(DateTime,default=datetime.now)

class ReactionComment(db.Model):
    __tablename__ = "reaction_comment"

    id = Column(Integer, primary_key=True)
    vote_type = Column(Enum(VoteType), nullable=False)
    user_id = Column(Integer,ForeignKey(User.id),nullable=False)
    comment_id = Column(Integer,ForeignKey(Comment.id),nullable=False)
    created_date = Column(DateTime,default=datetime.now)





if __name__ == '__main__':
    with app.app_context():
        # db.create_all()
        # db.session.commit()
        # password = hashlib.sha256(b'123').hexdigest()
        # admin = User(username = 'admin', password = password,first_name="",last_name="", email = '', phone='')
        # db.session.add(admin)
        # db.session.commit()

        categories = [PostCate(name="Python", description="Python Programming"),
            PostCate(name="Java", description="Java Programming"),
            PostCate(name="Spring Boot", description="Spring Framework"),
            PostCate(name="ReactJS", description="React Frontend"),
            PostCate(name="Database", description="MySQL & SQL Server"),
            PostCate(name="Machine Learning", description="AI & ML")]

        db.session.add_all(categories)
        db.session.commit()

