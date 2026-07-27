from datetime import datetime

from flask import flash, redirect
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, logout_user
from markupsafe import Markup
from wtforms import TextAreaField
from wtforms.widgets import TextArea

from app import app, db
from app.models import (
    ApplicationStatus,
    Category,
    Comment,
    Course,
    Lesson,
    Post,
    PostCate,
    Teacher,
    TeacherApplication,
    User,
)


class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("class", "ckeditor")
        return super().__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class MyAuthenticatedView(ModelView):
    # def is_accessible(self) -> bool:
    #     return current_user.is_authenticated and current_user.has_role("ADMIN")

    def inaccessible_callback(self, name, **kwargs):
        return redirect("/login")


class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        # KPI
        total_users = db.session.query(User).count()
        total_courses = db.session.query(Course).count()
        total_teachers = db.session.query(Teacher).count()
        total_posts = db.session.query(Post).count()

        return self.render(
            "admin/index.html",
            total_users=total_users,
            total_courses=total_courses,
            total_teachers=total_teachers,
            total_posts=total_posts,
        )


class MyLogoutView(BaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")

    def is_accessible(self):
        return current_user.is_authenticated


class UserAdmin(MyAuthenticatedView):
    column_list = ("id", "username", "first_name", "last_name", "email", "phone")
    column_searchable_list = ("username", "email", "phone")
    column_filters = ("is_active",)

    can_delete = False
    form_excluded_columns = (
        "password",
        "google_sub",
        "teacher_profile",
        "posts",
        "comments",
    )


class TeacherAdmin(MyAuthenticatedView):
    column_list = ("id", "user", "note")
    column_searchable_list = ("note",)


class CategoryAdmin(MyAuthenticatedView):
    column_list = ("id", "name")
    column_searchable_list = ("name",)


class CourseAdmin(MyAuthenticatedView):
    column_list = ("name", "is_sale", "teacher", "level")
    column_searchable_list = ("name",)
    column_filters = ("level", "is_sale")

    can_export = True
    extra_js = ["//cdn.ckeditor.com/4.6.0/standard/ckeditor.js"]
    form_overrides = {"description": CKTextAreaField}
    form_excluded_columns = ("chapters", "course_category", "outcomes")


class LessonAdmin(MyAuthenticatedView):
    column_list = ("id", "name", "type", "chapter", "description")
    column_filters = ("type",)


class PostCateAdmin(MyAuthenticatedView):
    column_list = ("id", "name", "description")
    column_searchable_list = ("name",)


class PostAdmin(MyAuthenticatedView):
    column_list = ("id", "title", "user", "categories", "view_count", "is_solved")
    column_searchable_list = ("title",)
    column_filters = ("is_solved", "categories")


class CommentAdmin(MyAuthenticatedView):
    column_list = ("id", "post", "user", "is_accepted")
    column_filters = ("is_accepted",)


# --- Đơn đăng ký giảng viên ---


def _documents_formatter(view, context, model, name):
    parts = []
    for url, label in [
        (model.id_card_file, "CCCD"),
        (model.degree_file, "Bằng cấp"),
        (model.cv_file, "CV"),
        (model.extra_cert_file, "Chứng chỉ"),
        (model.video_file, "Video"),
    ]:
        if url:
            parts.append(f'<a href="{url}" target="_blank" rel="noopener">{label}</a>')
    return (
        Markup(" &nbsp;|&nbsp; ".join(parts))
        if parts
        else Markup('<span class="text-muted">—</span>')
    )


def _status_formatter(view, context, model, name):
    colors = {
        ApplicationStatus.PENDING: "warning",
        ApplicationStatus.APPROVED: "success",
        ApplicationStatus.REJECTED: "danger",
    }
    color = colors.get(model.status, "secondary")
    return Markup(f'<span class="badge bg-{color}">{model.status.value}</span>')


def _approve_application(application):
    if not application.user.teacher_profile:
        db.session.add(Teacher(user_id=application.user_id, note=application.bio))
    application.status = ApplicationStatus.APPROVED
    application.reject_reason = None
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now()


def _reject_application(application, reason=None):
    application.status = ApplicationStatus.REJECTED
    application.reject_reason = reason or "Hồ sơ chưa đạt yêu cầu xét duyệt."
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now()


class TeacherApplicationAdmin(MyAuthenticatedView):
    column_list = (
        "id",
        "user",
        "major",
        "degree",
        "experience",
        "documents",
        "status",
        "created_date",
    )
    column_filters = ("status", "degree", "experience")
    column_searchable_list = ("major", "workplace")
    column_default_sort = ("created_date", True)
    column_sortable_list = (
        "id",
        "major",
        "degree",
        "experience",
        "status",
        "created_date",
    )

    column_labels = {
        "user": "Người nộp",
        "major": "Chuyên ngành",
        "degree": "Bằng cấp",
        "experience": "Kinh nghiệm",
        "documents": "Tài liệu",
        "status": "Trạng thái",
        "created_date": "Ngày nộp",
    }

    column_formatters = {
        "documents": _documents_formatter,
        "status": _status_formatter,
    }

    column_details_list = (
        "id",
        "user",
        "workplace",
        "degree",
        "major",
        "bio",
        "expertise",
        "experience",
        "teach_style",
        "linkedin",
        "website",
        "documents",
        "status",
        "reject_reason",
        "reviewer",
        "reviewed_at",
        "created_date",
    )
    can_view_details = True
    details_modal = True

    can_create = False
    can_delete = False
    form_columns = ("status", "reject_reason")

    def on_model_change(self, form, model, is_created):
        if model.status == ApplicationStatus.APPROVED:
            if not model.user.teacher_profile:
                db.session.add(Teacher(user_id=model.user_id, note=model.bio))
            model.reject_reason = None
        if model.status in (ApplicationStatus.APPROVED, ApplicationStatus.REJECTED):
            model.reviewed_by = current_user.id
            model.reviewed_at = datetime.now()

    @action("approve", "Duyệt", "Bạn có chắc muốn DUYỆT các đơn đã chọn?")
    def action_approve(self, ids):
        applications = TeacherApplication.query.filter(
            TeacherApplication.id.in_(ids)
        ).all()
        count = 0
        for application in applications:
            if application.status == ApplicationStatus.PENDING:
                _approve_application(application)
                count += 1
        db.session.commit()
        flash(f"Đã duyệt {count} đơn.", "success")

    @action("reject", "Từ chối", "Bạn có chắc muốn TỪ CHỐI các đơn đã chọn?")
    def action_reject(self, ids):
        applications = TeacherApplication.query.filter(
            TeacherApplication.id.in_(ids)
        ).all()
        count = 0
        for application in applications:
            if application.status == ApplicationStatus.PENDING:
                _reject_application(application)
                count += 1
        db.session.commit()
        flash(f"Đã từ chối {count} đơn.", "success")


admin = Admin(
    app,
    name="Language Academy Manager",
    index_view=MyAdminIndexView(),
    theme=Bootstrap4Theme(),
)

admin.add_view(UserAdmin(User, db.session, name="Users"))
admin.add_view(TeacherAdmin(Teacher, db.session, name="Teachers"))
admin.add_view(
    TeacherApplicationAdmin(TeacherApplication, db.session, name="Đơn đăng ký GV")
)
admin.add_view(CategoryAdmin(Category, db.session, name="Categories"))
admin.add_view(CourseAdmin(Course, db.session, name="Courses"))
admin.add_view(LessonAdmin(Lesson, db.session, name="Lessons"))
admin.add_view(PostCateAdmin(PostCate, db.session, name="Post Categories"))
admin.add_view(PostAdmin(Post, db.session, name="Posts"))
admin.add_view(CommentAdmin(Comment, db.session, name="Comments"))
admin.add_view(MyLogoutView(name="Đăng xuất"))
