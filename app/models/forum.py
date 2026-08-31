from datetime import datetime
from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import backref, relationship

from app import db
from app.models.base import BaseModel


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

