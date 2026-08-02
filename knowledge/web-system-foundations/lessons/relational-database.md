---
id: relational-database
title: "Cơ sở dữ liệu quan hệ"
depth: standard
status: complete
tags:
  - database
  - sql
---

## Cơ sở dữ liệu quan hệ

### Nhu cầu

Hệ thống cần lưu dữ liệu có cấu trúc, truy vấn theo nhiều điều kiện và duy trì
các ràng buộc khi nhiều thao tác xảy ra đồng thời.

### Tại sao có nhu cầu này?

Tự quản lý nhiều file khiến việc liên kết dữ liệu, chống ghi dở và thay đổi
schema trở thành trách nhiệm của từng đoạn code ứng dụng.

### Khái niệm cốt lõi

Database quan hệ tổ chức dữ liệu thành bảng, hàng và cột. Khóa cùng constraint
biểu diễn identity và invariant; transaction gom nhiều thay đổi thành một đơn vị
nhất quán.

### Kỹ thuật đang sử dụng

Ứng dụng gửi câu lệnh SQL có tham số. Database lập kế hoạch, thực thi trong
transaction, kiểm tra constraint rồi commit hoặc rollback.

### Ví dụ

Bảng `lessons` dùng `id` làm khóa chính và `slug` có unique constraint. Hai
request cố tạo cùng slug không thể cùng commit thành công.

### Ưu điểm và hạn chế

Mô hình quan hệ cung cấp query linh hoạt, constraint và transaction mạnh. Chi
phí là vận hành thêm một service, quản lý migration và hiểu rõ transaction
boundary.

### Khi nào nên và không nên dùng?

Phù hợp khi dữ liệu có quan hệ và invariant quan trọng. Một file tĩnh hoặc
embedded store có thể đơn giản hơn cho công cụ cá nhân chỉ đọc dữ liệu nhỏ.

### Liên kết kiến thức

Prerequisite là trạng thái bền vững. Các nhánh tiếp theo gồm schema design,
index, transaction isolation, backup và replication.

### Nhu cầu tiếp theo

::: {.next-step}
Database lưu đúng chưa có nghĩa là truy vấn đã nhanh hoặc thay đổi schema đã an
toàn. Nhu cầu tiếp theo là thiết kế schema và migration có thể kiểm chứng.
:::

### Tóm tắt

- Database đưa cấu trúc và invariant về một boundary dùng chung.
- Constraint bảo vệ dữ liệu ngay cả khi application code có lỗi.
- Transaction và migration cần được thiết kế, không xuất hiện miễn phí.

### Tài liệu tham khảo

- PostgreSQL Documentation — Data Definition và Transactions.

