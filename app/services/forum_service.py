from app import dao
from app.models import Comment, PostCate, VoteType
from app.services.upload_service import upload_file


def get_forum_posts(keyword=None, solved=None, category=None):
    if solved == "true":
        solved_val = True
    elif solved == "false":
        solved_val = False
    else:
        solved_val = None

    return dao.get_posts(keyword=keyword, solved=solved_val, category_id=category)


def get_forum_detail(post_id, user_id=None):
    post = dao.get_post_by_id(post_id)
    if not post:
        return None

    related_posts = dao.get_related_posts(post.id)
    user_vote = dao.get_user_post_vote(post.id, user_id) if user_id else None
    return {
        "post": post,
        "related_posts": related_posts,
        "user_vote": user_vote,
    }


def create_question(user_id, form_data, files):
    title = form_data.get("title", "").strip()
    content = form_data.get("content", "").strip()
    if not title or not content:
        return None, "Vui lòng nhập đầy đủ tiêu đề và nội dung câu hỏi!"

    image_file = files.get("image")
    image_url, _ = upload_file(image_file, folder="elearning-platform/forum")

    post = dao.create_post(
        title=title,
        content=content,
        category_ids=form_data.getlist("category_ids"),
        user_id=user_id,
        image=image_url,
    )
    return post, None


def get_all_categories():
    return PostCate.query.all()


def add_answer(post_id, user_id, content):
    content = (content or "").strip()
    if content:
        return dao.add_comment(post_id=post_id, user_id=user_id, content=content)
    return None


def accept_answer(comment_id):
    return dao.accept_answer(comment_id)


def vote_post(post_id, user_id, vote_direction):
    vote_type = VoteType.UP if vote_direction == "up" else VoteType.DOWN
    return dao.vote_post(post_id, user_id, vote_type)


def vote_comment(comment_id, user_id, vote_direction):
    vote_type = VoteType.UP if vote_direction == "up" else VoteType.DOWN
    return dao.vote_comment(comment_id, user_id, vote_type)


def reply_comment(comment_id, user_id, content):
    content = (content or "").strip()
    if not content:
        return None
    parent_comment = Comment.query.get_or_404(comment_id)
    return dao.add_comment(
        post_id=parent_comment.post_id,
        user_id=user_id,
        content=content,
        parent_comment_id=comment_id,
    )

