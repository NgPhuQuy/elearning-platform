from app import app, dao, db
from app.models import Admin, Category, PostCate, Teacher, User


def seed_data():
    with app.app_context():
        print("Đang bắt đầu seed data nền...")

        if not User.query.filter_by(username="admin").first():
            admin_user = User(
                username="admin",
                password=dao.hash_password("11111111"),
                first_name="Nguyen Tran",
                last_name="Admin",
                email="admin@gmail.com",
                phone="0999999999",
            )
            db.session.add(admin_user)
            db.session.flush()
            db.session.add(Admin(user_id=admin_user.id, note="System Super Admin"))
            print("Đã tạo tài khoản Admin.")

        if not User.query.filter_by(username="teacher01").first():
            teacher_user = User(
                username="teacher01",
                password=dao.hash_password("11111111"),
                first_name="Giảng viên",
                last_name="Python",
                email="teacher01@gmail.com",
            )
            db.session.add(teacher_user)
            db.session.flush()
            db.session.add(Teacher(user_id=teacher_user.id, note="Chuyên gia Backend"))
            print("Đã tạo tài khoản Teacher.")

        course_categories = ["Lập trình", "Thiết kế", "Marketing", "Data Science"]
        for cat in course_categories:
            if not Category.query.filter_by(name=cat).first():
                db.session.add(Category(name=cat))

        post_categories = ["Công nghệ", "Hỏi đáp", "Chia sẻ kinh nghiệm"]
        for p_cat in post_categories:
            if not PostCate.query.filter_by(name=p_cat).first():
                db.session.add(PostCate(name=p_cat))

        db.session.commit()
        print("Seed data hoàn tất!")


if __name__ == "__main__":
    seed_data()
