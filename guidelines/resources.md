# Resource lifecycle

Mỗi item là một file hoặc thư mục con cấp đầu tiên:

```text
resource/
├── index.yml
├── raw/
├── pool/
└── done/
```

- `raw`: nội dung mới thêm, chưa review.
- `pool`: nội dung đã review, sẵn sàng để tạo lesson.
- `done`: nội dung đã tạo thành lesson ở trạng thái `review` hoặc `complete`.

`resource/index.yml` là nguồn sự thật cho timestamp và lesson đích. Không sửa
timestamp thủ công nếu có thể dùng command.

## Commands

Đồng bộ item mới được copy thủ công vào `raw`:

```bash
./build.sh resource sync
```

Liệt kê:

```bash
./build.sh resource list
./build.sh resource list --status pool --json
```

Đánh dấu review xong:

```bash
./build.sh resource review <resource-id>
```

Sau khi lesson đã ở trạng thái `review` hoặc `complete`:

```bash
./build.sh resource complete <resource-id> \
  --cookbook <cookbook-id> \
  --lesson <lesson-id>
```

Không chuyển file trực tiếp nếu có thể dùng command. Nếu đã move thủ công, chạy
`resource sync`; hệ thống sẽ cập nhật trạng thái và timestamp còn thiếu.

## Skill tạo lesson

Gọi `$promote-pool-lesson` để:

1. Liệt kê tất cả file/thư mục trong pool.
2. Chọn một resource.
3. Xem đề xuất cookbook, lesson ID, depth, relation và vị trí path.
4. Xác nhận trước khi agent tạo lesson.
5. Validate/build thành công rồi mới chuyển resource sang done.
