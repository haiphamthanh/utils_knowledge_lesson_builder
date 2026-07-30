# Knowledge Lesson Builder

Project nhỏ để lưu lesson độc lập, mô tả quan hệ tri thức và xuất bản chúng theo
một learning path tuyến tính. Thiết kế cốt lõi:

- `lessons/` là nội dung có ID ổn định, không dùng số thứ tự trong tên file.
- `graph.yml` mô tả quan hệ thật giữa các chủ đề và kiểm tra prerequisite.
- `paths/*.yml` quyết định thứ tự đọc, chapter và phạm vi core/optional.
- `templates/<name>/` quyết định format đầu ra; chọn template bằng tên khi build.

> Graph validates the path. Graph does not author the path.

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
src/<cookbook>/
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

## Kiểm thử

```bash
.venv/bin/python -m unittest discover -s tests -v
```

