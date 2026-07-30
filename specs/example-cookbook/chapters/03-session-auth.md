# Xây dựng session authentication {#chapter-session-auth}

## Mục tiêu

Hiểu trọn vòng đời register/login/session/logout và các quyết định bảo mật đang
được hiện thực trong `src/modules/common/auth/`.

## Authentication flow

```text
email + password
  -> normalize + validate
  -> lookup password hash
  -> scrypt + timing-safe comparison
  -> random session token
  -> store SHA-256(token) in PostgreSQL
  -> send raw token once in HttpOnly cookie
```

Server cần raw token để gửi client nhưng không cần lưu nó. Những request sau gửi
cookie; server hash token rồi join `sessions` với `users`. Nếu database bị đọc
trộm, token hash không thể được dùng trực tiếp làm cookie.

## Password hash không phải encryption

Encryption có key để giải mã. Password storage cần hàm một chiều, chậm và có salt
riêng. Dự án tạo salt 16 byte và dùng `crypto.scryptSync`; chuỗi lưu có dạng:

```text
scrypt:<salt-hex>:<derived-key-hex>
```

Salt chống bảng hash dựng sẵn và làm hai user cùng password có hash khác nhau.
`timingSafeEqual` giảm rò rỉ timing khi so sánh derived key.

::: {.warning}
Không tự thiết kế thuật toán mật mã. Việc định dạng hash có version/scheme là
hữu ích để sau này rehash, nhưng primitive phải đến từ thư viện chuẩn đã review.
:::

## Session và cookie

Token được tạo bằng `randomBytes(32).toString("base64url")`. Session hết hạn sau
14 ngày. Cookie có:

- `HttpOnly`: JavaScript browser không đọc token.
- `SameSite=Lax`: giảm một số cross-site request.
- `Secure` ở production: chỉ gửi qua HTTPS.
- `Path=/`: dùng cho toàn ứng dụng.
- `Expires`: browser biết thời điểm bỏ cookie.

`HttpOnly` không chống việc browser tự gửi cookie trong request xấu; vì vậy XSS,
CSRF và validation vẫn cần được xử lý riêng.

## Request context và access

Mỗi request đọc token từ cookie, tìm session còn hạn và tạo `currentUser` công
khai chỉ gồm `id`, `email`, `role`. Password hash không đi vào context hoặc
response.

- Không có user ở endpoint private: `401 Authentication required`.
- Có user nhưng thiếu role: `403 Admin access required`.
- Có role nhưng record thuộc người khác: repository không trả record.

Logout xoá session trong database rồi gửi cookie có `Max-Age=0`. Chỉ xoá cookie
mà không xoá DB session sẽ để token bị đánh cắp tiếp tục hợp lệ.

## Session hay JWT?

| Tiêu chí | Session DB | JWT access token |
|---|---|---|
| Revoke tức thì | Dễ, xoá row | Khó nếu không có denylist/TTL ngắn |
| Mỗi request | Query/cache session | Verify chữ ký |
| State server | Có | Thường không |
| Thay đổi role tức thì | Có | Chờ token mới |
| Phù hợp browser app nhỏ | Rất phù hợp | Thường không cần |

JWT hữu ích giữa service hoặc hệ identity phân tán, nhưng không tự động an toàn
hơn. Nếu cuối cùng vẫn cần revoke store, refresh token và rotation, độ phức tạp
có thể cao hơn session.

## Lab: auth bằng `curl`

::: {.lab}
**Preflight:** server local chạy trên test DB; file cookie nằm ngoài Git.

```bash
case "$DATABASE_URL" in
  *lab*|*test*) ;;
  *) echo 'Refusing non-test database'; exit 1 ;;
esac
cookie_jar="$(mktemp)"
base_url="http://127.0.0.1:5050"

curl -i -c "$cookie_jar" -H 'Content-Type: application/json' \
  -d '{"email":"cookbook-user@example.test","password":"safe-lab-password"}' \
  "$base_url/api/auth/register"

curl -sS -b "$cookie_jar" "$base_url/api/me"
curl -i -b "$cookie_jar" -c "$cookie_jar" -X POST \
  "$base_url/api/auth/logout"
curl -sS -b "$cookie_jar" "$base_url/api/me"

psql "$DATABASE_URL" -Xv ON_ERROR_STOP=1 -c \
  "DELETE FROM users WHERE email='cookbook-user@example.test'"
rm -f "$cookie_jar"
```

Kỳ vọng: register trả `201` và `Set-Cookie`; `/me` đầu có user; logout trả 200;
`/me` cuối có `user: null`.
:::

::: {.checkpoint}
Mở cookie jar chỉ để xác nhận attribute/format, không chép token vào log hoặc tài
liệu. Query table `sessions` phải thấy token hash, không thấy raw cookie token.
:::

## Failure modes

- Trả password hash trong JSON do dùng `SELECT *`.
- Phân biệt “email không tồn tại” và “password sai”, hỗ trợ user enumeration.
- Production không dùng HTTPS khiến cookie `Secure` không hoạt động đúng luồng.
- Session hết hạn không được dọn định kỳ.
- Role thay đổi nhưng session/JWT cũ vẫn mang policy cũ.

## Tự kiểm tra

1. Tại sao salt có thể lưu cạnh hash?
2. Token hash bảo vệ tình huống nào?
3. Khác biệt giữa xoá cookie và revoke session là gì?

::: {.hint}
- Auth response chỉ trả public user projection.
- Dùng thông báo login chung để giảm user enumeration.
- Session ID là credential; bảo vệ như password.
- Chọn session trước nếu hệ thống là browser app cùng domain và cần revoke dễ.
:::

Tiếp theo: [Làm auth đủ an toàn cho production](#chapter-auth-hardening).
