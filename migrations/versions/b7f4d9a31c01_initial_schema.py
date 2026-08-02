from alembic import op
import sqlalchemy as sa


revision = "b7f4d9a31c01"
down_revision = None
branch_labels = None
depends_on = None


def _base_columns():
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.Column("updated_date", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
    ]


def upgrade():
    op.create_table(
        "user",
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=True),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.String(length=255), nullable=True),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "category",
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "post_cate",
        sa.Column("description", sa.String(length=255), nullable=True),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "teacher",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "course",
        sa.Column("is_sale", sa.Boolean(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("activate", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("BASIC", "INTERMEDIATE", "ADVANCED", name="courselevel"),
            nullable=False,
        ),
        *_base_columns(),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "teacher_application",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workplace", sa.String(length=255), nullable=True),
        sa.Column("degree", sa.String(length=50), nullable=True),
        sa.Column("major", sa.String(length=255), nullable=False),
        sa.Column("bio", sa.String(length=500), nullable=False),
        sa.Column("expertise", sa.String(length=500), nullable=True),
        sa.Column("experience", sa.String(length=50), nullable=True),
        sa.Column("teach_style", sa.String(length=20), nullable=True),
        sa.Column("linkedin", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("id_card_file", sa.String(length=500), nullable=False),
        sa.Column("degree_file", sa.String(length=500), nullable=False),
        sa.Column("cv_file", sa.String(length=500), nullable=False),
        sa.Column("extra_cert_file", sa.String(length=500), nullable=True),
        sa.Column("video_file", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="applicationstatus"),
            nullable=False,
        ),
        sa.Column("reject_reason", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["reviewed_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chapter",
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lesson",
        sa.Column(
            "type",
            sa.Enum("VIDEO", "NONE", "DOCUMENT", name="lessontype"),
            nullable=False,
        ),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapter.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "video_content",
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("video_url", sa.String(length=500), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lesson.id"]),
        sa.PrimaryKeyConstraint("lesson_id"),
    )

    op.create_table(
        "doc_content",
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("file_ext", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lesson.id"]),
        sa.PrimaryKeyConstraint("lesson_id"),
    )

    op.create_table(
        "course_outcome",
        sa.Column("content", sa.String(length=255), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course_category",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["course.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("course_id", "category_id"),
    )

    op.create_table(
        "enrollment",
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("completed_date", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("IN_PROGRESS", "COMPLETED", "FAILED", name="enrollmentstatus"),
            nullable=False,
        ),
        sa.Column("created_date", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("created_date", "user_id", "course_id"),
    )

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("last_watched_at", sa.DateTime(), nullable=True),
        sa.Column("enrollment_created_date", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["enrollment_created_date", "user_id", "course_id"],
            [
                "enrollment.created_date",
                "enrollment.user_id",
                "enrollment.course_id",
            ],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lesson.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "course_id",
            "enrollment_created_date",
            "lesson_id",
            name="uix_progress_per_attempt",
        ),
    )

    op.create_table(
        "test",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapter.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "question",
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["test_id"], ["test.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "answer",
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(length=500), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["question_id"], ["question.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "score",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=True),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("is_passed", sa.Boolean(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("enrollment_created_date", sa.DateTime(), nullable=False),

        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["test_id"], ["test.id"]),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payment",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(length=50), nullable=False),
        sa.Column("request_id", sa.String(length=50), nullable=False),
        sa.Column("momo_trans_id", sa.String(length=50), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "SUCCESS",
                "FAILED",
                "CANCELLED",
                name="paymentstatus",
            ),
            nullable=False,
        ),
        sa.Column("pay_type", sa.String(length=50), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("invoice_sent", sa.Boolean(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )

    op.create_table(
        "post",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("is_solved", sa.Boolean(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "post_category",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["post_cate.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id", "category_id"),
    )

    op.create_table(
        "comment",
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_accepted", sa.Boolean(), nullable=True),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parent_comment_id", sa.Integer(), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["comment.id"]),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reaction_post",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vote_type", sa.Enum("UP", "DOWN", name="votetype"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reaction_comment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vote_type", sa.Enum("UP", "DOWN", name="votetype"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["comment_id"], ["comment.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("reaction_comment")
    op.drop_table("reaction_post")
    op.drop_table("comment")
    op.drop_table("post_category")
    op.drop_table("post")
    op.drop_table("payment")
    op.drop_table("score")
    op.drop_table("answer")
    op.drop_table("question")
    op.drop_table("test")
    op.drop_table("lesson_progress")
    op.drop_table("enrollment")
    op.drop_table("course_category")
    op.drop_table("course_outcome")
    op.drop_table("doc_content")
    op.drop_table("video_content")
    op.drop_table("lesson")
    op.drop_table("chapter")
    op.drop_table("teacher_application")
    op.drop_table("course")
    op.drop_table("teacher")
    op.drop_table("post_cate")
    op.drop_table("category")
    op.drop_table("user")