import cloudinary.uploader
from flask import redirect, render_template, request,url_for
from flask_login import login_user, current_user, logout_user,login_required
from app import app, dao, login, db
from datetime import datetime
from app.dao import register_user
from app.models import ReactionType,Post,Comment,ReactionPost,ReactionComment

@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

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


@app.route('/forum')
@login_required
def forum():
    posts = dao.get_posts()
    return render_template('forum/index.html',posts=posts)

@app.route('/forum/<int:post_id>')
@login_required
def forum_detail(post_id):

    post = dao.get_post_by_id(post_id)

    my_post_react = ReactionPost.query.filter_by(post_id=post_id,user_id=current_user.id).first()

    return render_template('forum/detail.html',post=post,my_post_react=my_post_react)

@app.route('/forum/<int:post_id>/comment',methods=['POST'])
@login_required
def add_comment(post_id):
    dao.add_comment(post_id,current_user.id,request.form.get('content'))

    return redirect(url_for('forum_detail',post_id=post_id))

@app.route('/forum/create', methods=['GET', 'POST'])
@login_required
def create_post():
    categories = dao.get_post_categories()

    if request.method == 'POST':
        dao.add_post(request,current_user.id)
        return redirect(url_for('forum'))

    return render_template('forum/create-post.html',categories=categories)

@app.route('/forum/<int:post_id>/react',methods=['POST'])
@login_required
def react_post(post_id):

    react_type = ReactionType[request.form.get('type')]

    dao.react_post(post_id,current_user.id,react_type)

    post = Post.query.get(post_id)

    current_react = ReactionPost.query.filter_by(post_id=post_id,user_id=current_user.id).first()

    active = ( current_react is not None and current_react.type == react_type)

    return {
        "success": True,
        "count": len(post.reactions),
        "active": active,
        "type": react_type.name
    }

@app.route('/comment/<int:comment_id>/react',methods=['POST'])
@login_required
def react_comment(comment_id):

    react_type = ReactionType[
        request.form.get('type')
    ]

    dao.react_comment(comment_id,current_user.id,react_type)

    comment = Comment.query.get(comment_id)

    current_react = ReactionComment.query.filter_by(comment_id=comment_id,user_id=current_user.id).first()

    active = (current_react is not None and current_react.type == react_type)

    return {
        "success": True,
        "count": len(comment.reactions),
        "comment_id": comment_id,
        "active": active,
        "type": react_type.name
    }

@app.route('/comment/<int:comment_id>/reply',methods=['POST'])
@login_required
def reply_comment(comment_id):
    content = request.form.get('content')
    post_id = request.form.get('post_id')
    dao.add_reply_comment(comment_id,post_id,current_user.id,content)


    return redirect(url_for('forum_detail',post_id=post_id))

if __name__ == '__main__':
    app.run(debug=True)