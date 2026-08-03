# Hướng dẫn sử dụng cơ bản

Tài liệu này đi theo một vòng đời hoàn chỉnh:

```text
resource/raw
    → review
resource/pool
    → $promote-pool-lesson
knowledge/<cookbook>/lessons + graph + path
    → validate + build
resource/done
```

Chạy các lệnh từ thư mục gốc của project.

## Automation nào nên dùng?

| Tác vụ | Cách phù hợp | Lý do |
|---|---|---|
| Copy nguồn vào `raw` | Filesystem + `resource sync` | Deterministic, không cần agent suy luận |
| Chuyển `raw → pool` | Người dùng review + `resource review` | Quyết định tin cậy nguồn cần người dùng xác nhận; command đã move và ghi timestamp chính xác |
| Chuyển `pool → lesson → done` | `$promote-pool-lesson` | Phải đọc nội dung, chọn cookbook/relation/path và phối hợp nhiều file |
| Validate/build cookbook | `build.sh` | CLI cho kết quả lặp lại được và báo lỗi trực tiếp |
| Review lesson nằm đúng sách/vị trí | `$review-lesson-placement` | Cần kết hợp validation với đánh giá objective, depth và Progressive Disclosure |

Không tạo skill chỉ để bọc một command có sẵn. Skill được dành cho bước cần
đọc nhiều nguồn sự thật hoặc cần đánh giá ngữ nghĩa.

## 1. Thêm một nguồn kiến thức vào raw

Mỗi resource là một file hoặc một thư mục con cấp đầu tiên trong
`resource/raw/`. Nên đặt tên viết thường theo dạng `kebab-case` để hệ thống tạo
resource ID ổn định.

Thêm một file:

```bash
cp /duong-dan/toi/cache-notes.md resource/raw/cache-notes.md
```

Hoặc thêm một thư mục gồm nhiều file liên quan:

```bash
cp -R /duong-dan/toi/cache-notes resource/raw/cache-notes
```

Đồng bộ filesystem vào `resource/index.yml`, rồi kiểm tra kết quả:

```bash
./build.sh resource sync
./build.sh resource list --status raw
```

Lệnh `sync` tự ghi `created_at`. Không sửa timestamp thủ công và không dùng
cùng một tên item ở nhiều thư mục trạng thái.

## 2. Review và đưa raw vào pool

Đọc nguồn trong `resource/raw/`, loại bỏ nội dung không đáng tin cậy và xác nhận
nó đủ rõ để phát triển thành lesson. Sau đó dùng resource ID hiển thị bởi lệnh
`list`:

```bash
./build.sh resource review cache-notes
./build.sh resource list --status pool
```

Lệnh `review` thực hiện hai việc cùng nhau:

1. Move item từ `resource/raw/` sang `resource/pool/`.
2. Cập nhật `status: pool` và `reviewed_at` trong `resource/index.yml`.

Không move bằng tay khi command có thể thực hiện transition.

## 3. Dùng skill để đưa pool thành lesson

Trong Codex, gọi skill bằng một yêu cầu như:

```text
Sử dụng $promote-pool-lesson để tạo lesson từ resource cache-notes.
```

Nếu chưa biết resource ID, yêu cầu skill liệt kê pool trước:

```text
Sử dụng $promote-pool-lesson, liệt kê các resource trong pool để tôi chọn.
```

Skill sẽ đọc source và đề xuất:

- cookbook đích;
- lesson ID, title và depth;
- relation cần thêm vào `graph.yml`;
- vai trò `core`, `optional` hoặc `graph-only`;
- chapter và vị trí cụ thể trong path, nếu lesson cần xuất bản.

Skill phải chờ xác nhận trước khi ghi file. Hãy kiểm tra đề xuất theo ba nguồn sự
thật:

| Nguồn | Trách nhiệm |
|---|---|
| `knowledge/<cookbook>/lessons/<lesson-id>.md` | Nội dung của lesson |
| `knowledge/<cookbook>/graph.yml` | Quan hệ với các lesson khác |
| `knowledge/<cookbook>/paths/<path-id>.yml` | Chapter, vai trò và thứ tự đọc |

`cookbook.yml` chỉ chứa metadata và default của cookbook. Không thêm danh sách
lesson hoặc thứ tự lesson vào file này. Skill chỉ sửa `cookbook.yml` khi title,
description, default path, template hoặc format thực sự cần thay đổi.

Sau khi được xác nhận, skill thực hiện tuần tự:

1. Tạo lesson draft bằng `create-lesson`; graph node được đăng ký cùng lúc.
2. Viết lesson theo `templates/lesson.md` và chuyển status sang `review`.
3. Thêm các graph relation đã xác nhận.
4. Thêm lesson vào path khi vai trò là `core` hoặc `optional`; `graph-only`
   không nằm trong path.
5. Chạy unit test, validate và build cookbook liên quan.
6. Chỉ khi mọi bước thành công, chạy `resource complete` để move source từ
   `resource/pool/` sang `resource/done/`.
7. Cập nhật `completed_at`, `cookbook` và `lesson_id` trong
   `resource/index.yml`, rồi commit thay đổi hoàn chỉnh.

Kiểm tra kết quả lifecycle:

```bash
./build.sh resource list --status done
```

Nếu validation hoặc build lỗi, resource phải ở lại pool. Không tự chạy
`resource complete` để bỏ qua lỗi.

## 4. Build cookbook theo tên

