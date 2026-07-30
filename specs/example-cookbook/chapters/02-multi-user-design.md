# Thiết kế hệ thống nhiều người dùng {#chapter-multi-user}

## Mục tiêu

Thiết kế multi-user không bắt đầu bằng màn hình login. Nó bắt đầu bằng việc xác
định identity nào đang thao tác và record nào identity đó được phép chạm tới.

## Bốn câu hỏi khác nhau

| Khái niệm | Câu hỏi |
|---|---|
| Identity | Chủ thể này là ai? |
| Authentication | Bằng chứng nhận dạng có hợp lệ không? |
| Authorization | Chủ thể được phép thực hiện action nào? |
| Ownership | Record cụ thể này thuộc về ai? |

Role `USER` cho phép gọi endpoint tạo note không đồng nghĩa user được sửa mọi
note. Role trả lời quyền theo loại hành động; ownership trả lời quyền trên từng
record.

## Phân loại dữ liệu trước khi viết API

Dự án dùng ba loại chính:

- `USER_PRIVATE`: input, note, highlight, favorite, selection, study action.
- `ADMIN_SHARED`: lesson/catalog được admin quản lý và learner cùng đọc.
- `SYSTEM_CONFIG`: cấu hình build/runtime, không phải nội dung cá nhân.

Mỗi table private có `user_id` trực tiếp, hoặc join tới một record có `user_id`.
Điều này làm ownership trở thành dữ liệu có thể query và test, thay vì một giả
định trong UI.

```sql
SELECT id, note_date, content
FROM manual_notes
WHERE user_id = $1
ORDER BY note_date DESC;
```

Không query theo `id` rồi mới hy vọng controller nhớ so sánh owner. Cách an toàn
hơn là đưa owner vào điều kiện tìm record:

```sql
DELETE FROM manual_notes
WHERE id = $1 AND user_id = $2
RETURNING id;
```

Nếu không có row trả về, API không cần tiết lộ record không tồn tại hay thuộc
user khác.

## IDOR và horizontal privilege escalation

IDOR xảy ra khi client thay ID trong URL/body và server tin rằng ID hợp lệ đồng
nghĩa được phép truy cập. Đây là lỗi phía server; ẩn nút trên frontend không sửa
được.

Ví dụ nguy hiểm:

```sql
SELECT * FROM manual_notes WHERE id = $1;
```

User B lấy được UUID của User A bằng log, link chia sẻ nhầm hoặc đoán từ API khác
thì có thể đọc record. UUID làm việc đoán khó hơn, không thay thế authorization.

::: {.current}
Các repository private trong dự án lọc theo authenticated `user_id`. Image bytes
được join qua `user_inputs.user_id` trước khi trả nội dung. Smoke suite tạo hai
user để kiểm tra B không đọc hoặc sửa dữ liệu của A.
:::

## Role hay permission?

Hai role `USER`/`ADMIN` đủ khi policy đơn giản và ổn định. Khi xuất hiện editor,
support, content reviewer hoặc quyền theo tổ chức, một chuỗi `if role === ...`
sẽ nhanh chóng khó kiểm soát.

Chuyển sang permission khi:

- Một user có nhiều vai trò theo tenant/project.
- Cùng action nhưng scope khác nhau.
- Policy cần audit và thay đổi không deploy code.

Đừng thiết kế RBAC tổng quát trước khi có yêu cầu. Với ứng dụng nhỏ, endpoint
access metadata cộng ownership query rõ ràng dễ review hơn.

## Lab: ma trận hai user

::: {.lab}
**Preflight:** chạy server với một `TEST_DATABASE_URL` có tên chứa `test`; không
dùng dữ liệu production.

1. Đăng ký User A và User B, mỗi user giữ cookie jar riêng.
2. A tạo một manual note, ghi lại ID.
3. B thử list, read, update và delete ID của A.
4. Kỳ vọng B không thấy record và không thay đổi được nó.
5. A đọc lại record để chứng minh dữ liệu còn nguyên.

Có thể dùng smoke suite hiện tại làm oracle:

```bash
TEST_DATABASE_URL=postgresql://localhost:5432/ai_learn_jlpt_test \
  npm run test:integration
```
:::

::: {.checkpoint}
Test phải chứng minh cả **không lộ dữ liệu** và **không làm thay đổi dữ liệu**.
Chỉ test response status là chưa đủ; đọc lại record của A sau phép thử của B.
:::

## Failure modes

- List lọc owner nhưng update/delete quên lọc.
- Table con không có `user_id`, join ownership sai hoặc thiếu.
- Endpoint admin được bảo vệ nhưng static CMS page lại bị coi là lớp bảo mật.
- Dùng email từ request body thay vì user ID từ authenticated context.
- Batch query nhận một mảng ID nhưng không giới hạn tất cả ID theo owner.

## Tự kiểm tra

1. Vì sao UUID không phải access control?
2. Khi nào `404` an toàn hơn việc nói “record thuộc user khác”?
3. Shared catalog khác private note ở invariant nào?

::: {.hint}
- Gắn owner vào record ngay từ lúc tạo.
- Lấy owner từ session context, không lấy từ payload của client.
- Viết ma trận quyền trước endpoint: anonymous, owner, non-owner, admin.
- Test mọi verb; lỗi ownership thường nằm ở update/delete hơn list.
:::

Tiếp theo: [Xây dựng session authentication](#chapter-session-auth).

