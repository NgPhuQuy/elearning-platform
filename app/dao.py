import hashlib
from datetime import datetime

from flask_login import current_user

from app import TEACHER_APPLICATION_COOLDOWN_DAYS, db, login
from app.models import (
    ApplicationStatus,
    Category,
    Chapter,
    Comment,
    Course,
    CourseCategory,
    CourseOutcome,
    Lesson,
    Post,
    PostCate,
    ReactionComment,
    ReactionPost,
    Teacher,
    TeacherApplication,
    User,
VideoContent,
DocContent,
LessonType,
)


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()


def register_user(username, password, email,
                  phone, avatar, first_name, last_name):
    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password, email=email, phone=phone,
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




def register_teacher(user_id, note=""):
    teacher = Teacher(user_id=user_id, note=note)
    try:
        db.session.add(teacher)
        db.session.commit()
        return teacher
    except Exception:
        db.session.rollback()
        return None

def get_categories():
    return Category.query.order_by(Category.name).all()

def create_course(name,
                  description,
                  image,
                  teacher_id,
                  level,
                  category_ids,
                  ):

    course = Course(
        name=name,
        description=description,
        image=image,

        teacher_id=teacher_id,
        level=level
    )

    try:
        db.session.add(course)
        db.session.flush()

        if category_ids:
            for cate_id in category_ids:
                db.session.add(
                    CourseCategory(
                        course_id=course.id,
                        category_id=cate_id
                    )
                )

        db.session.commit()
        return course

    except Exception:
        db.session.rollback()
        return None

def get_course_details(course_id, teacher_id=None):
    query = Course.query.filter_by(id=course_id)

    if teacher_id is not None:
        query = query.filter_by(teacher_id=teacher_id)

    return query.first()

def save_video_for_lesson(lesson_id, teacher_id, video_url, duration=0):
    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()

    if not lesson:
        return None

    video = VideoContent.query.filter_by(lesson_id=lesson_id).first()
    if video:
        video.video_url = video_url
        video.duration = duration
    else:
        video = VideoContent(lesson_id=lesson_id, video_url=video_url, duration=duration)
        db.session.add(video)

    lesson.type = LessonType.VIDEO

    try:
        db.session.commit()
        return video
    except Exception:
        db.session.rollback()
        return None


def save_doc_for_lesson(lesson_id, teacher_id, file_url):
    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()

    if not lesson:
        return None

    doc = DocContent.query.filter_by(lesson_id=lesson_id).first()
    if doc:
        doc.file_url = file_url
    else:
        doc = DocContent(lesson_id=lesson_id, file_url=file_url)
        db.session.add(doc)

    lesson.type = LessonType.DOCUMENT

    try:
        db.session.commit()
        return doc
    except Exception:
        db.session.rollback()
        return None

def clear_video_content(lesson_id, teacher_id):
    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()
    if not lesson:
        return False

    video = VideoContent.query.filter_by(lesson_id=lesson_id).first()
    if video:
        db.session.delete(video)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return False
    return True


def clear_doc_content(lesson_id, teacher_id):
    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()
    if not lesson:
        return False

    doc = DocContent.query.filter_by(lesson_id=lesson_id).first()
    if doc:
        db.session.delete(doc)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return False
    return True
def delete_course(course_id, teacher_id):
    course = Course.query.filter_by(
        id=course_id,
        teacher_id=teacher_id
    ).first()

    if not course:
        return False

    try:
        db.session.delete(course)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False

def update_lesson(lesson_id,
                  teacher_id,
                  name=None,
                  description=None,
                  lesson_type=None):

    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()

    if not lesson:
        return None

    if name:
        lesson.name = name

    if description:
        lesson.description = description

    if lesson_type:
        lesson.type = lesson_type

    try:
        db.session.commit()
        return lesson

    except Exception:
        db.session.rollback()
        return None

def delete_lesson(lesson_id, teacher_id):

    lesson = Lesson.query.join(Chapter).join(Course).filter(
        Lesson.id == lesson_id,
        Course.teacher_id == teacher_id
    ).first()

    if not lesson:
        return False

    try:
        db.session.delete(lesson)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False
def get_chapters(course_id):
    return Chapter.query.filter_by(
        course_id=course_id
    ).order_by(Chapter.order).all()


def get_lessons(chapter_id):
    return Lesson.query.filter_by(
        chapter_id=chapter_id
    ).all()


def get_lesson_details(lesson_id):
    return Lesson.query.get(lesson_id)
def get_outcomes(course_id):
    return CourseOutcome.query.filter_by(course_id=course_id).all()


def create_outcome(course_id, content):
    outcome = CourseOutcome(
        course_id=course_id,
        content=content
    )

    try:
        db.session.add(outcome)
        db.session.commit()
        return outcome

    except Exception:
        db.session.rollback()
        return None

def replace_outcomes(course_id, contents):
    CourseOutcome.query.filter_by(course_id=course_id).delete()
    for content in contents:
        content = content.strip()
        if content:
            db.session.add(CourseOutcome(course_id=course_id, content=content))
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
def delete_outcome(outcome_id):
    outcome = CourseOutcome.query.get(outcome_id)

    if not outcome:
        return False

    try:
        db.session.delete(outcome)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False
