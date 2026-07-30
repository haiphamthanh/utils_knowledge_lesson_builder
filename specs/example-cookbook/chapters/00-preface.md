# Lời mở đầu {.unnumbered #preface}

Quyển sách này trả lời một câu hỏi thực tế: từ một codebase đang chạy trên máy
cá nhân, làm thế nào để hiểu, xây dựng và vận hành nó như một hệ thống web nhiều
người dùng?

Đây không phải tài liệu “copy lệnh rồi hy vọng”. Mỗi quyết định đều đi theo bốn
bước: vấn đề là gì, thành phần nào chịu trách nhiệm, cách kiểm chứng ra sao, và
khi hỏng thì quan sát ở đâu. Dự án AI Learn JLPT được dùng làm case study vì nó
có đủ một vòng đời nhỏ nhưng thực: browser client, native Node.js HTTP server,
session authentication, PostgreSQL, migration, build artifact, Nginx, systemd
và GitHub Actions.

## Cách đọc {.unnumbered}

Nếu muốn hiểu toàn hệ thống, đọc tuần tự. Nếu đang giải quyết một việc cụ thể:

| Nhu cầu | Chương nên đọc |
|---|---|
| Bổ sung auth hoặc sửa lỗi phân quyền | 2, 3, 4 |
| Học PostgreSQL và SQL | 5, 6, 7 |
| Hiểu kiến trúc codebase | 1, 8 |
| Chọn framework hoặc giảm dependency | 9 |
| Đưa hệ thống lên VPS | 10, 11, 12 |
| Tự đánh giá kiến thức | 13 |

Các nhãn trong sách có ý nghĩa cố định:

::: {.current}
Nội dung trong hộp này đã được đối chiếu với source hiện tại. Đường dẫn code là
source of truth; sách giải thích ý nghĩa chứ không thay thế code.
:::

::: {.recommendation}
Đây là thiết kế nên bổ sung khi yêu cầu production đòi hỏi. Nó không được mô tả
như một tính năng đã tồn tại.
:::

::: {.warning}
Lệnh có thể làm thay đổi dữ liệu hoặc availability. Đọc preflight và xác nhận
đúng database, host, user trước khi chạy.
:::

## Luật an toàn cho lab {.unnumbered}

1. Lab database chỉ dùng database có tên chứa `lab` hoặc `test`.
2. Không dùng `DATABASE_URL` production để chạy smoke test hoặc restore.
3. Không dán password, token, private key hay dump vào Git.
4. Lệnh xoá phải có target cụ thể; không dùng biến chưa được kiểm tra.
5. Một backup chỉ đáng tin sau khi `pg_restore --list` và restore thử thành công.

Kiến thức trong sách không phụ thuộc việc bạn chọn native HTTP, Express hay
NestJS. Framework thay đổi syntax; các invariant về identity, ownership,
transaction, release và recovery vẫn giữ nguyên.

::: {.hint}
- Đọc hệ thống theo luồng dữ liệu, không theo thứ tự thư mục.
- Luôn hỏi “ai sở hữu dữ liệu này?” trước khi viết query.
- Luôn hỏi “nếu bước này hỏng giữa chừng?” trước khi tự động hoá.
- Cài ít công cụ hơn nhưng hiểu rõ failure mode của từng công cụ.
:::
