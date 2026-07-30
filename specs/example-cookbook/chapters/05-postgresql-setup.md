# Cài đặt và kết nối PostgreSQL {#chapter-postgresql-setup}

## Mục tiêu

Hiểu PostgreSQL đang chạy ở đâu, đăng nhập bằng identity nào và phân biệt lỗi
service, network, role với database. Đây là nền để mọi chương SQL sau có thể
thực hành an toàn.

## Mental model

```text
PostgreSQL cluster (một server process)
  +-- role: postgres          quản trị
  +-- role: ai_learn_app      ứng dụng
  +-- database: postgres      maintenance
  +-- database: ai_learn_jlpt
        +-- schema: public
              +-- users
              +-- sessions
              +-- ...
```

**Role** là identity/quyền trong PostgreSQL. **Database** là vùng dữ liệu có
connection boundary. **Schema** là namespace bên trong database. **Table** giữ
row. Một cluster có nhiều database; một connection chỉ làm việc trong một
database tại một thời điểm.

## Cài cho development

Trên macOS với Homebrew:

```bash
brew install postgresql@16
brew services start postgresql@16
psql --version
pg_isready
```

Trên Ubuntu VPS:

```bash
sudo apt update
sudo apt install postgresql postgresql-client
sudo systemctl enable --now postgresql
sudo systemctl status postgresql --no-pager
```

Docker phù hợp cho môi trường lab tạm thời nhưng thêm volume/network lifecycle.
Nếu đã có PostgreSQL native ổn định, không cần thêm container chỉ để “chuẩn hoá”.

## Tạo role và database

Production nên dùng role riêng, không để ứng dụng kết nối bằng superuser:

```bash
sudo -u postgres createuser --no-superuser --no-createdb --no-createrole ai_learn_app
sudo -u postgres createdb --owner=ai_learn_app ai_learn_jlpt
sudo -u postgres psql -c "ALTER ROLE ai_learn_app PASSWORD 'REPLACE_ME';"
```

Không đặt password thật trực tiếp trong shell history. Script provision của dự
án tạo password ngẫu nhiên và ghi environment file quyền hạn chế.

Connection string có cấu trúc:

```text
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Ví dụ local không có credential thật:

```dotenv
DATABASE_URL=postgresql://localhost:5432/ai_learn_jlpt
```

::: {.current}
`src/lib/config.js` fail fast nếu thiếu `DATABASE_URL`; `src/lib/database.js`
tạo `pg.Pool`. Server query `SELECT 1` trước khi listen nên cấu hình DB sai không
tạo ra một process “có vẻ chạy” nhưng vô dụng.
:::

## Làm việc với `psql`

```bash
psql "$DATABASE_URL"
```

Các meta-command chạy bên trong `psql`:

| Lệnh | Ý nghĩa |
|---|---|
| `\conninfo` | Connection hiện tại |
| `\l` | Danh sách database |
| `\du` | Role và attribute |
| `\c db_name` | Đổi database |
| `\dn` | Danh sách schema |
| `\dt` | Table trong search path |
| `\d users` | Mô tả table/index/constraint |
| `\x` | Bật/tắt expanded output |
| `\timing` | Hiện thời gian query |
| `\q` | Thoát |

Với automation, dùng `-X` để không đọc `.psqlrc`, `-A -t` để output máy đọc và
`-v ON_ERROR_STOP=1` để dừng khi SQL lỗi.

## Lab: database cô lập

::: {.lab}
**Preflight:** xác nhận đang ở máy local và user có quyền tạo database.

```bash
createdb ai_learn_jlpt_lab
export LAB_DATABASE_URL=postgresql://localhost:5432/ai_learn_jlpt_lab
psql "$LAB_DATABASE_URL" -Xv ON_ERROR_STOP=1 -c \
  "SELECT current_database(), current_user, version();"
```

Apply schema của dự án:

```bash
DATABASE_URL="$LAB_DATABASE_URL" npm run db:migrate
psql "$LAB_DATABASE_URL" -Xc '\dt'
```

Cleanup sau khi thoát mọi connection:

```bash
dropdb ai_learn_jlpt_lab
unset LAB_DATABASE_URL
```
:::

::: {.warning}
Trước `dropdb`, in chính xác target: `printf '%s\n' "$LAB_DATABASE_URL"`. Script
tự động nên từ chối nếu tên database không chứa `lab` hoặc `test`.
:::

## Chẩn đoán theo lớp

| Lỗi | Kiểm tra |
|---|---|
| `connection refused` | Service, host, port, firewall |
| `password authentication failed` | Role/password/`pg_hba.conf` |
| `database does not exist` | Tên DB và cluster đang kết nối |
| `permission denied` | Owner/grant; không giải bằng superuser lâu dài |
| `relation does not exist` | Database/schema/search path/migration |

## Tự kiểm tra

1. Role khác database thế nào?
2. Vì sao application role không nên có `CREATEDB` hoặc superuser?
3. `pg_isready` chứng minh được gì và chưa chứng minh được gì?

::: {.hint}
- Luôn bắt đầu bằng `\conninfo`; nhiều lỗi SQL thực ra là kết nối nhầm database.
- Tách credential của app, migration và DBA khi hệ thống lớn dần.
- Connection URL là secret nếu chứa password.
- Production database không cần public port khi app chạy cùng private network.
:::

Tiếp theo: [SQL thực chiến](#chapter-practical-sql).
