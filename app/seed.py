from datetime import datetime, timedelta

from app import app, db
from app.dao import hash_password
from app.models import (
    Admin,
    Answer,
    ApplicationStatus,
    Category,
    Chapter,
    Comment,
    Conversation,
    ConversationMember,
    Course,
    CourseCategory,
    CourseLevel,
    CourseOutcome,
    DocContent,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonProgress,
    LessonType,
    Message,
    MessageReaction,
    Payment,
    PaymentStatus,
    Post,
    PostCate,
    Question,
    ReactionComment,
    ReactionPost,
    Score,
    Teacher,
    TeacherApplication,
    Test,
    User,
    VideoContent,
    VoteType,
)


def get_or_create_user(
    username,
    password,
    email,
    first_name,
    last_name,
    phone=None,
    bio="",
):
    user = User.query.filter_by(username=username).first()

    if user:
        return user

    user = User(
        username=username,
        password=hash_password(password),
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        avatar="",
        bio=bio,
        is_active=True,
    )

    db.session.add(user)
    db.session.flush()

    return user


def seed_users():
    print("Seeding users...")

    admin_user = get_or_create_user(
        username="admin",
        password="123456",
        email="admin@example.com",
        first_name="Nguyễn",
        last_name="Quản Trị",
        phone="0900000001",
        bio="Quản trị viên hệ thống",
    )

    teacher1 = get_or_create_user(
        username="teacher01",
        password="123456",
        email="teacher01@example.com",
        first_name="Nguyễn",
        last_name="Minh Anh",
        phone="0900000002",
        bio="Giảng viên tiếng Anh",
    )

    teacher2 = get_or_create_user(
        username="teacher02",
        password="123456",
        email="teacher02@example.com",
        first_name="Trần",
        last_name="Hoàng Nam",
        phone="0900000003",
        bio="Giảng viên IELTS",
    )

    teacher3 = get_or_create_user(
        username="teacher03",
        password="123456",
        email="teacher03@example.com",
        first_name="Lê",
        last_name="Thu Hà",
        phone="0900000004",
        bio="Giảng viên tiếng Nhật",
    )

    student1 = get_or_create_user(
        username="student01",
        password="123456",
        email="student01@example.com",
        first_name="Phạm",
        last_name="Minh Đức",
        phone="0900000005",
        bio="Sinh viên đang học tiếng Anh",
    )

    student2 = get_or_create_user(
        username="student02",
        password="123456",
        email="student02@example.com",
        first_name="Nguyễn",
        last_name="Ngọc Linh",
        phone="0900000006",
        bio="Sinh viên",
    )

    student3 = get_or_create_user(
        username="student03",
        password="123456",
        email="student03@example.com",
        first_name="Trần",
        last_name="Gia Huy",
        phone="0900000007",
        bio="Sinh viên",
    )

    student4 = get_or_create_user(
        username="student04",
        password="123456",
        email="student04@example.com",
        first_name="Võ",
        last_name="Khánh Vy",
        phone="0900000008",
        bio="Sinh viên",
    )

    student5 = get_or_create_user(
        username="student05",
        password="123456",
        email="student05@example.com",
        first_name="Đỗ",
        last_name="Anh Tuấn",
        phone="0900000009",
        bio="Sinh viên",
    )

    db.session.commit()

    return {
        "admin": admin_user,
        "teachers": [teacher1, teacher2, teacher3],
        "students": [
            student1,
            student2,
            student3,
            student4,
            student5,
        ],
    }


# ============================================================
# ADMIN / TEACHER
# ============================================================


def seed_admin_teacher(users):
    print("Seeding admin and teachers...")

    admin_user = users["admin"]

    admin = Admin.query.filter_by(user_id=admin_user.id).first()

    if not admin:
        admin = Admin(
            user_id=admin_user.id,
            note="Quản trị viên chính",
        )
        db.session.add(admin)

    teachers = []

    notes = [
        "Giảng viên tiếng Anh giao tiếp",
        "Giảng viên IELTS",
        "Giảng viên tiếng Nhật",
    ]

    for user, note in zip(users["teachers"], notes):
        teacher = Teacher.query.filter_by(user_id=user.id).first()

        if not teacher:
            teacher = Teacher(
                user_id=user.id,
                note=note,
            )
            db.session.add(teacher)
            db.session.flush()

        teachers.append(teacher)

    db.session.commit()

    return teachers


