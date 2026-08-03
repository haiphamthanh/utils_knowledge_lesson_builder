# Mô hình tri thức

Hệ thống tách ba nguồn sự thật để mỗi file chỉ trả lời một câu hỏi.

| Lớp | Câu hỏi | Nguồn sự thật |
|---|---|---|
| Lesson | Chủ đề này giải thích điều gì? | `lessons/<id>.md` |
| Knowledge graph | Các chủ đề quan hệ với nhau thế nào? | `graph.yml` |
| Learning path | Người đọc nên đi theo thứ tự nào? | `paths/<id>.yml` |

Nguyên tắc trung tâm:

> Graph validates the path. Graph does not author the path.

## Relation được phép

- `requires`: phải hiểu node đích trước node nguồn.
- `builds_on`: phát triển từ kiến thức trước nhưng không nhất thiết là
  prerequisite cứng.
- `part_of`: thuộc một chủ đề lớn hơn.
- `component_of`: là thành phần kỹ thuật.
- `explains`: giúp giải thích cơ chế.
- `applies`: ứng dụng một khái niệm khác.
- `contrasts_with`: dùng để so sánh.
- `related_to`: có liên quan nhưng không có quan hệ cụ thể hơn.
- `leads_to`: hạn chế hiện tại làm phát sinh nhu cầu tiếp theo.

Chỉ `requires` ảnh hưởng trực tiếp đến validation thứ tự path. Không dùng
`related_to` thay cho một quan hệ cụ thể hơn.

## Core, optional và graph-only

- `core`: bắt buộc để hoàn thành mục tiêu chapter.
- `optional`: giúp đào sâu nhưng không chặn mạch chính.
- `graph-only`: đã có trong kho tri thức nhưng chưa thuộc path xuất bản.

Một chapter nên có tối đa khoảng 5–8 core lesson. Khi vượt giới hạn, tách
chapter, chuyển nhánh sâu thành optional hoặc giữ lesson ở graph-only.

