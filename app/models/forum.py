from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref
from app import db
from models.base import BaseModel
from models.user import User


class PostCate(BaseModel):
    posts = relationship("Post", backref="category", lazy=True)


class Post(BaseModel):
    title = Column(String(255), nullable=False)
    content = Column(String(255), nullable=False)
    image = Column(String(500), default="")
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('post_cate.id'), nullable=False)

    # Mối quan hệ
    comments = relationship("Comment", backref="post", lazy=True)
    reactions = relationship("ReactionPost", backref="post", lazy=True)
    user = relationship("User", backref="posts")


class Comment(BaseModel):
    content = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('comment.id'), nullable=True)

    # Mối quan hệ
    user = relationship("User", backref="comments")
    replies = relationship("Comment", backref=backref("parent_comment", remote_side="Comment.id"), lazy=True)
    reactions = relationship("ReactionComment", backref="comment", lazy=True)


class ReactionPost(BaseModel):
    type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user = relationship("User", backref="reaction_posts")


class ReactionComment(BaseModel):
    type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=False)
    user = relationship("User", backref="reaction_comments")