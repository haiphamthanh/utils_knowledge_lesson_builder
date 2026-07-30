# Mental model của một hệ thống web {#chapter-mental-model}

## Mục tiêu

Sau chương này, bạn có thể vẽ lại đường đi của một request, phân biệt source với
runtime và biết kiểm tra ở lớp nào khi người dùng báo “ứng dụng không chạy”.

## Bảy khái niệm đủ để bắt đầu

- **Client** tạo HTTP request; trong dự án này là JavaScript chạy trong browser.
- **Server** nhận request và tạo response; đây là process Node.js.
- **Process** là một chương trình đang chạy, có PID, memory và lifecycle.
- **Port** giúp hệ điều hành chuyển network traffic tới đúng process.
- **API** là hợp đồng giữa client và server: method, path, input, status, output.
- **Database** giữ state lâu dài qua các lần restart.
- **Environment** cung cấp cấu hình thay đổi theo nơi chạy như port và URL DB.

Một mô hình tối thiểu:

```text
Browser
  -> HTTPS :443
  -> Nginx reverse proxy
  -> HTTP 127.0.0.1:5050
  -> Node.js request handler
  -> PostgreSQL 127.0.0.1:5432
  <- JSON/HTML response
```

Nginx và Node đều là server nhưng ở hai boundary khác nhau. Nginx kết thúc TLS,
giới hạn request và proxy. Node hiểu domain rule. PostgreSQL thực thi constraint,
transaction và lưu state. Đặt đúng trách nhiệm giúp lỗi dễ cô lập.

## Source, build artifact và runtime

`src/` là thứ con người sửa. `scripts/build.js` dùng esbuild tạo `dist/`.
Production chạy `dist/server.js`, không chạy TypeScript từ `src/`.

```text
source + dependencies + build configuration
                  |
                  v
           reproducible build
                  |
                  v
       dist/server.js + dist/public + migrations
                  |
                  v
            production process
```

Điểm quan trọng là **build một lần, chạy cùng artifact**. Nếu mỗi host tự build
theo dependency và tool version khác nhau, “cùng commit” chưa chắc là cùng phần
mềm.

## Theo dấu một request thật

Với `GET /api/lessons`, đường đi khái quát là:

1. `src/index.ts` nhận request, gắn security headers và đo thời gian.
2. `src/modules/request-context.ts` đọc cookie, tìm user và tạo request ID.
3. `src/modules/index.ts` tập hợp endpoint registry.
4. `src/lib/dispatcher.ts` khớp method/path và kiểm tra access metadata.
5. Controller chuyển HTTP input thành lời gọi domain/repository.
6. Repository gọi `src/lib/database.js` bằng parameterized SQL.
7. Response đi ngược lại; logger ghi status và duration.

Nếu path đúng nhưng method sai, dispatcher trả `405` và header `Allow`. Nếu
không đăng nhập ở endpoint `user`, nó trả `401`; user thường gọi endpoint
`admin` nhận `403`. Đây là hợp đồng, không phải chi tiết UI.

::: {.current}
Endpoint được khai báo bằng `{ method, pattern, access, controller }`. Access có
ba mức `public`, `user`, `admin`. Unknown `/api/*` luôn trả JSON `404`, không rơi
về HTML của frontend.
:::

## Liveness, readiness và shutdown

`/health/live` trả lời “process còn phục vụ HTTP không?”. `/health/ready` còn
query `SELECT 1`, nên trả lời “process có đủ dependency để nhận traffic không?”.
Không trộn hai khái niệm: database tạm down không nhất thiết có nghĩa process đã
chết.

Khi nhận `SIGTERM`, server dừng nhận kết nối mới, đóng connection còn lại sau
timeout rồi đóng DB pool. Đây là graceful shutdown. Nếu gọi `kill -9`, ứng dụng
không có cơ hội hoàn tất quy trình đó.

## Lab: truy dấu endpoint

::: {.lab}
**Preflight:** đứng tại root repository; lab chỉ đọc source.

```bash
rg -n 'pattern: "/health/ready"' src/modules
rg -n 'handleReadiness|SELECT 1' src/modules
rg -n 'dispatchEndpoint' src
rg -n 'createRequestContext' src
```

Với mỗi kết quả, ghi lại input và output của tầng đó. Tiếp tục với một endpoint
có `access: "user"` và tìm query cuối cùng.
:::

::: {.checkpoint}
Bạn phải chỉ ra được nơi path được match, nơi access được chặn và nơi PostgreSQL
được gọi. Nếu chưa, đừng bắt đầu sửa endpoint.
:::

## Failure modes

| Triệu chứng | Lớp kiểm tra đầu tiên |
|---|---|
| Domain không mở | DNS, firewall, Nginx |
| `502 Bad Gateway` | Node process/port |
| `/live` 200, `/ready` 500 | PostgreSQL/config |
| API 401 | Cookie/session |
| API 403 | Role/ownership |
| HTML cũ sau deploy | Artifact/cache/release symlink |

## Tự kiểm tra

1. Tại sao port 5050 không nên mở ra Internet khi đã có Nginx?
2. Tại sao source chạy được không chứng minh artifact production chạy được?
3. Một database outage nên làm liveness hay readiness thất bại?

::: {.hint}
- Tìm entrypoint, request flow, data store và process manager trước khi đọc chi tiết.
- Dùng request ID để nối log giữa các boundary.
- Health check phải kiểm tra đúng thứ bạn định tự động phục hồi.
- Một lỗi được khoanh vùng tốt có giá trị hơn một lần restart may mắn.
:::

Tiếp theo: [Thiết kế hệ thống nhiều người dùng](#chapter-multi-user).

