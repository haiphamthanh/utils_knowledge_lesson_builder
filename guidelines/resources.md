# Resource lifecycle

## Nguồn sự thật và cấu trúc

```text
resource/
├── raw/       # nguồn chưa review
├── archive/   # original bất biến của split parent
├── pool/      # item đã review, sẵn sàng tạo lesson
├── done/      # item đã tạo lesson
└── index.yml  # lifecycle, lineage, timestamp và checksum (schema v2)
```

Luồng nhỏ là `raw → inspect → pool → lesson → done`. Luồng split là
`raw → inspect → prepare → archive + nhiều pool children → lesson → done`.
Không move trực tiếp giữa các thư mục. `archive/` được commit vào Git;
`build/resource-preparation/` chỉ là candidate tạm và đã được ignore.

## Quy tắc integrity

- Core chỉ phân tích ngữ nghĩa cho `.md`, `.markdown`, `.txt` UTF-8. Binary
  được giữ nguyên dưới dạng attachment/archive. Symlink bị từ chối.
- Checksum cây bao gồm relative path và byte content. `sync` không tự sửa
  checksum của `pool`, `done` hoặc `archive` khi phát hiện thay đổi.
- Split phải gán mỗi dòng text đúng một lần: coverage 100%, không gap/overlap.
- Attachment phải được copy nguyên file vào ít nhất một part hoặc được người
  dùng xác nhận `archive-only`.
- `finalize` dùng copy-on-write. Raw chỉ bị xóa sau khi archive/pool, manifest
  và index đã được ghi và kiểm tra. Có thể retry cùng preparation ID.

## Commands

```bash
./build.sh resource sync
./build.sh resource list [--status raw|archive|pool|done] [--json]
./build.sh resource inspect <resource-id> [--json]
./build.sh resource prepare <resource-id> --plan <plan.yml>
./build.sh resource finalize <resource-id> --preparation <preparation-id>
./build.sh resource verify <resource-id> [--json]
./build.sh resource review <resource-id> [--allow-large-single --reason "..."]
./build.sh resource complete <resource-id> --cookbook <id> --lesson <id>
```

`resource review` là đường tắt tương thích cho resource nhỏ. Trên 3.000 từ,
lệnh từ chối nếu thiếu `--allow-large-single`; nó không được bypass một
preparation đang tồn tại. Trên 8.000 từ, workflow prepare mặc định bắt buộc
split; override cần lý do và xác nhận rõ của người dùng.

## Split-plan version 1

```yaml
version: 1
resource_id: system-design-notes
source_sha256: "<hash từ inspect>"
mode: split
reason: "Tài liệu có hai mục tiêu học độc lập"
parts:
  - id: system-boundary
    title: System Boundary
    fragments:
      - path: article.md
        start_line: 1
        end_line: 140
    attachments: []
  - id: request-lifecycle
    title: Request Lifecycle
    fragments:
      - path: article.md
        start_line: 141
        end_line: 310
    attachments:
      - diagrams/request-flow.png
archive_only: []
```

Mỗi child trong pool có `content.md` nguyên văn và `provenance.yml`. Archive
parent có `source/` và `manifest.yml`; `resource verify` dùng các bằng chứng này
để kiểm lại original hash, lineage, fragment, attachment và line coverage.

## Skill

- Gọi `$prepare-raw-resource` để AI đề xuất biên ngữ nghĩa. Skill phải chờ xác
  nhận trước khi prepare và chờ lần nữa trước khi finalize. AI không được sửa
  nội dung hoặc tự move file.
- Gọi `$promote-pool-lesson` để tạo lesson. Skill phải chạy `resource verify`
  trước, ưu tiên `content.md`, và dừng nếu child/parent archive không hợp lệ.
