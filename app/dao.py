import hashlib
from datetime import datetime

from flask_login import current_user
from app import db, login
from app.models import User, Post, ReactionPost, ReactionComment, Comment, VoteType, Course


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

    return c


def accept_answer(comment_id):
    comment = Comment.query.get(comment_id)

    if not comment:
        return False

    comment.is_accepted = True
    comment.post.is_solved = True

    db.session.commit()

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