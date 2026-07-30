# Làm auth đủ an toàn cho production {#chapter-auth-hardening}

## Mục tiêu

Auth hiện tại có nền tảng tốt nhưng “đăng nhập được” khác “chịu được Internet”.
Chương này sắp thứ tự các lớp phòng vệ cần bổ sung theo rủi ro.

## Threat model tối thiểu

Giả định attacker có thể:

- Gửi login/register tự động với tốc độ cao.
- Biết email từ nguồn khác và thử password bị lộ.
- Lừa user mở trang ngoài để gửi request chéo.
- Có được một session token qua máy dùng chung hoặc log sai cách.
- Thay ID, role hoặc `user_id` trong payload.

Threat model biến từ “hãy làm auth an toàn” thành test cụ thể.

## Ưu tiên 1: giới hạn thử credential

::: {.recommendation}
Thêm rate limit theo cả IP và normalized account key. Ví dụ: cửa sổ ngắn cho IP,
backoff tăng dần cho account, log sự kiện nhưng không log password. Trả response
giống nhau cho email tồn tại và không tồn tại.
:::

Không khoá account vĩnh viễn sau vài lần sai; attacker có thể dùng cơ chế đó để
DoS người khác. Một thiết kế hợp lý kết hợp delay, limit và cảnh báo.

## Ưu tiên 2: session lifecycle

- Rotate session sau login hoặc thay đổi privilege.
- Cho user xem và revoke các session khác.
- Revoke toàn bộ khi đổi/reset password.
- Dọn `expires_at <= NOW()` bằng job định kỳ.
- Lưu metadata tối thiểu phục vụ audit như created time; cân nhắc privacy trước
  khi lưu IP/user agent dài hạn.

Query cleanup đơn giản:

```sql
DELETE FROM sessions WHERE expires_at <= NOW();
```

## CSRF và SameSite

`SameSite=Lax` giảm nhiều cross-site POST truyền thống nhưng không thay thế toàn
bộ CSRF defense. Nếu có endpoint nhạy cảm, cross-origin integration hoặc thay
đổi cookie policy, dùng CSRF token gắn với session và kiểm tra `Origin`.

Không dùng GET để thay đổi state. `GET /logout` hay `GET /delete` khiến browser,
prefetcher và crawler có thể kích hoạt action ngoài ý muốn.

## Email verification và reset password

Hai luồng này nên dùng token ngẫu nhiên một lần, lưu token hash cùng expiry:

```text
request reset
  -> luôn trả response chung
  -> nếu account tồn tại: tạo random token
  -> lưu hash(token), purpose, user_id, expires_at, used_at
  -> gửi raw token qua email
  -> consume trong transaction
  -> đổi password + revoke sessions + đánh dấu used_at
```

Schema đề xuất có thể dùng table `auth_tokens` với unique token hash, `purpose`
giới hạn `VERIFY_EMAIL`/`RESET_PASSWORD`, expiry ngắn và `used_at`.

::: {.warning}
Không lưu raw reset token, không gửi password mới qua email và không cho phép một
token được dùng hai lần. Link reset có thể xuất hiện trong browser history hoặc
proxy log; TTL phải ngắn.
:::

## Audit, MFA và OAuth

Audit log nên ghi `event`, `actor_user_id`, `target_user_id`, request ID, time và
outcome; không ghi password/token/body. Sự kiện quan trọng: login success/fail,
password reset, role change, revoke session và admin action.

MFA đáng thêm khi account có dữ liệu giá trị cao hoặc quyền admin. OAuth/OIDC
đáng thêm khi tổ chức đã có identity provider. Cả hai tạo recovery và operational
work mới; không nên thêm chỉ để thay form login đang đủ dùng.

## Recipe triển khai theo lát dọc

1. Viết threat/test case trước.
2. Thêm schema bằng migration forward-only.
3. Tạo repository chỉ xử lý token hash và transaction.
4. Tạo service áp policy TTL/one-time/revoke.
5. Controller chỉ parse input và map lỗi chung.
6. Thêm audit event và metric.
7. Test token hết hạn, reuse, concurrent consume và cross-user.

## Lab: review auth hiện tại

::: {.lab}
Không sửa code. Lập bảng cho `register`, `login`, `logout`, `change role` với các
cột: asset, attacker, abuse case, control hiện có, control còn thiếu, test.

Đối chiếu các file `auth.js`, `session.js`, `controller.ts`, `dispatcher.ts` và
smoke test. Ưu tiên ba gap có impact cao nhất thay vì liệt kê công nghệ.
:::

## Failure modes

- Rate limit chỉ theo IP, làm hỏng user sau NAT hoặc dễ đổi IP để vượt.
- Reset token không one-time hoặc không revoke session cũ.
- Audit log chứa credential.
- Bật OAuth nhưng bỏ qua account linking takeover.
- Thêm MFA nhưng không thiết kế recovery code/support flow.

## Tự kiểm tra

1. Tại sao account lock cứng có thể trở thành DoS?
2. Vì sao reset password cần revoke session?
3. Khi nào SameSite chưa đủ chống CSRF?

::: {.hint}
- Hardening theo threat, không theo checklist công nghệ.
- Token một lần phải có purpose, expiry và atomic consume.
- Admin là mục tiêu ưu tiên cho MFA và audit.
- Recovery flow thường rủi ro hơn happy-path login; review nó trước go-live.
:::

Tiếp theo: [Cài đặt và kết nối PostgreSQL](#chapter-postgresql-setup).

