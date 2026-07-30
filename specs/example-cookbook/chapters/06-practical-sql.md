# SQL thực chiến trên schema dự án {#chapter-practical-sql}

## Mục tiêu

Đọc và viết SQL bảo toàn invariant, chống injection và có thể giải thích bằng
query plan. Ví dụ dùng schema AI Learn JLPT thay vì table minh hoạ xa lạ.

## Data type là một phần của thiết kế

- `UUID`: ID khó va chạm, tạo độc lập; không phải access control.
- `TIMESTAMPTZ`: thời điểm tuyệt đối; hiển thị theo timezone ở UI.
- `DATE`: ngày lịch như ngày học, không phải timestamp lúc nửa đêm.
- `JSONB`: cấu trúc linh hoạt cần query; không thay thế mọi column/relationship.
- `BYTEA`: binary nhỏ/vừa cần transaction cùng dữ liệu; ảnh lớn nên cân nhắc
  object storage khi scale.

`NOT NULL`, `DEFAULT`, `CHECK`, `UNIQUE` và foreign key làm database bảo vệ
invariant dù dữ liệu đi vào từ API, migration hay admin script.

## CRUD có scope

Insert một note private:

```sql
INSERT INTO manual_notes (user_id, note_date, content)
VALUES ($1, $2, $3)
RETURNING id, note_date, content, completed;
```

Update phải khóa theo owner:

```sql
UPDATE manual_notes
SET content = $3, updated_at = NOW()
WHERE id = $1 AND user_id = $2
RETURNING id, content, updated_at;
```

Placeholder `$1` không chỉ giúp escape quote; nó tách SQL structure khỏi data.
Không thể parameterize tên table/column — dynamic identifier cần allowlist.

## JOIN và quan hệ

Session lookup hiện tại join identity với credential state:

```sql
SELECT users.id, users.email, users.role
FROM sessions
JOIN users ON users.id = sessions.user_id
WHERE sessions.token_hash = $1
  AND sessions.expires_at > NOW();
```

Foreign key `sessions.user_id REFERENCES users(id) ON DELETE CASCADE` đảm bảo
xoá user cũng xoá session. `CASCADE` hữu ích khi child không còn ý nghĩa độc lập;
với lịch sử/audit, có thể cần `RESTRICT` hoặc `SET NULL`.

## Aggregate, CTE và pagination

Đếm study action theo ngày:

```sql
SELECT action_date, count(*) AS actions
FROM study_actions
WHERE user_id = $1 AND action_date >= $2
GROUP BY action_date
ORDER BY action_date;
```

CTE làm các bước biến đổi dễ đọc, nhưng đừng dùng nó để che một query quá phức
tạp. Pagination nhỏ có thể dùng `LIMIT/OFFSET`; dataset lớn nên dùng cursor dựa
trên cặp sort ổn định như `(created_at, id)`.

## Transaction

Transaction cần khi nhiều câu lệnh phải cùng thành công hoặc cùng thất bại:

```sql
BEGIN;
UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2;
DELETE FROM sessions WHERE user_id = $2;
COMMIT;
```

Nếu update password thành công nhưng revoke session thất bại, invariant bảo mật
bị phá. Transaction đóng gói hai thay đổi thành một đơn vị atomic.

Trong Node, mọi câu của transaction phải dùng **cùng connection**. Gọi helper
`query()` trên pool cho từng câu có thể lấy connection khác nhau.

## Index và query plan

Index đổi chi phí đọc lấy chi phí storage/write. Tạo index theo query thật:

```sql
CREATE INDEX idx_manual_notes_user_date
  ON manual_notes(user_id, note_date);
```

Thứ tự column quan trọng. Index trên `(user_id, note_date)` phù hợp filter owner
rồi range/order theo date. Nó không nhất thiết tốt cho query chỉ theo `note_date`.

Đọc plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM manual_notes
WHERE user_id = '00000000-0000-0000-0000-000000000000'
ORDER BY note_date DESC
LIMIT 20;
```

`ANALYZE` thực thi query; không dùng tuỳ tiện với DELETE/UPDATE production.
Quan sát estimated/actual rows, scan type, sort và buffer — đừng chỉ tìm chữ
“Index Scan”. Table nhỏ thường sequential scan là đúng.

## JSONB: dùng có chủ đích

`metadata JSONB` phù hợp thuộc tính phụ thay đổi theo action. Những field cần
foreign key, unique, range validation hoặc join thường nên là column. Nếu query
một JSON path thường xuyên, thêm expression/GIN index sau khi đo workload.

## Lab: query an toàn

::: {.lab}
**Preflight:** `LAB_DATABASE_URL` phải chứa `lab` hoặc `test`.

```bash
case "$LAB_DATABASE_URL" in
  *lab*|*test*) ;;
  *) echo 'Refusing non-lab database'; exit 1 ;;
esac
psql "$LAB_DATABASE_URL" -Xv ON_ERROR_STOP=1
```

Trong `psql`:

```sql
\timing on
BEGIN;
INSERT INTO users (email, password_hash)
VALUES ('sql-lab@example.test', 'lab:not-a-real-password-hash')
RETURNING id;
ROLLBACK;
```

Sau rollback, query email phải trả 0 row. Tiếp theo chọn một index hiện có trong
`\d manual_notes`, viết query phù hợp và so sánh `EXPLAIN` trước/sau khi tăng dữ
liệu lab.
:::

::: {.checkpoint}
Bạn phải giải thích được constraint nào bảo vệ dữ liệu, query nào dùng index và
tại sao transaction rollback không để lại row.
:::

## Failure modes

- `SELECT *` làm API vô tình lộ column nhạy cảm.
- Dùng offset lớn gây scan/sort tốn kém.
- Index từng column nhưng query cần composite index.
- Transaction giữ mở trong lúc gọi network API, gây lock lâu.
- JSONB biến thành nơi cất mọi thứ và mất constraint.

## Tự kiểm tra

1. Khi nào `ON DELETE CASCADE` không phù hợp?
2. Vì sao transaction trong pool cần cùng client?
3. Tại sao sequential scan chưa chắc là lỗi?

::: {.hint}
- Viết invariant trước, rồi chọn constraint và transaction để bảo vệ nó.
- Index theo filter + sort của query nóng, không theo cảm giác.
- Luôn scope private query bằng owner.
- Đo plan trên dữ liệu gần với production; table 10 row đánh lừa optimizer review.
:::

Tiếp theo: [PostgreSQL bên trong ứng dụng](#chapter-postgresql-app).

