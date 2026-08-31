from flask import redirect, render_template, request, url_for
from flask_login import current_user

from app import app
from app.decorators import login_required
from app.services import forum_service


@app.route("/forum")
def forum():
    keyword = request.args.get("kw")
    solved = request.args.get("solved")
    category = request.args.get("category", type=int)
    posts = forum_service.get_forum_posts(keyword=keyword, solved=solved, category=category)
    return render_template("forum/index.html", posts=posts)


@app.route("/forum/<int:post_id>")
@login_required
def forum_detail(post_id):
    ctx = forum_service.get_forum_detail(post_id, user_id=current_user.id)
    if not ctx:
        return redirect(url_for("forum"))
    return render_template("forum/detail.html", **ctx)


@app.route("/forum/create", methods=["GET", "POST"])
@login_required
def create_question():
    if request.method == "POST":
        post, error = forum_service.create_question(current_user.id, request.form, request.files)
        if error:
            categories = forum_service.get_all_categories()
            return render_template("forum/create.html", categories=categories, error=error)
        return redirect(url_for("forum"))

    categories = forum_service.get_all_categories()
    return render_template("forum/create.html", categories=categories)


@app.route("/forum/<int:post_id>/answer", methods=["POST"])
@login_required
def answer(post_id):
    forum_service.add_answer(post_id, current_user.id, request.form.get("content"))
    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/forum/<int:post_id>/upvote", methods=["POST"])
@login_required
def upvote_post(post_id):
    forum_service.vote_post(post_id, current_user.id, "up")
    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/forum/<int:post_id>/downvote", methods=["POST"])
@login_required
def downvote_post(post_id):
    forum_service.vote_post(post_id, current_user.id, "down")
    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/comment/<int:comment_id>/accept", methods=["POST"])
@login_required
def accept_answer(comment_id):
    forum_service.accept_answer(comment_id)
    return redirect(request.referrer or url_for("forum"))


@app.route("/comment/<int:comment_id>/upvote", methods=["POST"])
@login_required
def upvote_comment(comment_id):
    forum_service.vote_comment(comment_id, current_user.id, "up")
    return redirect(request.referrer or url_for("forum"))


@app.route("/comment/<int:comment_id>/downvote", methods=["POST"])
@login_required
def downvote_comment(comment_id):
    forum_service.vote_comment(comment_id, current_user.id, "down")
    return redirect(request.referrer or url_for("forum"))


@app.route("/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply_comment(comment_id):
    comment = forum_service.reply_comment(comment_id, current_user.id, request.form.get("content"))
    if comment:
        return redirect(url_for("forum_detail", post_id=comment.post_id))
    return redirect(url_for("forum"))
