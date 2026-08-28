from sqlalchemy.exc import SQLAlchemyError

from app import app, dao, db
from app.models import Admin, Category, PostCate, Teacher, User

COURSE_CATEGORIES = ("Lập trình", "Thiết kế", "Marketing", "Data Science")
POST_CATEGORIES = ("Công nghệ", "Hỏi đáp", "Chia sẻ kinh nghiệm")


def _ensure_user(username, email, first_name, last_name, phone=None):
    user = User.query.filter_by(username=username).first()
    if user:
        return user, False

    user = User(
        username=username,
        password=dao.hash_password("11111111"),
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
    )
    db.session.add(user)
    db.session.flush()
    return user, True


def _ensure_named_records(model, names):
    existing_names = {record.name for record in model.query.filter(model.name.in_(names)).all()}
    for name in names:
        if name not in existing_names:
            db.session.add(model(name=name))


def seed_data():
    with app.app_context():
        print("Đang bắt đầu seed data nền...")

        try:
            admin_user, created = _ensure_user(
                username="admin",
                email="admin@gmail.com",
                first_name="Nguyen Tran",
                last_name="Admin",
                phone="0999999999",
            )
            if created:
                print("Đã tạo tài khoản Admin.")

            if not Admin.query.filter_by(user_id=admin_user.id).first():
                db.session.add(Admin(user_id=admin_user.id, note="System Super Admin"))

            teacher_user, created = _ensure_user(
                username="teacher01",
                email="teacher01@gmail.com",
                first_name="Giảng viên",
                last_name="Python",
            )
            if created:
                print("Đã tạo tài khoản Teacher.")

            if not Teacher.query.filter_by(user_id=teacher_user.id).first():
                db.session.add(Teacher(user_id=teacher_user.id, note="Chuyên gia Backend"))

            _ensure_named_records(Category, COURSE_CATEGORIES)
            _ensure_named_records(PostCate, POST_CATEGORIES)

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise

        print("Seed data hoàn tất!")


if __name__ == "__main__":
    seed_data()
