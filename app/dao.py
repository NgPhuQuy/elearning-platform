import hashlib

from flask_login import current_user

from app.models import User,Post,Comment,ReactionPost,ReactionComment,PostCate
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

def get_posts():
    return Post.query.order_by(
        Post.created_date.desc()
    ).all()

def get_post_categories():
    return PostCate.query.filter_by(
        is_active=True
    ).all()

def get_post_by_id(post_id):
    return Post.query.get(post_id)


def add_post(form, user_id):
    image = ""

    if 'image' in form.files:
        file = form.files['image']

        if file.filename:
            res = cloudinary.uploader.upload(file)
            image = res['secure_url']

    post = Post(
        title=form.form.get("title"),
        content=form.form.get("content"),
        image=image,
        category_id=form.form.get("category_id"),
        user_id=user_id
    )

    db.session.add(post)
    db.session.commit()

    return post


def add_comment(post_id, user_id, content):
    c = Comment(content=content,post_id=post_id,user_id=user_id)

    db.session.add(c)
    db.session.commit()

    return c

def add_reply_comment(parent_comment_id, post_id,user_id,content):
    reply = Comment(content=content,user_id=user_id,post_id=post_id,parent_comment_id=parent_comment_id)
    db.session.add(reply)
    db.session.commit()

    return reply

def react_post(post_id, user_id, react_type):

    react = ReactionPost.query.filter_by(
        post_id=post_id,
        user_id=user_id
    ).first()

    if react:

        if react.type == react_type:
            db.session.delete(react)
            db.session.commit()

            return False

        react.type = react_type
        db.session.commit()

        return True

    react = ReactionPost(
        post_id=post_id,
        user_id=user_id,
        type=react_type
    )

    db.session.add(react)
    db.session.commit()

    return True

def react_comment(comment_id, user_id, react_type):

    react = ReactionComment.query.filter_by(comment_id=comment_id,user_id=user_id).first()
    if react:
        if react.type == react_type:
            db.session.delete(react)

        else:
            react.type = react_type

    else:
        react = ReactionComment(comment_id=comment_id,user_id=user_id,type=react_type)
        db.session.add(react)

    db.session.commit()

    return ReactionComment.query.filter_by(
        comment_id=comment_id
    ).count()