# ============================================================
# COURSE CATEGORY
# ============================================================


def seed_categories():
    print("Seeding course categories...")

    names = [
        "Tiếng Anh",
        "IELTS",
        "Tiếng Nhật",
        "Tiếng Hàn",
        "Giao tiếp",
        "Luyện thi",
        "Cho người mới bắt đầu",
    ]

    categories = []

    for name in names:
        category = Category.query.filter_by(name=name).first()

        if not category:
            category = Category(name=name)
            db.session.add(category)
            db.session.flush()

        categories.append(category)

    db.session.commit()

    return categories


# ============================================================
# COURSES
# ============================================================


def seed_courses(teachers, categories):
    print("Seeding courses...")

    cate = {c.name: c for c in categories}

    course_data = [
        {
            "name": "Tiếng Anh Giao Tiếp Cơ Bản",
            "description": "Khóa học dành cho người mới bắt đầu học tiếng Anh giao tiếp.",
            "price": 2500000,
            "level": CourseLevel.BASIC,
            "teacher": teachers[0],
            "categories": [
                cate["Tiếng Anh"],
                cate["Giao tiếp"],
                cate["Cho người mới bắt đầu"],
            ],
        },
        {
            "name": "Tiếng Anh Giao Tiếp Trung Cấp",
            "description": "Phát triển khả năng giao tiếp tiếng Anh trong các tình huống thực tế.",
            "price": 3000000,
            "level": CourseLevel.INTERMEDIATE,
            "teacher": teachers[0],
            "categories": [
                cate["Tiếng Anh"],
                cate["Giao tiếp"],
            ],
        },
        {
            "name": "IELTS Foundation",
            "description": "Nền tảng IELTS dành cho người mới bắt đầu luyện thi.",
            "price": 3500000,
            "level": CourseLevel.BASIC,
            "teacher": teachers[1],
            "categories": [
                cate["Tiếng Anh"],
                cate["IELTS"],
                cate["Luyện thi"],
            ],
        },
        {
            "name": "IELTS 6.5+",
            "description": "Khóa luyện IELTS nâng cao hướng tới band điểm 6.5 trở lên.",
            "price": 4500000,
            "level": CourseLevel.ADVANCED,
            "teacher": teachers[1],
            "categories": [
                cate["Tiếng Anh"],
                cate["IELTS"],
                cate["Luyện thi"],
            ],
        },
        {
            "name": "Tiếng Nhật N5",
            "description": "Khóa học tiếng Nhật trình độ N5.",
            "price": 2800000,
            "level": CourseLevel.BASIC,
            "teacher": teachers[2],
            "categories": [
                cate["Tiếng Nhật"],
                cate["Cho người mới bắt đầu"],
            ],
        },
        {
            "name": "Tiếng Nhật N4",
            "description": "Khóa học tiếng Nhật trình độ N4.",
            "price": 3200000,
            "level": CourseLevel.INTERMEDIATE,
            "teacher": teachers[2],
            "categories": [
                cate["Tiếng Nhật"],
            ],
        },
    ]

    courses = []

    for data in course_data:
        course = Course.query.filter_by(name=data["name"]).first()

        if not course:
            course = Course(
                name=data["name"],
                description=data["description"],
                price=data["price"],
                level=data["level"],
                teacher_id=data["teacher"].id,
                image="",
                is_sale=True,
                activate=True,
            )

            db.session.add(course)
            db.session.flush()

            for category in data["categories"]:
                db.session.add(
                    CourseCategory(
                        course_id=course.id,
                        category_id=category.id,
                    )
                )

        courses.append(course)

    db.session.commit()

    return courses


# ============================================================
# CHAPTER + LESSON
# ============================================================


