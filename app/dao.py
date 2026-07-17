import hashlib

from flask_login import current_user

from app.models import User, Course, Lesson, Category, CourseCategory, Post,Comment,ReactionPost,ReactionComment,PostCate
from app import db, login
import cloudinary.uploader
@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def register_user(username, password, email,
                  phone, avatar, first_name, last_name):
    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password, email=email,phone=phone,
                avatar=avatar, first_name=first_name, last_name=last_name)
    db.session.add(user)
    db.session.commit()
    return user

def is_username_exist(username):
    return User.query.filter(User.username == username).first()


def is_email_used(email):
    return User.query.filter(User.email == email).first()


def is_phone_used(phone):
    return User.query.filter(User.phone == phone).first()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def change_info(email, phone, file_path, first_name, last_name):
    if email != current_user.email:

        if is_email_used(email):
            return False, "Email đã được sử dụng bởi tài khoản khác."

    current_user.email = email
    current_user.phone = phone
    current_user.avatar = file_path
    current_user.first_name = first_name
    current_user.last_name = last_name
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None


def change_password(new_password):
    current_user.password = hash_password(new_password)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None

def get_categories():
    return Category.query.all()


def create_course(  name, description , image,teacher_id , category_ids):
    course = Course(name=name, description=description, image=image, teacher_id=teacher_id)



    try:
        db.session.add(course)
        db.session.commit()
        if category_ids and isinstance(category_ids, list):
            for cate_id in category_ids:
                course_category = CourseCategory(
                    course_id=course.id,
                    category_id=cate_id
                )
                db.session.add(course_category)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return None

    return course

def get_course_details(course_id, teacher_id):
    return Course.query.filter(
        Course.id == course_id,
        Course.teacher_id == teacher_id
    ).first()


def get_courses_by_teacher_id(teacher_id):
    return Course.query.filter_by(
        teacher_id=teacher_id
    ).all()
def update_course (course_id, teacher_id, name=None, description=None, image=None, category_ids=None):
    course = Course.query.filter(Course.id == course_id, Course.teacher_id == teacher_id).first()
    if course:
        if  name:
            course.name = name
        if  description:
            course.description = description
        if image:
            course.image = image
        if category_ids is not None:
            CourseCategory.query.filter_by(course_id=course.id).delete()
            for cate_id in category_ids:
                db.session.add(CourseCategory(course_id=course.id, category_id=cate_id))
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return None;

        return course;

    return None;



def create_lesson(teacher_id ,course_id, description, name):
    course = Course.query.filter(Course.teacher_id == teacher_id, Course.id == course_id).first()
    if not course:
        return None
    lesson = Lesson(name=name, description=description, course_id=course_id)
    try:
        db.session.add(lesson)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return None

    return lesson


def update_lesson(lesson_id, course_id, teacher_id, name=None, description=None):

    lesson = Lesson.query.join(Course).filter(
        Course.id == course_id,
        Course.teacher_id == teacher_id,
        Lesson.id == lesson_id
    ).first()

    if lesson:

        if name:
            lesson.name = name
        if description:
            lesson.description = description


        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return None
        return lesson;

    return None


def delete_course(course_id , teacher_id):
    course = Course.query.filter(Course.id == course_id, Course.teacher_id == teacher_id).first()
    if course:
        db.session.delete(course)
        db.session.commit()
        return True
    return False

def delete_lesson(lesson_id, course_id, teacher_id):
    lesson = Lesson.query.join(Course).filter(
        Course.id == course_id,
        Course.teacher_id == teacher_id,
        Lesson.id == lesson_id
    ).first()

    if lesson:
        try:
            db.session.delete(lesson)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return False
        return True

    return False
def get_lesson_details(lesson_id):
    return Lesson.query.get(lesson_id)
