from datetime import datetime

from sqlalchemy import DECIMAL, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app import db
from app.models.base import BaseModel


class Test(BaseModel):
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
    chapter_id = Column(Integer, ForeignKey("chapter.id", ondelete="CASCADE"), nullable=True)
    duration = Column(Integer, default=0)
    max_attempts = Column(Integer, default=1)
    questions = relationship("Question", backref="test", cascade="all, delete-orphan", lazy="selectin")
    scores = relationship("Score", backref="test", cascade="all, delete-orphan", lazy=True)
    pass_score = Column(DECIMAL(10, 2), default=5)


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
