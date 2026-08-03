# Quy trình authoring

## 1. Phân loại trước khi tạo

Xác định chủ đề có một mục tiêu học độc lập hay chỉ là một mục nhỏ của lesson đã
có. Tìm theo ID, title và tags để tránh trùng.

Chọn depth:

- `overview`: bức tranh tổng thể, giới thiệu trước và đào sâu sau.
- `standard`: hiểu cơ chế, ví dụ và trade-off.
- `deep-dive`: biến thể, edge case và chi tiết implementation.

## 2. Tạo draft

```bash
./build.sh create-lesson <cookbook> <lesson-id> \
  --title "Tên bài" \
  --depth standard
```

Không dùng số thứ tự trong ID hoặc tên file. ID phải ổn định để có thể chèn bài
vào giữa mà không đổi tên hàng loạt.

## 3. Viết theo chuỗi tư duy

Mỗi lesson phải trả lời:

1. Nhu cầu là gì?
2. Tại sao nhu cầu xuất hiện?
3. Khái niệm và kỹ thuật hiện tại là gì?
4. Kỹ thuật hoạt động thế nào?
5. Ví dụ cụ thể nào chứng minh cách hiểu?
6. Ưu điểm, hạn chế và điều kiện áp dụng là gì?
7. Nó liên kết với kiến thức nào?
8. Hạn chế nào làm phát sinh nhu cầu tiếp theo?

Overview không được phình thành deep-dive. Nếu một nhánh cần giải thích dài, tạo
lesson riêng và liên kết qua graph.

## 4. Chọn relation và vị trí

Chỉ dùng `requires` khi người đọc không thể hiểu đúng lesson nguồn nếu chưa biết
lesson đích. Sau đó quyết định lesson là core, optional hay graph-only.

Không mặc định thêm vào cuối path. Với core lesson, tìm:

- bài gần nhất mà chủ đề mới phát triển từ đó;
- bài gần nhất sử dụng chủ đề mới;
- chapter có cùng learning objective.

## 5. Review và xuất bản

Giữ `status: draft` trong lúc viết. Khi nội dung đủ để review, đổi sang `review`;
khi đã kiểm chứng, đổi sang `complete`.

```bash
./build.sh validate <cookbook> --include-draft
./build.sh build <cookbook> --include-draft
```

Build phát hành thông thường không dùng `--include-draft`.

Khi cần kiểm tra lesson đã thuộc đúng cookbook, chapter, vai trò và thứ tự
prerequisite hay chưa, gọi `$review-lesson-placement`. Skill này chỉ đọc và báo
cáo; mọi thay đổi sau review vẫn cần được xác nhận riêng.