def seed_chapters_lessons(courses):
    print("Seeding chapters and lessons...")

    for course in courses:
        existing = Chapter.query.filter_by(course_id=course.id).count()

        if existing > 0:
            continue

        chapter1 = Chapter(
            name="Chương 1: Làm quen",
            description="Những kiến thức cơ bản đầu tiên.",
            order=1,
            course_id=course.id,
        )

        chapter2 = Chapter(
            name="Chương 2: Kiến thức nền tảng",
            description="Các kiến thức quan trọng của khóa học.",
            order=2,
            course_id=course.id,
        )

        chapter3 = Chapter(
            name="Chương 3: Luyện tập",
            description="Luyện tập và áp dụng kiến thức.",
            order=3,
            course_id=course.id,
        )

        db.session.add_all(
            [
                chapter1,
                chapter2,
                chapter3,
            ]
        )

        db.session.flush()

        lessons = [
            Lesson(
                name="Giới thiệu khóa học",
                description="Giới thiệu nội dung khóa học.",
                type=LessonType.VIDEO,
                chapter_id=chapter1.id,
            ),
            Lesson(
                name="Từ vựng cơ bản",
                description="Các từ vựng thường gặp.",
                type=LessonType.VIDEO,
                chapter_id=chapter1.id,
            ),
            Lesson(
                name="Ngữ pháp nền tảng",
                description="Các cấu trúc ngữ pháp cơ bản.",
                type=LessonType.DOCUMENT,
                chapter_id=chapter2.id,
            ),
            Lesson(
                name="Bài tập thực hành",
                description="Bài tập áp dụng kiến thức.",
                type=LessonType.VIDEO,
                chapter_id=chapter2.id,
            ),
            Lesson(
                name="Luyện tập tổng hợp",
                description="Ôn tập kiến thức toàn chương.",
                type=LessonType.DOCUMENT,
                chapter_id=chapter3.id,
            ),
        ]

        db.session.add_all(lessons)
        db.session.flush()

        for lesson in lessons:
            if lesson.type == LessonType.VIDEO:
                db.session.add(
                    VideoContent(
                        lesson_id=lesson.id,
                        video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        duration=600,
                    )
                )

            elif lesson.type == LessonType.DOCUMENT:
                db.session.add(
                    DocContent(
                        lesson_id=lesson.id,
                        content_text="Tài liệu học tập mẫu.",
                        file_url="",
                        file_ext="pdf",
                    )
                )

    db.session.commit()


# ============================================================
# COURSE OUTCOME
# ============================================================


def seed_outcomes(courses):
    print("Seeding course outcomes...")

    for course in courses:
        if course.outcomes:
            continue

        outcomes = [
            "Nắm được kiến thức nền tảng của khóa học.",
            "Có thể áp dụng kiến thức vào tình huống thực tế.",
            "Cải thiện khả năng tự học và luyện tập.",
        ]

        for content in outcomes:
            db.session.add(
                CourseOutcome(
                    content=content,
                    course_id=course.id,
                )
            )

    db.session.commit()


# ============================================================
# TEST + QUESTIONS + ANSWERS
# ============================================================


