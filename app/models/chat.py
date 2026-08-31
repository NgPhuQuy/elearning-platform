from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app import db
from app.models.base import BaseModel


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
