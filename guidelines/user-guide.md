# Hướng dẫn dùng ngay

Chạy từ thư mục gốc của project và thay các ID mẫu bằng ID thực tế.

## Step 1: Copy source thô vào `resource/raw`

```bash
cp /duong-dan/toi/cache-notes.md resource/raw/cache-notes.md
```

Source gồm nhiều file thì copy cả thư mục:

```bash
cp -R /duong-dan/toi/cache-notes resource/raw/cache-notes
```

## Step 2: Đồng bộ và inspect source

```bash
./build.sh resource sync
./build.sh resource list --status raw
./build.sh resource inspect cache-notes --json
```

## Step 3: Đưa source vào pool

Nguồn nhỏ, chỉ có một chủ đề:

```bash
./build.sh resource review cache-notes
```

Nguồn lớn, nhiều file hoặc nhiều chủ đề, gọi trong Codex:

```text
Sử dụng $prepare-raw-resource để xử lý resource cache-notes.
```

Xác nhận proposal và verification report khi skill yêu cầu.

## Step 4: Tạo lesson từ pool

```bash
./build.sh resource list --status pool
```

Sau đó gọi trong Codex:

```text
Sử dụng $promote-pool-lesson để tạo lesson từ resource <resource-id>.
```

Xác nhận cookbook, graph relation và vị trí learning path được đề xuất.

## Step 5: Validate và build cookbook

### Validate cookbook

```bash
./build.sh validate web-system-foundations
```

### Build cookbook

Xem template trước khi build:

```bash
./build.sh template list
```

Ví dụ chọn theme:

```bash
./build.sh build web-system-foundations --template editorial
./build.sh build web-system-foundations --template editorial-banner
./build.sh build web-system-foundations --template editorial-study
```

Output nằm trong:

```text
build/<cookbook-id>/<path-id>/
```

## Step 6: Kiểm tra kết quả

```bash
./build.sh resource list --status done
```

Khi cần kiểm tra lesson đã nằm đúng sách và đúng thứ tự, gọi:

```text
Sử dụng $review-lesson-placement để kiểm tra lesson <lesson-id> trong cookbook <cookbook-id>.
```

# Hướng dẫn chi tiết

Tài liệu này đi theo một vòng đời hoàn chỉnh:

```text
resource/raw
    → inspect → review (nhỏ) hoặc $prepare-raw-resource (lớn/nhiều chủ đề)
resource/pool
    → $promote-pool-lesson
knowledge/<cookbook>/lessons + graph + path
    → validate + build
resource/done
```

Chạy các lệnh từ thư mục gốc của project.

## Automation nào nên dùng?

| Tác vụ                             | Cách phù hợp                          | Lý do                                                                          |
| ---------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| Copy nguồn vào `raw`               | Filesystem + `resource sync`          | Deterministic, không cần agent suy luận                                        |
| Chuyển `raw → pool` nhỏ            | Người dùng review + `resource review` | Deterministic, ít hơn 3.000 từ và chỉ một chủ đề                               |
| Chuẩn hóa/split nguồn lớn          | `$prepare-raw-resource`               | AI chọn biên ngữ nghĩa; CLI bảo đảm checksum, coverage và copy-on-write        |
| Chuyển `pool → lesson → done`      | `$promote-pool-lesson`                | Phải đọc nội dung, chọn cookbook/relation/path và phối hợp nhiều file          |
| Validate/build cookbook            | `build.sh`                            | CLI cho kết quả lặp lại được và báo lỗi trực tiếp                              |
| Review lesson nằm đúng sách/vị trí | `$review-lesson-placement`            | Cần kết hợp validation với đánh giá objective, depth và Progressive Disclosure |

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

Đồng bộ filesystem vào `resource/index.yml`, rồi inspect kết quả:

