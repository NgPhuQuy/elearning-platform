# E-Learning Platform

Nền tảng học trực tuyến xây dựng bằng **Flask + MySQL**: giáo viên tạo và bán khóa học, học viên đăng ký, học theo từng bài, làm bài kiểm tra và nhận chứng chỉ. Có diễn đàn hỏi đáp, chat thời gian thực và thanh toán MoMo / VNPay.

Dự án gồm cả phần ứng dụng lẫn quy trình vận hành: Docker, CI/CD bằng GitHub Actions, image trên GHCR, deploy staging/production lên Render.

## Tính năng

| Nhóm | Mô tả |
|---|---|
| Tài khoản | Đăng ký, đăng nhập, đăng nhập bằng Google (OAuth), đổi thông tin, đổi mật khẩu, ảnh đại diện (Cloudinary) |
| Phân quyền | 3 vai trò: **User** (học viên), **Teacher**, **Admin**. Học viên nộp đơn đăng ký làm giáo viên và chờ admin duyệt (giới hạn gửi lại 14 ngày) |
| Khóa học | Giáo viên tạo, sửa, xóa, kích hoạt khóa học; chia chương, bài học (video / tài liệu); phân loại theo danh mục và cấp độ |
| Học tập | Đăng ký khóa học, học theo bài, đánh dấu hoàn thành, theo dõi tiến độ, trang "Khóa học của tôi" |
| Kiểm tra | Bài test trắc nghiệm gắn với khóa học, chấm điểm tự động, điểm đạt cấu hình được, giáo viên xem điểm từng học viên |
| Chứng chỉ | Cấp chứng chỉ khi hoàn thành khóa học và đạt bài test, xem và lưu trong "Chứng chỉ của tôi" |
| Diễn đàn | Đặt câu hỏi, trả lời, bình luận lồng nhau, upvote / downvote, đánh dấu câu trả lời được chấp nhận, lọc và tìm kiếm |
| Chat | Chat thời gian thực bằng Socket.IO: gửi / sửa / xóa tin nhắn, thả cảm xúc, đánh dấu đã đọc, tìm người để nhắn |
| Thanh toán | Thanh toán khóa học qua **MoMo** và **VNPay** (sandbox), xử lý IPN, lịch sử thanh toán |
| Quản trị | Trang admin (Flask-Admin) quản lý người dùng, khóa học, bài học, danh mục, diễn đàn, đơn đăng ký giáo viên |
| Email | Gửi email qua SMTP |

## Công nghệ

- **Backend:** Python 3.12, Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-Login, Flask-SocketIO, Flask-Admin, Authlib
- **Cơ sở dữ liệu:** MySQL 8
- **Frontend:** Jinja2 template, CSS, JavaScript thuần
- **Dịch vụ ngoài:** Cloudinary (lưu ảnh/tệp), Google OAuth, MoMo, VNPay, SMTP
- **Vận hành:** Docker, Docker Compose, Gunicorn (gevent-websocket), GitHub Actions, GHCR, Render
- **Chất lượng:** pytest, pytest-cov, Ruff (lint + format)

## Kiến trúc

Ứng dụng tách thành các tầng để dễ bảo trì và kiểm thử:

```
app/
├── controllers/   # Route Flask / Socket.IO: nhận request, trả response
├── services/      # Logic nghiệp vụ (học tập, thanh toán, chat, diễn đàn...)
├── dao/           # Truy vấn cơ sở dữ liệu
├── models/        # SQLAlchemy models
├── templates/     # Giao diện Jinja2
├── static/        # CSS, JS
├── admin.py       # Trang quản trị
├── momo.py, vnpay.py, mailer.py
└── seed.py        # Dữ liệu mẫu
migrations/        # Alembic migrations
scripts/           # Script khởi động, tạo schema, smoke test, deploy
tests/             # unit/ và integration/
```

Luồng xử lý: `controller → service → dao → model`.

## Chạy trên máy (Docker, khuyến nghị)

Yêu cầu: Docker và Docker Compose.

```bash
# 1. Clone
git clone https://github.com/NgPhuQuy/elearning-platform.git
cd elearning-platform

# 2. Tạo file môi trường
cp .env.example .env
```

Mở `.env` và chỉnh tối thiểu 2 biến sau cho khớp với database trong `compose.yaml`:

```env
SECRET_KEY=chuoi-bi-mat-ngau-nhien
DB_URI=mysql+pymysql://elearning:elearning@db:3306/elearning?charset=utf8mb4
```

Các biến Google, Cloudinary, MoMo, VNPay, SMTP có thể để trống nếu chưa dùng tính năng tương ứng.

