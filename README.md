# Knowledge Lesson Builder

Project nhỏ để lưu lesson độc lập, mô tả quan hệ tri thức và xuất bản chúng theo
một learning path tuyến tính. Thiết kế cốt lõi:

- `lessons/` là nội dung có ID ổn định, không dùng số thứ tự trong tên file.
- `graph.yml` mô tả quan hệ thật giữa các chủ đề và kiểm tra prerequisite.
- `paths/*.yml` quyết định thứ tự đọc, chapter và phạm vi core/optional.
- `templates/<name>/` quyết định format đầu ra; chọn template bằng tên khi build.

> Graph validates the path. Graph does not author the path.

Kiến trúc tổng thể và sequence diagram nằm tại
[`docs/architecture.md`](docs/architecture.md). Quy tắc authoring và tài liệu
vận hành được gom trong [`guidelines/`](guidelines/README.md).

Bắt đầu với [`guidelines/user-guide.md`](guidelines/user-guide.md) để đi trọn quy trình
từ resource thô đến cookbook đã build.

## Cài đặt

Yêu cầu Python 3.11+, Pandoc 3.x; build PDF cần thêm XeLaTeX.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Chạy example

```bash
./build.sh validate web-system-foundations
./build.sh build web-system-foundations
./build.sh build web-system-foundations --format pdf
```

Output:

```text
build/web-system-foundations/foundation/
├── web-system-foundations-foundation-default.html
└── web-system-foundations-foundation-default.pdf
```

## Chọn template

Mỗi định dạng workbook nằm trong một thư mục có tên ổn định:

```text
templates/
├── lesson.md
└── default/
    ├── template.yml
    ├── html-template.html
    ├── pdf-template.tex
    ├── book.css
    └── admonitions.lua
```

Build bằng tên:

```bash
./build.sh build web-system-foundations --template default --format html
```

Muốn thêm style mới, copy `templates/default/` sang `templates/<ten-moi>/`, đổi
`id` trong `template.yml`, rồi chỉnh các asset bên trong. Core builder không cần
thay đổi.

## Cấu trúc cookbook

```text
knowledge/<cookbook>/
├── cookbook.yml
├── graph.yml
├── paths/
│   └── foundation.yml
└── lessons/
    └── lesson-id.md
```

`cookbook.yml` chỉ giữ metadata chung và mặc định build. `graph.yml` không quyết
định thứ tự xuất bản. Một lesson có thể xuất hiện trong nhiều path mà không sao
chép nội dung.

## Tạo lesson mới

```bash
./build.sh create-lesson web-system-foundations cache \
  --title "Cache" \
  --depth standard
```

Lệnh chỉ thực hiện hai thay đổi chắc chắn:

1. Tạo `lessons/cache.md` ở trạng thái `draft`.
2. Thêm node `cache` vào `graph.yml`.

Lệnh không tự đoán relation và không tự chèn lesson vào learning path. Sau khi
viết nội dung, hãy chọn một trong ba vai trò: `core`, `optional` hoặc
`graph-only`, rồi chạy validation.

Guideline đầy đủ nằm trong [`guidelines/`](guidelines/README.md).

## Resource lifecycle

Nguồn nhỏ đi thẳng qua pool; nguồn lớn được split nhưng vẫn giữ original:

```text
resource nhỏ: raw → inspect → pool → done
resource lớn: raw → inspect/prepare → archive + nhiều pool children → done
```

```bash
./build.sh resource sync
./build.sh resource inspect <resource-id> --json
./build.sh resource review <resource-id>
./build.sh resource prepare <resource-id> --plan <plan.yml>
./build.sh resource finalize <resource-id> --preparation <preparation-id>
./build.sh resource verify <resource-id>
./build.sh resource complete <resource-id> \
  --cookbook web-system-foundations \
  --lesson request-response
```

`resource/index.yml` schema v2 lưu checksum, lineage, thời điểm và lesson đích.
Split giữ byte gốc trong `resource/archive/`; candidate chỉ nằm trong `build/`
cho tới xác nhận finalize. Xem
[`guidelines/resources.md`](guidelines/resources.md) để biết quy tắc transition.

Skill `$promote-pool-lesson` nằm trong
`.codex/skills/promote-pool-lesson` của chính repo này. Khi gọi skill, agent sẽ
liệt kê pool, đề xuất lesson/graph/path và yêu cầu xác nhận trước khi tạo nội
dung hoặc move resource.

Skill `$prepare-raw-resource` dùng AI duy nhất cho quyết định ngữ nghĩa
single/split. CLI deterministic kiểm coverage/checksum; skill chờ xác nhận hai
lần và không được viết lại nội dung nguồn.

Skill `$review-lesson-placement` nằm trong
`.codex/skills/review-lesson-placement` và chỉ audit cookbook, chapter,
prerequisite cùng độ sâu nội dung; skill này không tự sửa file.

## Kiểm thử

```bash
.venv/bin/python -m unittest discover -s tests -v
```
