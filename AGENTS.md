# Project instructions

Đọc `readme/agent-instructions.md`, `readme/knowledge-model.md` và
`readme/authoring.md` trước khi thay đổi lesson, graph hoặc learning path.
Đọc `readme/resources.md` trước khi chuyển item giữa raw, pool và done.

Giữ ba nguồn sự thật tách biệt:

- lesson quản lý nội dung;
- graph quản lý quan hệ;
- path quản lý trải nghiệm đọc.

Không tự sinh thứ tự path từ graph và không đánh số lesson trong tên file.

Trước mỗi commit, chạy:

```bash
.venv/bin/python -m unittest discover -s tests -v
./build.sh validate <cookbook>
```

Build lại format bị ảnh hưởng khi sửa template hoặc nội dung. Tạo commit riêng
trước khi chuyển từ refactor sang thay đổi nghiệp vụ.
