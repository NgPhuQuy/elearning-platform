from datetime import datetime
from enum import Enum as MyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app import db


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
