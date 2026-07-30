# PostgreSQL bên trong ứng dụng {#chapter-postgresql-app}

## Mục tiêu

Kết nối kiến thức SQL với lifecycle của Node process: pool, transaction,
migration, backup và các failure mode chỉ xuất hiện khi có concurrency.

## Connection pool

Mở connection PostgreSQL có chi phí; giữ một pool cho process giúp tái sử dụng.
`src/lib/database.js` lazy-create `pg.Pool` với:

- `max`: số connection tối đa của process.
- `connectionTimeoutMillis`: chờ mở/lấy connection bao lâu.
- `idleTimeoutMillis`: đóng connection idle sau bao lâu.

Pool sizing là bài toán toàn hệ thống:

```text
tổng connection tiềm năng
  = số app process × DB_POOL_MAX
    + migration/admin/monitoring headroom
```

Nếu PostgreSQL cho 100 connection, 10 replica × pool 20 là cấu hình không thể
đạt. Pool không tạo capacity; nó giới hạn concurrency vào database.

## Query và transaction

Helper `query(text, params)` phù hợp câu độc lập. `withClient(callback)` giữ một
client cho transaction:

```javascript
await withClient(async (client) => {
  await client.query("BEGIN");
  try {
    await client.query("UPDATE ...", values);
    await client.query("DELETE ...", values);
    await client.query("COMMIT");
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  }
});
```

Luôn release client trong `finally`. Client bị giữ quên sẽ làm pool cạn dần và
request mới timeout dù database vẫn healthy.

## Migration như release contract

Migration runner đọc file `NNN_name.sql`, sort, kiểm tra `schema_migrations` rồi
chạy mỗi file trong transaction. Quy tắc:

1. Migration đã apply không được sửa nội dung trong lịch sử.
2. Thay đổi mới là file số tiếp theo.
3. Migration phải tương thích với version app trong cửa sổ rollout/rollback.
4. Backup trước migration có rủi ro dữ liệu.
5. Chạy migration một lần ở release step, không để mỗi replica tranh nhau.

Forward-only không có nghĩa không thể phục hồi. Nó nghĩa rollback thường là một
migration sửa tiếp hoặc restore có kiểm soát, không phải tự động chạy “down.sql”
trên production đang có traffic.

## Lock, deadlock và timeout

Update giữ row lock tới cuối transaction. Schema migration có thể cần lock mạnh
hơn. Một transaction dài làm request khác chờ; hai transaction lấy resource
theo thứ tự ngược nhau có thể deadlock và PostgreSQL sẽ huỷ một transaction.

Giảm rủi ro bằng cách:

- Transaction ngắn, không gọi HTTP/email bên trong.
- Cập nhật resource theo thứ tự ổn định.
- Đặt lock/statement timeout phù hợp cho migration.
- Retry chỉ transaction idempotent với lỗi transient đã phân loại.

## Backup và restore

Custom format hỗ trợ validate và chọn object khi restore:

```bash
pg_dump -Fc --no-owner --no-acl "$DATABASE_URL" -f app.dump
pg_restore --list app.dump >/dev/null
shasum -a 256 app.dump > app.dump.sha256
```

Restore an toàn vào database mới:

```bash
createdb ai_learn_jlpt_restore_test
pg_restore --exit-on-error --no-owner --no-acl \
  --dbname=postgresql://localhost:5432/ai_learn_jlpt_restore_test app.dump
```

Sau restore: chạy migration mới nhất, smoke test và kiểm tra ownership/content.
Chỉ đổi `DATABASE_URL` sau khi database mới đạt acceptance criteria.

::: {.current}
Các script trong `scripts/ops/` tạo dump, validate bằng `pg_restore --list`, ghi
SHA-256 và từ chối initial restore nếu database đã có table. Release script tạo
backup `predeploy` trước migration.
:::

## Lab: recovery drill

::: {.lab}
**Preflight:** dùng source database lab và tên target chứa `restore_test`.

1. Tạo vài record marker trong DB lab.
2. Chạy `pg_dump -Fc` và `pg_restore --list`.
3. Restore vào database mới.
4. So sánh migration count, user count và marker record.
5. Chạy application smoke test với target restore.
6. Drop cả hai DB lab sau khi ghi kết quả.
:::

::: {.checkpoint}
Một file dump tồn tại không phải checkpoint. Checkpoint là ứng dụng kết nối được,
migration state đúng và các invariant dữ liệu vượt qua smoke test.
:::

## Failure modes

- Pool max hợp lý cho một process nhưng vượt DB limit khi scale replica.
- Migration sửa table lớn giữ lock lâu hơn thời gian deploy.
- Backup nằm cùng disk/VPS và mất cùng incident.
- Restore trực tiếp đè production thay vì tạo database mới.
- Retry query ghi dữ liệu không idempotent tạo duplicate.

## Tự kiểm tra

1. Pool 10 với 8 replica cần reserve ít nhất bao nhiêu connection?
2. Tại sao backup và migration phải nằm trước switch traffic?
3. Restore test cần kiểm tra điều gì ngoài row count?

::: {.hint}
- Budget connection ở cấp hệ thống, không ở từng service riêng lẻ.
- Migration là code production; review lock và backward compatibility.
- Recovery drill nên chạy định kỳ trước khi có incident.
- Giữ ít nhất một backup ngoài failure domain của VPS.
:::

Tiếp theo: [Ghép các thành phần thành hệ thống](#chapter-components).