```bash
# 3. Khởi động app và MySQL
docker compose up --build -d

# 4. Tạo bảng (chạy migration)
docker compose run --rm app python -m scripts.create_schema

# 5. (Tùy chọn) nạp dữ liệu mẫu
docker compose run --rm app python -m app.seed
```

Mở http://localhost:8000. Kiểm tra sức khỏe: http://localhost:8000/healthz

Dừng và xóa container: `docker compose down` (thêm `-v` nếu muốn xóa luôn dữ liệu MySQL).

## Chạy không dùng Docker

Yêu cầu: Python 3.12 và một MySQL đang chạy.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # trỏ DB_URI tới MySQL của bạn, host là localhost
flask --app app db upgrade       # tạo bảng
python -m app.seed               # (tùy chọn) dữ liệu mẫu
python -m app.index              # chạy tại http://localhost:5000
```

## Demo

Sau khi chạy `python -m app.seed`, đăng nhập bằng các tài khoản mẫu (mật khẩu chung: `11111111`):

| Vai trò | Username |
|---|---|
| Admin | `admin` |
| Giáo viên | `teacher01`, `teacher02`, `teacher03` |
| Học viên | `student01` ... `student05` |

Gợi ý các luồng nên thử:

1. **Học viên:** đăng nhập `student01` → xem danh sách khóa học → đăng ký / thanh toán → học bài → làm bài test → xem chứng chỉ.
2. **Giáo viên:** đăng nhập `teacher01` → "Quản lý khóa học" → tạo khóa học, thêm chương và bài học, tạo bài test và câu hỏi → xem điểm học viên.
3. **Diễn đàn:** đặt câu hỏi, trả lời bằng tài khoản khác, upvote và chấp nhận câu trả lời.
4. **Chat:** mở 2 trình duyệt (hoặc 1 cửa sổ ẩn danh) đăng nhập 2 tài khoản khác nhau và nhắn tin qua lại để thấy cập nhật tức thì.
5. **Admin:** đăng nhập tại `/login-admin` → vào trang quản trị, duyệt đơn đăng ký giáo viên.

## Kiểm thử và chất lượng code

```bash
pip install -r requirements-test.txt

pytest                      # chạy toàn bộ test
pytest --cov=app            # kèm độ phủ
ruff check .                # lint
ruff format --check .       # kiểm tra định dạng
```

Test gồm `tests/unit` (chấm điểm bài test, tiến độ học, thanh toán, VNPay, phân quyền, diễn đàn...) và `tests/integration` (luồng đăng nhập, đăng ký khóa học, thanh toán, chat, phân quyền khóa học, render template, smoke test hạ tầng).

## CI/CD và triển khai

```
feature branch ──PR──► dev ──PR──► main
                         │            │
                         ▼            ▼
                        CI           CI ──► CD (build + push image lên GHCR)
                                                    │
                                                    ├─► Staging (Render, tự động)
                                                    └─► Production (chạy tay, deploy theo digest)
```

- **CI** (`.github/workflows/ci.yml`): chạy khi có PR hoặc push vào `dev` / `main`. Gồm kiểm tra nguồn PR (PR vào `main` chỉ được từ `dev`), lint + format bằng Ruff, chạy migration, chạy test kèm coverage, build Docker image và chạy smoke test container.
- **CD** (`.github/workflows/cd.yml`): build image, push lên GHCR, xác minh manifest và ghi **digest bất biến** (`ghcr.io/<owner>/<repo>@sha256:...`) vào summary. Sau đó kích hoạt deploy staging trên Render.
- **Production** (`.github/workflows/deploy-production.yml`): chạy thủ công với digest image đã kiểm chứng trên staging, có các bước xác nhận (đã verify staging, đã có backup database, gõ `PRODUCTION`). Hỗ trợ cả phát hành bản mới lẫn rollback về image cũ.
- Triển khai bằng Docker Compose: `compose.production.yaml` và `scripts/deploy_release.sh` (pull image, khởi động DB, migrate, khởi động app, smoke test).

## Biến môi trường

Xem đầy đủ trong `.env.example`. Các nhóm chính:

| Biến | Công dụng |
|---|---|
| `SECRET_KEY`, `DB_URI` | Bắt buộc. Khóa session và chuỗi kết nối MySQL |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Đăng nhập Google |
| `CLOUD_NAME`, `CLOUD_KEY`, `CLOUD_SECRET` | Cloudinary |
| `MOMO_*`, `VNPAY_*` | Cổng thanh toán |
| `MAIL_*` | SMTP gửi email |
| `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT` | Cấu hình Gunicorn |
| `MYSQL_*`, `APP_IMAGE`, `APP_PORT` | Dùng cho `compose.production.yaml` |

> **Bảo mật:** không commit file `.env`. Các giá trị trong `.env.example` chỉ là ví dụ.