def seed_tests(courses):
    print("Seeding tests...")

    for course in courses:
        if course.tests:
            continue

        chapters = course.chapters

        if not chapters:
            continue

        test1 = Test(
            name="Kiểm tra Chương 1",
            course_id=course.id,
            chapter_id=chapters[0].id,
            duration=20,
            max_attempts=3,
            pass_score=5,
        )

        test2 = Test(
            name="Kiểm tra cuối khóa",
            course_id=course.id,
            chapter_id=chapters[2].id,
            duration=30,
            max_attempts=2,
            pass_score=6,
        )

        db.session.add_all([test1, test2])
        db.session.flush()

        # ----------------------------------------------------
        # TEST 1
        # ----------------------------------------------------

        q1 = Question(
            name="Câu hỏi 1",
            test_id=test1.id,
            content="Which word means 'xin chào'?",
        )

        q2 = Question(
            name="Câu hỏi 2",
            test_id=test1.id,
            content="Which sentence is correct?",
        )

        db.session.add_all([q1, q2])
        db.session.flush()

        db.session.add_all(
            [
                Answer(
                    question_id=q1.id,
                    content="Hello",
                    is_correct=True,
                ),
                Answer(
                    question_id=q1.id,
                    content="Goodbye",
                    is_correct=False,
                ),
                Answer(
                    question_id=q1.id,
                    content="Thanks",
                    is_correct=False,
                ),
                Answer(
                    question_id=q1.id,
                    content="Sorry",
                    is_correct=False,
                ),
                Answer(
                    question_id=q2.id,
                    content="I am a student.",
                    is_correct=True,
                ),
                Answer(
                    question_id=q2.id,
                    content="I student am.",
                    is_correct=False,
                ),
                Answer(
                    question_id=q2.id,
                    content="Am student I.",
                    is_correct=False,
                ),
                Answer(
                    question_id=q2.id,
                    content="Student I am.",
                    is_correct=False,
                ),
            ]
        )

        # ----------------------------------------------------
        # TEST 2
        # ----------------------------------------------------

        q3 = Question(
            name="Câu hỏi 1",
            test_id=test2.id,
            content="Which option is correct?",
        )

        q4 = Question(
            name="Câu hỏi 2",
            test_id=test2.id,
            content="Choose the correct answer.",
        )

        db.session.add_all([q3, q4])
        db.session.flush()

        db.session.add_all(
            [
                Answer(
                    question_id=q3.id,
                    content="Option A",
                    is_correct=True,
                ),
                Answer(
                    question_id=q3.id,
                    content="Option B",
                    is_correct=False,
                ),
                Answer(
                    question_id=q3.id,
                    content="Option C",
                    is_correct=False,
                ),
                Answer(
                    question_id=q3.id,
                    content="Option D",
                    is_correct=False,
                ),
                Answer(
                    question_id=q4.id,
                    content="Correct answer",
                    is_correct=True,
                ),
                Answer(
                    question_id=q4.id,
                    content="Wrong answer",
                    is_correct=False,
                ),
            ]
        )

    db.session.commit()


# ============================================================
# ENROLLMENT
# ============================================================


def seed_enrollments(users, courses):
    print("Seeding enrollments...")

    students = users["students"]

    # Student 1: đang học
    e1 = Enrollment.query.filter_by(
        user_id=students[0].id,
        course_id=courses[0].id,
    ).first()

    if not e1:
        e1 = Enrollment(
            user_id=students[0].id,
            course_id=courses[0].id,
            price=courses[0].price,
            progress=40,
            status=EnrollmentStatus.IN_PROGRESS,
        )
        db.session.add(e1)

    # Student 2: hoàn thành
    e2 = Enrollment.query.filter_by(
        user_id=students[1].id,
        course_id=courses[2].id,
    ).first()

    if not e2:
        e2 = Enrollment(
            user_id=students[1].id,
            course_id=courses[2].id,
            price=courses[2].price,
            progress=100,
            status=EnrollmentStatus.COMPLETED,
            completed_date=datetime.now() - timedelta(days=3),
        )
        db.session.add(e2)

    # Student 3: đang học
    e3 = Enrollment.query.filter_by(
        user_id=students[2].id,
        course_id=courses[1].id,
    ).first()

    if not e3:
        e3 = Enrollment(
            user_id=students[2].id,
            course_id=courses[1].id,
            price=courses[1].price,
            progress=20,
            status=EnrollmentStatus.IN_PROGRESS,
        )
        db.session.add(e3)

    # Student 4: failed
    e4 = Enrollment.query.filter_by(
        user_id=students[3].id,
        course_id=courses[3].id,
    ).first()

    if not e4:
        e4 = Enrollment(
            user_id=students[3].id,
            course_id=courses[3].id,
            price=courses[3].price,
            progress=100,
            status=EnrollmentStatus.FAILED,
        )
        db.session.add(e4)

    # Student 5: đang học
    e5 = Enrollment.query.filter_by(
        user_id=students[4].id,
        course_id=courses[4].id,
    ).first()

    if not e5:
        e5 = Enrollment(
            user_id=students[4].id,
            course_id=courses[4].id,
            price=courses[4].price,
            progress=60,
            status=EnrollmentStatus.IN_PROGRESS,
        )
        db.session.add(e5)

    db.session.commit()

    return [e1, e2, e3, e4, e5]


