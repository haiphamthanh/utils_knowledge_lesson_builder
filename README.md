# Knowledge Lesson Builder

Project nhỏ để lưu lesson độc lập, mô tả quan hệ tri thức và xuất bản chúng theo
một learning path tuyến tính. Thiết kế cốt lõi:

- `lessons/` là nội dung có ID ổn định, không dùng số thứ tự trong tên file.
- `graph.yml` mô tả quan hệ thật giữa các chủ đề và kiểm tra prerequisite.
- `paths/*.yml` quyết định thứ tự đọc, chapter và phạm vi core/optional.
- `templates/<name>/` quyết định format đầu ra; chọn template bằng tên khi build.

> Graph validates the path. Graph does not author the path.

Kiến trúc tổng thể, sequence diagram, quy tắc authoring và tài liệu vận hành được
gom trong thư mục [`readme/`](readme/README.md).

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

Guideline đầy đủ nằm trong [`readme/`](readme/README.md).

## Resource lifecycle

Nội dung đầu vào đi qua ba trạng thái:

```text
resource/raw → resource/pool → resource/done
```

```bash
./build.sh resource sync
./build.sh resource list --status pool
./build.sh resource review <resource-id>
./build.sh resource complete <resource-id> \
  --cookbook web-system-foundations \
  --lesson request-response
```

`resource/index.yml` lưu thời điểm tạo, review, hoàn thành và lesson đích. Xem
[`readme/resources.md`](readme/resources.md) để biết quy tắc transition.

Skill `$promote-pool-lesson` nằm trong
`.codex/skills/promote-pool-lesson` của chính repo này. Khi gọi skill, agent sẽ
liệt kê pool, đề xuất lesson/graph/path và yêu cầu xác nhận trước khi tạo nội
dung hoặc move resource.

## Kiểm thử

```bash
.venv/bin/python -m unittest discover -s tests -v
```
