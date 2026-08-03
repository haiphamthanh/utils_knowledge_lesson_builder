---
id: request-response
title: "Request và response"
depth: overview
status: complete
tags:
  - web
  - http
---

## Request và response

### Nhu cầu

Một người dùng cần yêu cầu hệ thống thực hiện công việc và nhận lại kết quả theo
một hợp đồng mà cả client lẫn server đều hiểu.

### Tại sao có nhu cầu này?

Nếu từng client gọi trực tiếp vào chi tiết nội bộ của server, hai phía bị gắn
chặt với nhau. Mọi thay đổi nhỏ đều có thể làm hỏng toàn bộ luồng.

### Khái niệm cốt lõi

Request mô tả hành động, tài nguyên và dữ liệu đầu vào. Response trả về trạng
thái cùng dữ liệu đầu ra. HTTP là hợp đồng truyền tải phổ biến cho cặp tương tác
này.

### Kỹ thuật đang sử dụng

Client gửi method, path, headers và có thể có body. Server định tuyến request,
kiểm tra đầu vào, thực thi nghiệp vụ rồi trả status, headers và body.

```text
Browser -> GET /lessons -> Server -> 200 + JSON
```

### Ví dụ

`GET /health` không thay đổi dữ liệu. Server có thể trả `200 OK` cùng
`{"status":"ok"}` để công cụ vận hành biết process còn phản hồi.

### Ưu điểm và hạn chế

Hợp đồng request–response tạo boundary dễ kiểm thử và thay thế. Tuy nhiên, bản
thân HTTP không giữ trạng thái nghiệp vụ sau khi process dừng.

### Khi nào nên và không nên dùng?

Phù hợp cho tương tác có đầu vào và đầu ra rõ ràng. Không nên ép mọi luồng dài
hoặc bất đồng bộ thành một request phải chờ đến khi hoàn tất.

### Liên kết kiến thức

Đây là bức tranh tổng thể. Các chủ đề liên quan gồm routing, authentication,
queue và observability.

### Nhu cầu tiếp theo

::: {.next-step}
Khi server tạo ra dữ liệu mà người dùng cần xem lại vào ngày mai, lưu dữ liệu
trong memory là chưa đủ. Ta cần hiểu trạng thái bền vững.
:::

### Tóm tắt

- Request–response là hợp đồng giữa client và server.
- Status code là một phần của hợp đồng, không chỉ là chi tiết kỹ thuật.
- HTTP không tự giải quyết nhu cầu lưu dữ liệu qua restart.

### Tài liệu tham khảo

- RFC 9110 — HTTP Semantics.