# forum
def get_posts(keyword=None, solved=None):
    query = Post.query

    if keyword:
        query = query.filter(Post.title.contains(keyword))

    if solved is not None:
        query = query.filter(Post.is_solved == solved)

    return query.order_by(Post.created_date.desc()).all()


def get_post_by_id(post_id):
    post = Post.query.get(post_id)

    if post:
        post.view_count += 1
        db.session.commit()

    return post


def create_post(title, content, category_id, user_id, image=None):
    post = Post(title=title, content=content, category_id=category_id, user_id=user_id, image=image)

    db.session.add(post)
    db.session.commit()

    return post


def add_comment(post_id, user_id, content, parent_comment_id=None):
    c = Comment(content=content, post_id=post_id, user_id=user_id, parent_comment_id=parent_comment_id)

    db.session.add(c)
    db.session.commit()
def get_courses_by_teacher_id(teacher_id):
    return Course.query.filter_by(
        teacher_id=teacher_id
    ).order_by(Course.created_date.desc()).all()
def update_course (course_id, teacher_id, name=None, description=None, image=None, level=None,category_ids=None):
    course = Course.query.filter(Course.id == course_id, Course.teacher_id == teacher_id).first()
    if course:
        if  name:
            course.name = name
        if  description:
            course.description = description
        if image:
            course.image = image

        if level:
            course.level = level
        if category_ids is not None:
            CourseCategory.query.filter_by(course_id=course.id).delete()
            for cate_id in category_ids:
                db.session.add(CourseCategory(course_id=course.id, category_id=cate_id))
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return None;

    return


def accept_answer(comment_id):
    comment = Comment.query.get(comment_id)
def create_chapter(course_id, teacher_id, name, description):

# def accept_answer(comment_id):
#     comment = Comment.query.get(comment_id)

    course = Course.query.filter(
        Course.id == course_id,
        Course.teacher_id == teacher_id
    ).first()



    db.session.commit()
    if not course:
        return None

    chapter = Chapter(
        name=name,
        description=description,
        course_id=course.id
    )

    try:
        db.session.add(chapter)
        db.session.commit()
        return chapter

    except Exception:
        db.session.rollback()
        return None

def update_chapter(chapter_id,
                   teacher_id,
                   name=None,
                   description=None):

    chapter = Chapter.query.join(Course).filter(
        Chapter.id == chapter_id,
        Course.teacher_id == teacher_id
    ).first()

    if not chapter:
        return None

    if name:
        chapter.name = name

    if description:
        chapter.description = description

    try:
        db.session.commit()
        return chapter

    except Exception:
        db.session.rollback()
        return None

def delete_chapter(chapter_id, teacher_id):

    chapter = Chapter.query.join(Course).filter(
        Chapter.id == chapter_id,
        Course.teacher_id == teacher_id
    ).first()

    if not chapter:
        return False

    try:
        db.session.delete(chapter)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def create_lesson(teacher_id,  chapter_id,name,  description, lesson_type):
    chapter = Chapter.query.join(Course).filter(
        Chapter.id == chapter_id,
        Course.teacher_id == teacher_id
    ).first()

    if not chapter:
        return None
    lesson = Lesson(name=name, description=description,  type=LessonType[lesson_type],  chapter_id=chapter.id)
    try:
        db.session.add(lesson)
        db.session.commit()
        return lesson
    except Exception as e:
        db.session.rollback()
        return None

    return True


def vote_post(post_id, user_id, vote_type):
    reaction = ReactionPost.query.filter_by(
        post_id=post_id,
        user_id=user_id
    ).first()

    if reaction:

        if reaction.vote_type == vote_type:
            db.session.delete(reaction)

        else:
            reaction.vote_type = vote_type

    else:
        reaction = ReactionPost(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_type
        )

        db.session.add(reaction)

    db.session.commit()


def vote_comment(comment_id, user_id, vote_type):
    reaction = ReactionComment.query.filter_by(
        comment_id=comment_id,
        user_id=user_id
    ).first()

    if reaction:

        if reaction.vote_type == vote_type:
            db.session.delete(reaction)

        else:
            reaction.vote_type = vote_type

    else:
        reaction = ReactionComment(
            comment_id=comment_id,
            user_id=user_id,
            vote_type=vote_type
        )

        db.session.add(reaction)

    db.session.commit()


def get_post_score(post):
    score = 0

    for r in post.reactions:
        score += r.vote_type.value

    return score


def get_comment_score(comment):
    score = 0

    for r in comment.reactions:
        score += r.vote_type.value

    return score


def get_related_posts(post_id, category_id, limit=5):
    return (
        Post.query.filter(
            Post.category_id == category_id,
            Post.id != post_id
        )
        .order_by(Post.created_date.desc())
        .limit(limit)
        .all()
    )


def get_user_post_vote(post_id, user_id):
    return ReactionPost.query.filter_by(
        post_id=post_id,
        user_id=user_id
    ).first()


def get_course_sale():
    return Course.query.filter_by(is_sale=True).all()

def get_question_today():
    return Post.query.filter(Post.created_date == datetime.today()).all()