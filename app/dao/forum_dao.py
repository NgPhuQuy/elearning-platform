from datetime import datetime

from flask_login import current_user

from app import db
from app.models import Comment, Post, PostCate, PostCategory, ReactionComment, ReactionPost


def get_posts(keyword=None, solved=None, category_id=None):
    query = Post.query
    if keyword:
        query = query.filter(Post.title.contains(keyword) | Post.content.contains(keyword))
    if solved is not None:
        query = query.filter(Post.is_solved == solved)
    if category_id:
        query = query.join(Post.categories).filter(PostCate.id == category_id)
    return query.order_by(Post.created_date.desc()).all()


def get_post_by_id(post_id):
    post = Post.query.get(post_id)
    if post:
        post.view_count += 1
        db.session.commit()
    return post


def get_post_categories():
    return PostCate.query.order_by(PostCate.name).all()


def get_related_posts(post_id, limit=5):
    post = Post.query.get(post_id)
    if not post:
        return []
    cate_ids = [c.id for c in post.categories]
    return (
        Post.query.join(Post.categories)
        .filter(Post.id != post.id)
        .filter(PostCate.id.in_(cate_ids))
        .distinct()
        .limit(limit)
        .all()
    )


def create_post(title, content, category_ids, user_id, image=None):
    post = Post(title=title, content=content, image=image, user_id=user_id)
    db.session.add(post)
    db.session.commit()

    if category_ids:
        for cate_id in category_ids:
            db.session.add(PostCategory(post_id=post.id, category_id=cate_id))
        db.session.commit()
    return post


def add_comment(post_id, user_id, content, parent_comment_id=None):
    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=content,
        parent_comment_id=parent_comment_id,
    )
    db.session.add(comment)
    db.session.commit()
    return comment


def accept_answer(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return False
    post = comment.post
    if post.user_id != current_user.id:
        return False

    Comment.query.filter_by(post_id=post.id, is_accepted=True).update({"is_accepted": False})
    comment.is_accepted = True
    post.is_solved = True
    db.session.commit()
    return True


def _vote_entity(model_cls, fk_field, target_id, user_id, vote_type):
    filter_kwargs = {fk_field: target_id, "user_id": user_id}
    reaction = model_cls.query.filter_by(**filter_kwargs).first()
    if reaction:
        if reaction.vote_type == vote_type:
            db.session.delete(reaction)
        else:
            reaction.vote_type = vote_type
    else:
        filter_kwargs["vote_type"] = vote_type
        db.session.add(model_cls(**filter_kwargs))
    db.session.commit()


def vote_post(post_id, user_id, vote_type):
    return _vote_entity(ReactionPost, "post_id", post_id, user_id, vote_type)


def vote_comment(comment_id, user_id, vote_type):
    return _vote_entity(ReactionComment, "comment_id", comment_id, user_id, vote_type)


def get_post_score(post):
    return sum(r.vote_type.value for r in post.reactions)


def get_comment_score(comment):
    return sum(r.vote_type.value for r in comment.reactions)


def get_user_post_vote(post_id, user_id):
    return ReactionPost.query.filter_by(post_id=post_id, user_id=user_id).first()


def get_question_today():
    return Post.query.filter(db.func.date(Post.created_date) == datetime.now().date()).all()
