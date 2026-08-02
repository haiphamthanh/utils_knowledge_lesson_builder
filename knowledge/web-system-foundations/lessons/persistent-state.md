---
id: persistent-state
title: "Trạng thái bền vững"
depth: standard
status: complete
tags:
  - state
  - storage
---

## Trạng thái bền vững

### Nhu cầu

Dữ liệu người dùng tạo ra phải còn tồn tại sau khi server restart hoặc được
triển khai phiên bản mới.

### Tại sao có nhu cầu này?

Memory gắn với vòng đời process. Khi process dừng, các object trong memory biến
mất; nhiều process cũng không tự nhìn thấy cùng một bản state.

### Khái niệm cốt lõi

Persistent state là dữ liệu có vòng đời dài hơn process tạo ra nó. Nó cần một
storage boundary cùng quy tắc đọc, ghi và phục hồi rõ ràng.

### Kỹ thuật đang sử dụng

Luồng tối thiểu là nhận input, kiểm tra hợp lệ, ghi qua storage adapter, xác nhận
kết quả rồi mới trả thành công cho client.

### Ví dụ

Một lesson đang soạn dở được ghi vào database. Sau deploy, request mới đọc lại
cùng lesson bằng ID thay vì phụ thuộc vào memory của process cũ.

### Ưu điểm và hạn chế

Persistence giúp dữ liệu sống qua restart và có thể dùng chung. Đổi lại, hệ
thống có thêm failure mode: timeout, ghi một phần, cạnh tranh cập nhật và backup
không dùng được.

### Khi nào nên và không nên dùng?

Dùng cho dữ liệu có giá trị sau request hiện tại. Không cần lưu bền vững cho
cache có thể tái tạo hoặc dữ liệu trung gian rất ngắn hạn.

### Liên kết kiến thức

Chủ đề này phát triển từ mô hình request–response và dẫn tới database,
transaction, backup cùng cache.

### Nhu cầu tiếp theo

::: {.next-step}
File đơn lẻ có thể lưu dữ liệu, nhưng khó bảo đảm cấu trúc, truy vấn và cập nhật
đồng thời. Ta cần một hệ quản trị dữ liệu có hợp đồng mạnh hơn.
:::

### Tóm tắt

- Persistent state sống lâu hơn process.
- Xác nhận ghi thành công phải phản ánh đúng durability mong muốn.
- Thêm storage cũng thêm failure mode cần quan sát và phục hồi.

### Tài liệu tham khảo

- Martin Kleppmann, *Designing Data-Intensive Applications*, 2017.