# ============================================================
# LESSON PROGRESS
# ============================================================


def seed_lesson_progress(enrollments):
    print("Seeding lesson progress...")

    for enrollment in enrollments:
        if not enrollment:
            continue

        lessons = [lesson for chapter in enrollment.course.chapters for lesson in chapter.lessons]

        if not lessons:
            continue

        # Chỉ đánh dấu một số bài đã hoàn thành
        number_done = max(1, len(lessons) // 2)

        for lesson in lessons[:number_done]:
            existed = LessonProgress.query.filter_by(
                enrollment_id=enrollment.id,
                lesson_id=lesson.id,
            ).first()

            if not existed:
                db.session.add(
                    LessonProgress(
                        enrollment_id=enrollment.id,
                        lesson_id=lesson.id,
                        is_completed=True,
                        completed_at=datetime.now() - timedelta(days=2),
                        last_watched_at=datetime.now() - timedelta(days=1),
                    )
                )

    db.session.commit()


# ============================================================
# SCORE
# ============================================================


def seed_scores(enrollments):
    print("Seeding scores...")

    for enrollment in enrollments:
        tests = enrollment.course.tests

        if not tests:
            continue

        # Student 2 hoàn thành -> điểm cao
        if enrollment.status == EnrollmentStatus.COMPLETED:
            for test in tests:
                existed = Score.query.filter_by(
                    enrollment_id=enrollment.id,
                    test_id=test.id,
                    attempt_number=1,
                ).first()

                if not existed:
                    db.session.add(
                        Score(
                            enrollment_id=enrollment.id,
                            test_id=test.id,
                            attempt_number=1,
                            score_value=8.5,
                            is_passed=True,
                            started_at=datetime.now() - timedelta(days=5),
                            completed_at=datetime.now() - timedelta(days=5),
                        )
                    )

        # Student failed -> có lịch sử làm bài
        elif enrollment.status == EnrollmentStatus.FAILED:
            test = tests[0]

            existed = Score.query.filter_by(
                enrollment_id=enrollment.id,
                test_id=test.id,
                attempt_number=1,
            ).first()

            if not existed:
                db.session.add(
                    Score(
                        enrollment_id=enrollment.id,
                        test_id=test.id,
                        attempt_number=1,
                        score_value=3,
                        is_passed=False,
                        started_at=datetime.now() - timedelta(days=3),
                        completed_at=datetime.now() - timedelta(days=3),
                    )
                )

    db.session.commit()


# ============================================================
# FORUM CATEGORY
# ============================================================


def seed_post_categories():
    print("Seeding post categories...")

    names = [
        "Hỏi đáp",
        "Chia sẻ kinh nghiệm",
        "Ngữ pháp",
        "Từ vựng",
        "IELTS",
        "Tiếng Nhật",
    ]

    categories = []

    for name in names:
        category = PostCate.query.filter_by(name=name).first()

        if not category:
            category = PostCate(
                name=name,
                description=f"Chuyên mục {name}",
            )
            db.session.add(category)
            db.session.flush()

        categories.append(category)

    db.session.commit()

    return categories


# ============================================================
# POSTS + COMMENTS + REACTIONS
# ============================================================


def seed_forum(users, post_categories):
    print("Seeding forum...")

    students = users["students"]
    teacher = users["teachers"][0]

    post1 = Post.query.filter_by(title="Làm thế nào để cải thiện kỹ năng Speaking?").first()

    if not post1:
        post1 = Post(
            title="Làm thế nào để cải thiện kỹ năng Speaking?",
            content=(
                "Mình đang học tiếng Anh nhưng cảm thấy kỹ năng Speaking "
                "còn khá yếu. Mọi người có phương pháp luyện tập nào hiệu quả không?"
            ),
            user_id=students[0].id,
            view_count=120,
            is_solved=True,
        )

        db.session.add(post1)
        db.session.flush()

        post1.categories.append(post_categories[0])
        post1.categories.append(post_categories[1])

    post2 = Post.query.filter_by(title="Cách học từ vựng tiếng Anh hiệu quả").first()

    if not post2:
        post2 = Post(
            title="Cách học từ vựng tiếng Anh hiệu quả",
            content=(
                "Mọi người thường học từ vựng bằng phương pháp nào? "
                "Mình muốn tìm một phương pháp có thể duy trì lâu dài."
            ),
            user_id=students[1].id,
            view_count=85,
            is_solved=False,
        )

        db.session.add(post2)
        db.session.flush()

        post2.categories.append(post_categories[3])

    post3 = Post.query.filter_by(title="Kinh nghiệm luyện IELTS Listening").first()

    if not post3:
        post3 = Post(
            title="Kinh nghiệm luyện IELTS Listening",
            content=(
                "Mình đang luyện IELTS và muốn cải thiện Listening. "
                "Các bạn có thể chia sẻ tài liệu hoặc phương pháp học không?"
            ),
            user_id=students[2].id,
            view_count=200,
            is_solved=False,
        )

        db.session.add(post3)
        db.session.flush()

        post3.categories.append(post_categories[4])

    db.session.commit()

    # --------------------------------------------------------
    # COMMENTS
    # --------------------------------------------------------

    comment = Comment.query.filter_by(
        post_id=post1.id,
        user_id=teacher.id,
    ).first()

    if not comment:
        comment = Comment(
            content=("Bạn có thể luyện Speaking mỗi ngày bằng cách tự nói về các chủ đề quen thuộc và ghi âm lại."),
            post_id=post1.id,
            user_id=teacher.id,
            is_accepted=True,
        )

        db.session.add(comment)
        db.session.flush()

    reply = Comment.query.filter_by(
        post_id=post1.id,
        user_id=students[1].id,
        parent_comment_id=comment.id,
    ).first()

    if not reply:
        reply = Comment(
            content="Cảm ơn bạn, mình sẽ thử phương pháp này.",
            post_id=post1.id,
            user_id=students[1].id,
            parent_comment_id=comment.id,
        )

        db.session.add(reply)

    db.session.commit()

    # --------------------------------------------------------
    # POST REACTIONS
    # --------------------------------------------------------

    reactions = [
        (post1, students[0], VoteType.UP),
        (post1, students[1], VoteType.UP),
        (post1, teacher, VoteType.UP),
        (post2, students[0], VoteType.UP),
        (post2, students[2], VoteType.DOWN),
        (post3, students[1], VoteType.UP),
        (post3, students[3], VoteType.UP),
    ]

    for post, user, vote_type in reactions:
        existed = ReactionPost.query.filter_by(
            post_id=post.id,
            user_id=user.id,
        ).first()

        if not existed:
            db.session.add(
                ReactionPost(
                    post_id=post.id,
                    user_id=user.id,
                    vote_type=vote_type,
                )
            )

    # --------------------------------------------------------
    # COMMENT REACTION
    # --------------------------------------------------------

    existed = ReactionComment.query.filter_by(
        comment_id=comment.id,
        user_id=students[0].id,
    ).first()

    if not existed:
        db.session.add(
            ReactionComment(
                comment_id=comment.id,
                user_id=students[0].id,
                vote_type=VoteType.UP,
            )
        )

    db.session.commit()


# ============================================================
# CHAT
# ============================================================


def seed_chat(users):
    print("Seeding chat...")

    students = users["students"]
    teachers = users["teachers"]

    # --------------------------------------------------------
    # PRIVATE CHAT
    # --------------------------------------------------------

    conversation = Conversation.query.filter_by(title="Chat Student 1 - Teacher 1").first()

    if not conversation:
        conversation = Conversation(
            title="Chat Student 1 - Teacher 1",
            image="",
            is_group=False,
        )

        db.session.add(conversation)
        db.session.flush()

        db.session.add_all(
            [
                ConversationMember(
                    conversation_id=conversation.id,
                    user_id=students[0].id,
                ),
                ConversationMember(
                    conversation_id=conversation.id,
                    user_id=teachers[0].id,
                ),
            ]
        )

        db.session.flush()

        message1 = Message(
            content="Em chào cô, em muốn hỏi về bài học hôm nay.",
            conversation_id=conversation.id,
            sender_id=students[0].id,
        )

        message2 = Message(
            content="Chào em, em cứ hỏi nhé.",
            conversation_id=conversation.id,
            sender_id=teachers[0].id,
        )

        message3 = Message(
            content="Em chưa hiểu phần ngữ pháp ở chương 2.",
            conversation_id=conversation.id,
            sender_id=students[0].id,
        )

        db.session.add_all(
            [
                message1,
                message2,
                message3,
            ]
        )

        db.session.flush()

        db.session.add(
            MessageReaction(
                message_id=message2.id,
                user_id=students[0].id,
                emoji="👍",
            )
        )

    # --------------------------------------------------------
    # GROUP CHAT
    # --------------------------------------------------------

    group = Conversation.query.filter_by(
        title="Nhóm học tiếng Anh",
        is_group=True,
    ).first()

    if not group:
        group = Conversation(
            title="Nhóm học tiếng Anh",
            image="",
            is_group=True,
        )

        db.session.add(group)
        db.session.flush()

        members = [
            students[0],
            students[1],
            students[2],
            students[3],
            teachers[0],
        ]

        for user in members:
            db.session.add(
                ConversationMember(
                    conversation_id=group.id,
                    user_id=user.id,
                )
            )

        db.session.flush()

        messages = [
            ("Mọi người hôm nay học chương mấy rồi?", students[0]),
            ("Mình đang học chương 2.", students[1]),
            ("Mình cũng vậy.", students[2]),
            ("Có ai làm bài test chưa?", students[3]),
            ("Nếu gặp khó khăn thì mọi người cứ hỏi nhé.", teachers[0]),
        ]

        for content, user in messages:
            db.session.add(
                Message(
                    content=content,
                    conversation_id=group.id,
                    sender_id=user.id,
                )
            )

    db.session.commit()


# ============================================================
# TEACHER APPLICATION
# ============================================================


def seed_teacher_applications(users):
    print("Seeding teacher applications...")

    students = users["students"]
    admin = users["admin"]

    applications = [
        {
            "user": students[0],
            "status": ApplicationStatus.PENDING,
            "workplace": "ABC English Center",
            "degree": "Cử nhân",
            "major": "Ngôn ngữ Anh",
            "bio": "Có kinh nghiệm giảng dạy tiếng Anh.",
            "expertise": "Speaking, Grammar",
            "experience": "2 năm",
            "teach_style": "Thực hành",
        },
        {
            "user": students[1],
            "status": ApplicationStatus.APPROVED,
            "workplace": "XYZ Language Center",
            "degree": "Cử nhân",
            "major": "Ngôn ngữ Anh",
            "bio": "Giảng viên tiếng Anh.",
            "expertise": "IELTS",
            "experience": "3 năm",
            "teach_style": "Tương tác",
            "reviewed_by": admin.id,
            "reviewed_at": datetime.now() - timedelta(days=5),
        },
        {
            "user": students[2],
            "status": ApplicationStatus.REJECTED,
            "workplace": "Language Center",
            "degree": "Cử nhân",
            "major": "Ngôn ngữ",
            "bio": "Ứng tuyển giảng viên.",
            "expertise": "Grammar",
            "experience": "1 năm",
            "teach_style": "Truyền thống",
            "reject_reason": "Hồ sơ chưa đáp ứng yêu cầu.",
            "reviewed_by": admin.id,
            "reviewed_at": datetime.now() - timedelta(days=10),
        },
    ]

    for data in applications:
        existed = TeacherApplication.query.filter_by(user_id=data["user"].id).first()

        if existed:
            continue

        application = TeacherApplication(
            user_id=data["user"].id,
            workplace=data["workplace"],
            degree=data["degree"],
            major=data["major"],
            bio=data["bio"],
            expertise=data["expertise"],
            experience=data["experience"],
            teach_style=data["teach_style"],
            status=data["status"],
            reject_reason=data.get("reject_reason"),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=data.get("reviewed_at"),
        )

        db.session.add(application)

    db.session.commit()


# ============================================================
# PAYMENT
# ============================================================


def seed_payments(users, courses):
    print("Seeding payments...")

    students = users["students"]

    payments = [
        {
            "user": students[0],
            "course": courses[0],
            "amount": courses[0].price,
            "status": PaymentStatus.SUCCESS,
            "order_id": "ORDER-SEED-0001",
            "request_id": "REQ-SEED-0001",
            "momo_trans_id": "MOMO-SEED-0001",
            "pay_type": "MOMO",
            "paid_at": datetime.now() - timedelta(days=10),
        },
        {
            "user": students[1],
            "course": courses[2],
            "amount": courses[2].price,
            "status": PaymentStatus.SUCCESS,
            "order_id": "ORDER-SEED-0002",
            "request_id": "REQ-SEED-0002",
            "momo_trans_id": "MOMO-SEED-0002",
            "pay_type": "MOMO",
            "paid_at": datetime.now() - timedelta(days=15),
        },
        {
            "user": students[2],
            "course": courses[1],
            "amount": courses[1].price,
            "status": PaymentStatus.PENDING,
            "order_id": "ORDER-SEED-0003",
            "request_id": "REQ-SEED-0003",
            "momo_trans_id": None,
            "pay_type": "MOMO",
            "paid_at": None,
        },
        {
            "user": students[3],
            "course": courses[3],
            "amount": courses[3].price,
            "status": PaymentStatus.FAILED,
            "order_id": "ORDER-SEED-0004",
            "request_id": "REQ-SEED-0004",
            "momo_trans_id": None,
            "pay_type": "MOMO",
            "paid_at": None,
        },
    ]

    for data in payments:
        existed = Payment.query.filter_by(order_id=data["order_id"]).first()

        if existed:
            continue

        payment = Payment(
            user_id=data["user"].id,
            course_id=data["course"].id,
            order_id=data["order_id"],
            request_id=data["request_id"],
            momo_trans_id=data["momo_trans_id"],
            amount=data["amount"],
            status=data["status"],
            pay_type=data["pay_type"],
            paid_at=data["paid_at"],
            invoice_sent=data["status"] == PaymentStatus.SUCCESS,
        )

        db.session.add(payment)

    db.session.commit()


# ============================================================
# MAIN
# ============================================================


def seed_database():
    print("=" * 60)
    print("START SEED DATABASE")
    print("=" * 60)

    users = seed_users()

    teachers = seed_admin_teacher(users)

    categories = seed_categories()

    courses = seed_courses(
        teachers,
        categories,
    )

    seed_chapters_lessons(courses)

    # Refresh relationship data
    db.session.expire_all()

    seed_outcomes(courses)

    seed_tests(courses)

    db.session.expire_all()

    enrollments = seed_enrollments(
        users,
        courses,
    )

    db.session.expire_all()

    seed_lesson_progress(enrollments)

    seed_scores(enrollments)

    post_categories = seed_post_categories()

    seed_forum(
        users,
        post_categories,
    )

    seed_chat(users)

    seed_teacher_applications(users)

    seed_payments(
        users,
        courses,
    )

    db.session.commit()

    print("=" * 60)
    print("SEED DATABASE SUCCESS")
    print("=" * 60)

    print("\nLOGIN ACCOUNTS")
    print("-" * 60)
    print("Admin:")
    print("  username: admin")
    print("  password: 123456")

    print("\nTeachers:")
    print("  teacher01 / 123456")
    print("  teacher02 / 123456")
    print("  teacher03 / 123456")

    print("\nStudents:")
    print("  student01 / 123456")
    print("  student02 / 123456")
    print("  student03 / 123456")
    print("  student04 / 123456")
    print("  student05 / 123456")

    print("=" * 60)


if __name__ == "__main__":
    with app.app_context():
        seed_database()
