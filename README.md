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
├── web-system-foundations-foundation-chapter-lesson.html
└── web-system-foundations-foundation-chapter-lesson.pdf
```

## Chọn template

Mỗi định dạng workbook nằm trong một thư mục có tên ổn định:

```text
templates/
├── lesson.md
├── chapter-lesson/    # Chương 01 / Bài 01, khuyến nghị
├── clean/             # Không đánh số
├── academic/          # Đánh số 1 / 1.1 / 1.1.1
├── editorial/         # Handbook với semantic content cards
├── editorial-banner/  # Theme banner xanh–vàng
├── editorial-study/   # Theme study book cyan–orange
└── default/           # Asset dùng chung và tương thích cũ
```

Chọn phong cách bằng tên:

```bash
./build.sh build web-system-foundations --template chapter-lesson
./build.sh build web-system-foundations --template clean
./build.sh build web-system-foundations --template academic
```

Khám phá toàn bộ template trước khi chọn:

```bash
./build.sh template list
./build.sh template list --json
```

| Template | Chapter | Lesson | Heading bên trong |
|---|---|---|---|
| `chapter-lesson` | `CHƯƠNG 01` | `Bài 01` | Không số |
| `clean` | Không số | Không số | Không số |
| `academic` | `1` | `1.1` | `1.1.1` |
| `editorial` | `CHƯƠNG 01` | `Bài 01` | Content cards theo vai trò |
| `editorial-banner` | `CHƯƠNG 01` | `Bài 01` | Banner xanh và dải màu đậm |
| `editorial-study` | `CHƯƠNG 01` | `Bài 01` | Cyan–orange dạng study book |

Template có thể dùng lại asset trong `templates/default/` bằng relative path,
nhưng không thể tham chiếu file nằm ngoài `templates/`. Hai field
`number_sections` và `toc_depth` trong `template.yml` điều khiển độ sâu mục lục
và đánh số; không thêm số vào lesson ID hoặc tên file.

`editorial-banner` và `editorial-study` được thiết kế lại từ đầu dựa trên ngôn
ngữ thị giác của hai bài tham khảo VniTeach; URL nguồn cảm hứng được lưu trong
`template.yml`. Project không sao chép nguyên source template bên ngoài.

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
