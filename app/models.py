import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

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
    teach =relationship("Teacher", backref="user", lazy=True)


class Teacher(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id'), unique=True, nullable=False)
    note = Column(String(255), default="")
    courses = relationship("Course", backref="teacher", lazy=True)



class Category(BaseModel):
    course_category = relationship("CourseCategory", backref="category",   lazy=True)
class CourseCategory(db.Model):
    __tablename__ = "course_category"
    course_id = Column(Integer, ForeignKey('course.id',ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), primary_key=True)

class Course(BaseModel):
    description = Column(String(255), nullable=False)
    image = Column(String(500), default="")
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=False)
    lessons = relationship("Lesson", backref="course", lazy = True)
    course_category = relationship("CourseCategory", backref="course",cascade="all, delete-orphan", lazy=True)

class Lesson(BaseModel):
    description = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), primary_key=True)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
        password = hashlib.sha256(b'123').hexdigest()
        teacher = User(username='teacher', password=password,first_name="Emifukada", last_name="", email='jfafhaf@gmail.com', phone='')
        teacher_profile = Teacher(
            user=teacher,
            note="Giáo viên dạy tiếng nhật"
        )

        admin = User(username = 'admin', password = password,first_name="",last_name="", email = '', phone='')
        db.session.add(teacher)
        db.session.add(teacher_profile)
        db.session.add(admin)
        categories = [
            Category(name="Lập trình Python"),
            Category(name="Lập trình Java"),
            Category(name="Lập trình Web"),
            Category(name="Cơ sở dữ liệu"),
            Category(name="Trí tuệ nhân tạo"),
            Category(name="Machine Learning"),
            Category(name="Tiếng Anh"),
            Category(name="Tiếng Nhật"),
            Category(name="Thiết kế UI/UX"),
            Category(name="Marketing")
        ]

        db.session.add_all(categories)
        db.session.commit()