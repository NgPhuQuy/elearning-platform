from enum import Enum as MyEnum

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ROLE(MyEnum):
    ADMIN = "Admin"
    USER = "User"


class User(BaseModel, UserMixin):
    username = Column(String(255), unique=True)
    password = Column(String(255))
    google_sub = Column(String(255), unique=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    avatar = Column(String(255), default="")
    email = Column(String(255), unique=True)
    phone = Column(String(255))
    role = Column(Enum(ROLE), default=ROLE.USER)
    bio = Column(String(255), default="")
    enrollments = relationship("Enrollment", backref="user", lazy=True)
    courses = relationship("Course", backref="user", lazy=True)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or (self.username or "")


class ApplicationStatus(MyEnum):
    PENDING = "Chờ duyệt"
    APPROVED = "Đã duyệt"
    REJECTED = "Từ chối"


class TeacherApplication(BaseModel):
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
