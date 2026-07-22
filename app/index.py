import cloudinary.uploader
from flask import redirect, render_template, request,url_for
from flask_login import login_user, current_user, logout_user,login_required
from app import app, dao, login, db
from datetime import datetime
from app.dao import register_user
from app.models import PostCate,VoteType,Comment,Post

@app.context_processor
def inject_common():
    return {
        "current_year": datetime.now().year,
        "dao": dao
    }
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            error = "Mật khẩu không khớp!"
            return render_template("auth/register.html", error=error)

        username = request.form.get('username')
        if dao.is_username_exist(username=username):
            error = "Username đã tồn tại!"
            return render_template("auth/register.html", error=error)

        email = request.form.get("email")
        if dao.is_email_used(email=email):
            error = "Email đã được sử dụng!"
            return render_template("auth/register.html", error=error)

        phone = request.form.get("phone")
        if dao.is_phone_used(phone=phone):
            error = "Số điện thoại này đã được đăng ký!"
            return render_template("auth/register.html", error=error)

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        avatar = request.files.get("avatar")

        file_path = None
        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar)
                file_path = res["secure_url"]
            except Exception:
                error = "Tải file thất bại!"
                return render_template("auth/register.html", error=error)
        try:
            user = register_user(username, password, email, phone, file_path, first_name, last_name)
            login_user(user)
            return redirect("/")

        except Exception:
            error = "Hệ thống lỗi, vui lòng quay lại sau!"
            db.session.rollback()
            return render_template("auth/register.html", error=error)

    return render_template("auth/register.html", error=error)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)

        if user:
            login_user(user)
            return redirect("/")
        else:
            error = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("auth/login.html", error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

@app.route('/profile')
def profile():
    return render_template("profile/profile.html")


@app.route('/profile/change-info', methods=['GET', 'POST'])
def change_info():
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        avatar = request.files.get("avatar")
        file_path = None

        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar)
                file_path = res["secure_url"]
            except Exception:
                error = "Tải file thất bại!"
                return render_template("profile/change-info.html", error=error)

        dao.change_info(email, phone, file_path, first_name, last_name)

        return redirect("/profile")

    return render_template("profile/change-info.html", error=error)


@app.route('/profile/change-password', methods=['GET', 'POST'])
def change_password():
    error = None
    if request.method == "POST":
        curr_password = request.form.get('curr_password')
        user = dao.auth_user(username=current_user.username, password=curr_password)
        if not user:
            error = "Sai mật khẩu!"
            return render_template("profile/change-password.html", error=error)

        new_password = request.form.get('new_password')
        new_confirm = request.form.get('new_confirm')
        if new_password != new_confirm:
            error = "Mật khẩu không khớp!"
            return render_template("profile/change-password.html", error=error)

        dao.change_password(new_password)
        return redirect("/")

    return render_template("profile/change-password.html", error=error)


#forum

@app.route("/forum")
@login_required
def forum():

    keyword = request.args.get("kw")
    solved = request.args.get("solved")

    if solved == "true":
        solved = True
    elif solved == "false":
        solved = False
    else:
        solved = None

    posts = dao.get_posts(keyword=keyword, solved=solved)

    return render_template( "forum/index.html",posts=posts)

@app.route("/forum/<int:post_id>")
@login_required
def forum_detail(post_id):
    post = Post.query.get_or_404(post_id)

    post.view_count += 1
    db.session.commit()
    related_posts = dao.get_related_posts(post.id,post.category_id)
    user_vote = dao.get_user_post_vote(post.id, current_user.id)
    return render_template("forum/detail.html",post=post,related_posts=related_posts,user_vote=user_vote)

@app.route("/forum/create", methods=["GET", "POST"])
@login_required
def create_question():

    if request.method == "POST":

        image = request.files.get("image")

        image_url = None

        if image and image.filename:
            res = cloudinary.uploader.upload(image)
            image_url = res["secure_url"]

        dao.create_post(
            title=request.form["title"],
            content=request.form["content"],
            category_id=request.form["category_id"],
            user_id=current_user.id,
            image=image_url
        )

        return redirect(url_for("forum"))

    categories = PostCate.query.all()

    return render_template(
        "forum/create.html",
        categories=categories
    )

@app.route("/forum/<int:post_id>/answer",methods=["POST"])
@login_required
def answer(post_id):

    dao.add_comment(
        post_id=post_id,
        user_id=current_user.id,
        content=request.form["content"]
    )

    return redirect(
        url_for("forum_detail",post_id=post_id)
    )

@app.route("/forum/<int:post_id>/upvote",methods=["POST"])
@login_required
def upvote_post(post_id):

    dao.vote_post(post_id,current_user.id,VoteType.UP)
    return redirect(url_for("forum_detail",post_id=post_id))

@app.route("/forum/<int:post_id>/downvote",methods=["POST"])
@login_required
def downvote_post(post_id):

    dao.vote_post(post_id,current_user.id,VoteType.DOWN)

    return redirect(url_for("forum_detail",post_id=post_id))


@app.route("/comment/<int:comment_id>/accept",methods=["POST"])
@login_required
def accept_answer(comment_id):

    dao.accept_answer(comment_id)

    return redirect(request.referrer)

@app.route("/comment/<int:comment_id>/upvote",methods=["POST"])
@login_required
def upvote_comment(comment_id):

    dao.vote_comment(comment_id,current_user.id,VoteType.UP)

    return redirect(request.referrer)

@app.route("/comment/<int:comment_id>/downvote",methods=["POST"])
@login_required
def downvote_comment(comment_id):

    dao.vote_comment(comment_id,current_user.id,VoteType.DOWN)

    return redirect(request.referrer)


@app.route("/comment/<int:comment_id>/reply",methods=["POST"])
@login_required
def reply_comment(comment_id):

    parent_comment = Comment.query.get_or_404(comment_id)

    dao.add_comment(
        post_id=parent_comment.post_id,
        user_id=current_user.id,
        content=request.form["content"],
        parent_comment_id=comment_id
    )

    return redirect(url_for("forum_detail",post_id=parent_comment.post_id))
if __name__ == '__main__':
    app.run(debug=True)