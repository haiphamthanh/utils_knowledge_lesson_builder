# System Engineering Cookbook

Đây là source của quyển **Cookbook Xây dựng và Vận hành Hệ thống Web
Multi-user**. Nội dung được viết bằng Markdown và ghép thành một quyển sách duy
nhất theo thứ tự trong `book.yaml`.

## Build

Yêu cầu:

- Pandoc 3.x.
- XeLaTeX cùng các package phổ biến của TeX Live (`texlive-xetex`,
  `texlive-latex-extra`, `fonts-texgyre` trên Ubuntu).

Chạy từ thư mục gốc repository:

```bash
./cookbook/build.sh all
```

Các target:

```bash
./cookbook/build.sh pdf    # cookbook/dist/system-engineering-cookbook.pdf
./cookbook/build.sh html   # cookbook/dist/system-engineering-cookbook.html
./cookbook/build.sh all
./cookbook/build.sh clean
```

HTML chỉ cần Pandoc. Target PDF cần thêm XeLaTeX. `dist/` là output sinh ra,
không phải source of truth.

## Quy ước nội dung

- **Hệ thống hiện có**: hành vi đã được xác nhận từ source hiện tại.
- **Khuyến nghị**: thiết kế production nên bổ sung, chưa mặc định có trong code.
- **Lab**: bài thực hành có preflight và cleanup.
- **Cảnh báo**: thao tác có thể làm mất dữ liệu hoặc mở rộng bề mặt tấn công.
- **Hint**: kinh nghiệm có thể áp dụng lại cho hệ thống khác.