```bash
./build.sh resource sync
./build.sh resource list --status raw
./build.sh resource inspect cache-notes --json
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

Lệnh `review` dành cho nguồn nhỏ, một chủ đề, và thực hiện hai việc cùng nhau:

1. Move item từ `resource/raw/` sang `resource/pool/`.
2. Cập nhật `status: pool` và `reviewed_at` trong `resource/index.yml`.

Không move bằng tay khi command có thể thực hiện transition.

Nếu nguồn vượt 3.000 từ, gồm nhiều file hoặc nhiều chủ đề, gọi:

```text
Sử dụng $prepare-raw-resource để xử lý resource cache-notes.
```

Skill đọc outline trước, đề xuất giữ nguyên hoặc bảng các part theo file/line,
rồi chờ xác nhận lần một. Sau `resource prepare`, skill trình bày checksum,
coverage, gap/overlap, attachment và output hash; chỉ sau xác nhận lần hai mới
chạy `resource finalize`. Với split, original đi vào
`resource/archive/<parent-id>/source/`, mỗi part vào
`resource/pool/<part-id>/`, và có thể kiểm lại bất kỳ lúc nào:

```bash
./build.sh resource verify cache-notes
./build.sh resource verify <part-id>
```

Trên 8.000 từ phải split trừ khi người dùng xác nhận rõ một lý do giữ nguyên.
Trên 50.000 từ mà không có heading/cấu trúc file đủ rõ, skill dừng và yêu cầu
outline. AI không tóm tắt hay viết lại nội dung tại bước này.

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

| Nguồn                                         | Trách nhiệm                    |
| --------------------------------------------- | ------------------------------ |
| `knowledge/<cookbook>/lessons/<lesson-id>.md` | Nội dung của lesson            |
| `knowledge/<cookbook>/graph.yml`              | Quan hệ với các lesson khác    |
| `knowledge/<cookbook>/paths/<path-id>.yml`    | Chapter, vai trò và thứ tự đọc |

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
  --template chapter-lesson \
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
└── web-system-foundations-foundation-chapter-lesson.html
```

Các lựa chọn sẵn có:

| Template           | Cách hiển thị chỉ mục                                                      |
| ------------------ | -------------------------------------------------------------------------- |
| `chapter-lesson`   | `CHƯƠNG 01`, `Bài 01`; heading nhỏ không có số                             |
| `clean`            | Không đánh số                                                              |
| `academic`         | Đánh số đầy đủ `1`, `1.1`, `1.1.1`                                         |
| `editorial`        | Handbook cân bằng với các card theo vai trò nội dung                       |
| `editorial-banner` | PDF A4 với chapter banner, tab số dựng đứng và dải mép xanh–vàng           |
| `editorial-study`  | PDF A4 với chapter `C–HƯƠNG`, viền chẵn/lẻ cyan–orange và khung giáo trình |

Xem template trước khi build:

```bash
./build.sh template list
```

Ví dụ chọn theme:

```bash
./build.sh build web-system-foundations --template editorial
./build.sh build web-system-foundations --template editorial-banner
./build.sh build web-system-foundations --template editorial-study
```

Hai theme trên dùng LaTeX template độc lập cho PDF; thay đổi một theme không
làm đổi bố cục PDF của theme còn lại. Bản HTML vẫn giữ cùng semantic content
cards để nội dung có cấu trúc nhất quán giữa các format.

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

| Mục đích               | Lệnh                                               |
| ---------------------- | -------------------------------------------------- |
| Đồng bộ resource mới   | `./build.sh resource sync`                         |
| Liệt kê raw            | `./build.sh resource list --status raw`            |
| Inspect raw            | `./build.sh resource inspect <resource-id> --json` |
| Review raw nhỏ → pool  | `./build.sh resource review <resource-id>`         |
| Chuẩn hóa/split raw    | Gọi `$prepare-raw-resource` trong Codex            |
| Verify resource        | `./build.sh resource verify <resource-id>`         |
| Liệt kê pool           | `./build.sh resource list --status pool`           |
| Tạo lesson từ pool     | Gọi `$promote-pool-lesson` trong Codex             |
| Review vị trí lesson   | Gọi `$review-lesson-placement` trong Codex         |
| Kiểm tra cookbook/path | `./build.sh validate <cookbook> --path <path>`     |
| Build HTML mặc định    | `./build.sh build <cookbook>`                      |
| Build cả optional      | `./build.sh build <cookbook> --include-optional`   |
| Kiểm tra done          | `./build.sh resource list --status done`           |

Đọc thêm [`knowledge-model.md`](knowledge-model.md),
[`authoring.md`](authoring.md) và [`resources.md`](resources.md) khi cần thay đổi
nghiệp vụ chi tiết.