Tên dùng trong command là cookbook ID. Nó phải khớp giữa tên thư mục
`knowledge/<cookbook-id>/` và trường `id` trong `cookbook.yml`.

Build bằng default path, template và format:

```bash
./build.sh build web-system-foundations
```

Chọn cụ thể path, template và format:

```bash
./build.sh build web-system-foundations \
  --path foundation \
  --template default \
  --format html
```

Optional lesson chỉ xuất hiện khi được yêu cầu:

```bash
./build.sh build web-system-foundations --include-optional
```

Output có quy ước:

```text
build/<cookbook-id>/<path-id>/
└── <cookbook-id>-<path-id>-<template-id>.<extension>
```

Ví dụ:

```text
build/web-system-foundations/foundation/
└── web-system-foundations-foundation-default.html
```

Muốn đổi tiêu đề hiển thị trong sách, sửa `title` trong `cookbook.yml`. Không
đổi cookbook ID chỉ để đổi tiêu đề. Nếu thật sự tạo một cookbook khác, tạo một
thư mục ID mới trong `knowledge/` với `cookbook.yml`, `graph.yml`, `lessons/` và
`paths/` riêng.

## 5. Kiểm tra lesson đã nằm đúng sách và đúng vị trí

Cách nhanh nhất là gọi skill read-only:

```text
Sử dụng $review-lesson-placement để kiểm tra lesson cache trong cookbook
web-system-foundations.
```

Skill đọc lesson, graph, các path liên quan và lesson lân cận; sau đó chạy
validation phù hợp và trả bảng evidence. Skill không tự sửa file. Các bước bên
dưới là cách kiểm tra thủ công hoặc dùng để xác minh lại báo cáo của skill.

### Bước 1: Tìm path đang chứa lesson

```bash
rg -n --fixed-strings "cache" knowledge/web-system-foundations/paths
```

Không có kết quả có thể mang một trong ba ý nghĩa:

- lesson đang là `graph-only` theo chủ đích;
- lesson chưa được đưa vào path;
- đang tìm sai cookbook hoặc lesson ID.

Nếu lesson nằm trong `optional_lessons`, nó không xuất hiện trong bản build mặc
định.

### Bước 2: Validate prerequisite và thứ tự

```bash
./build.sh validate web-system-foundations --path foundation
```

Để kiểm tra cả nhánh optional:

```bash
./build.sh validate web-system-foundations \
  --path foundation \
  --include-optional
```

Validator sẽ báo lỗi nếu:

- path tham chiếu lesson không tồn tại;
- lesson xuất hiện trước một prerequisite khai báo bằng `requires`;
- dependency `requires` có cycle;
- core lesson phụ thuộc optional lesson;
- overview phụ thuộc deep-dive;
- lesson bị lặp hoặc đang ở trạng thái không được xuất bản.

Chỉ dùng `requires` khi người đọc không thể hiểu đúng bài mới nếu chưa biết bài
đích. Các quan hệ như `builds_on`, `related_to` hoặc `leads_to` không được dùng
để ép thứ tự.

### Bước 3: Xem thứ tự thực tế sau khi build

```bash
./build.sh build web-system-foundations --path foundation
rg -n '^# |^## ' \
  build/.work/web-system-foundations/foundation/book.md
```

File `book.md` là source trung gian đã ghép đúng thứ tự chapter và lesson. Đây
là cách nhanh nhất để kiểm tra lesson nằm trước/sau bài nào mà chưa cần đọc toàn
bộ HTML hoặc PDF.

### Bước 4: Kiểm tra kiến thức trước đó có “vừa đủ”

Validation chỉ kiểm tra các invariant có thể xác định bằng máy. Người review cần
đọc `objective`, `context` và `out_of_scope` của chapter rồi trả lời:

1. Không có prerequisite thật sự nào bị thiếu trước lesson mới?
2. Có relation `requires` nào chỉ là “liên quan” và nên đổi sang relation nhẹ
   hơn?
3. Lesson có trực tiếp phục vụ objective của chapter không?
4. Lesson nên là core, optional hay graph-only?
5. Overview có dừng ở bức tranh tổng thể thay vì đào sâu implementation không?
6. Chapter có giữ khoảng 5–8 core lesson trở xuống không?
7. Phần “Nhu cầu tiếp theo” có nối tự nhiên sang kiến thức sau không?

Nếu chưa chắc vị trí, giữ lesson ở `graph-only` và ghi đề xuất review. Không tự
thêm vào cuối path và không dùng graph để tự sinh thứ tự đọc.

## Lệnh tham khảo nhanh

| Mục đích | Lệnh |
|---|---|
| Đồng bộ resource mới | `./build.sh resource sync` |
| Liệt kê raw | `./build.sh resource list --status raw` |
| Review raw → pool | `./build.sh resource review <resource-id>` |
| Liệt kê pool | `./build.sh resource list --status pool` |
| Tạo lesson từ pool | Gọi `$promote-pool-lesson` trong Codex |
| Review vị trí lesson | Gọi `$review-lesson-placement` trong Codex |
| Kiểm tra cookbook/path | `./build.sh validate <cookbook> --path <path>` |
| Build HTML mặc định | `./build.sh build <cookbook>` |
| Build cả optional | `./build.sh build <cookbook> --include-optional` |
| Kiểm tra done | `./build.sh resource list --status done` |

Đọc thêm [`knowledge-model.md`](knowledge-model.md),
[`authoring.md`](authoring.md) và [`resources.md`](resources.md) khi cần thay đổi
nghiệp vụ chi tiết.
