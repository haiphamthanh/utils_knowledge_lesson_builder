# Hướng dẫn cho agent

Khi thay đổi tri thức trong project:

1. Đọc `cookbook.yml`, `graph.yml`, path liên quan và metadata các lesson lân
   cận trước khi sửa.
2. Không dùng tên file để biểu diễn thứ tự.
3. Không tự suy thứ tự PDF từ graph.
4. Không thêm prerequisite chỉ vì hai chủ đề liên quan.
5. Không tự chèn lesson mới vào cuối learning path.
6. Giữ overview ngắn; tách nhánh sâu thành standard/deep-dive.
7. Không để core lesson phụ thuộc optional lesson.
8. Chạy unit test, validation và ít nhất một build liên quan trước khi commit.
9. Mỗi commit chỉ chứa một thay đổi nghiệp vụ hoặc một refactor độc lập.

Khi chưa chắc vị trí của lesson, tạo lesson + graph node và để ở trạng thái
graph-only. Nêu rõ gợi ý vị trí thay vì tự thay đổi learning path.

