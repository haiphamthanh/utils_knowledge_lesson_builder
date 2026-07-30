# Ghép các thành phần thành hệ thống {#chapter-components}

## Mục tiêu

Nhìn codebase như các boundary cộng tác thay vì một danh sách file. Mục tiêu của
kiến trúc không phải tạo nhiều layer, mà là đặt mỗi quyết định ở đúng nơi.

## Dependency map

```text
Browser UI
   |
HTTP controller + endpoint metadata
   |
Domain service / use-case
   |
Repository contract
   |
PostgreSQL adapter

Cross-cutting: config, logger, auth context, error mapping, build
```

- Controller hiểu HTTP nhưng không nên chứa SQL dài.
- Service hiểu use-case nhưng không nên biết cookie/header.
- Repository hiểu persistence và ownership query.
- Composition root nối dependency và đăng ký endpoint.

Layer không cần là class hoặc framework. Trong dự án, TypeScript được dùng ở
HTTP/composition boundary; service/repository JavaScript vẫn có public contract
rõ. Boundary quan trọng hơn đuôi file.

## Request flow và failure boundary

```text
request
  -> validate config/request
  -> resolve identity
  -> authorize endpoint
  -> execute domain action
  -> query transactionally
  -> map result/error
  -> structured log + response
```

Mỗi bước phải trả lời: input tin cậy đến đâu, error nào có thể xảy ra, log gì mà
không lộ secret, và retry có an toàn không.

## Config

Config thay đổi theo environment; code behavior/invariant nằm trong source.
`HOST`, `PORT`, `DATABASE_URL`, pool size và timeout là config. SQL table name,
cookie security policy production hay access rule không nên được biến thành một
biến tuỳ tiện chỉ để “linh hoạt”.

Validate config trước listen. Fail fast tạo lỗi rõ ở deploy thay vì lỗi ngẫu
nhiên ở request đầu tiên.

## Error và log

Error nội bộ cần context để điều tra; response public cần ổn định và không lộ
stack/SQL. Structured log của request nên có request ID, method, path, status,
duration. Không log cookie, password, token hoặc toàn bộ request body.

Request ID giúp ghép `request_failed` với log proxy và client report. Chỉ chấp
nhận request ID đầu vào có charset/length an toàn; nếu không, tự sinh UUID.

## Build và static assets

Build script bundle backend, browser JS/CSS, copy HTML/config và migrations vào
`dist/`. Artifact production phải chứa đủ:

- `dist/server.js`.
- `dist/public/`.
- `dist/bin/migrate.js`.
- `dist/migrations/`.
- Production dependencies theo lockfile.

Smoke test artifact tìm lỗi mà unit test source không thấy: asset thiếu, path
resolution sai hoặc migration không được đóng gói.

## Security và resilience là thành phần

Security headers, body limit, ownership filter và parameter binding không phải
“cleanup sau”. Health check, timeout, shutdown, backup và restart cũng là một
phần thiết kế. Một feature không hoàn thành nếu chỉ có happy path controller.

::: {.current}
Architecture tests ngăn import xuyên boundary, dispatcher thống nhất access và
smoke suite kiểm tra auth, CMS, image ownership cùng nhiều loại private learning
data. Production process chạy artifact `dist/`.
:::

## Lab: thiết kế endpoint trước khi code

::: {.lab}
Thiết kế `POST /api/manual-notes/:id/archive` trên giấy:

1. Endpoint metadata: method, pattern, access.
2. Request context: identity nào được dùng.
3. Validation: ID và state transition.
4. Repository query có `id` + `user_id`.
5. Response codes cho anonymous, non-owner, missing và success.
6. Log fields, không log content.
7. Test matrix và migration nếu cần column mới.

Sau đó chỉ ra file/boundary sẽ thay đổi; không cần viết code.
:::

::: {.checkpoint}
Thiết kế đạt khi reviewer có thể kiểm tra ownership và failure behavior mà không
cần đoán controller sẽ “nhớ làm đúng”.
:::

## Failure modes

- Controller vừa parse HTTP, vừa query, vừa quyết định business rule.
- Shared module import internal repository của feature khác.
- Catch mọi error và trả 200 với `{error}`.
- Build production khác lệnh được CI kiểm tra.
- Health endpoint luôn 200 dù dependency bắt buộc đã chết.

## Tự kiểm tra

1. Boundary nào nên biết cookie?
2. Tại sao migration phải nằm trong artifact?
3. Request ID giải quyết vấn đề quan sát nào?

::: {.hint}
- Kiến trúc tốt làm policy dễ tìm và test, không tối đa số layer.
- Composition root là nơi dependency gặp nhau; domain không nên tự tìm dependency.
- Build artifact là sản phẩm deploy, không phải thư mục phụ.
- Hoàn thiện vertical slice gồm auth, data, error, test và operation.
:::

Tiếp theo: [Chọn framework, OS và plugin](#chapter-tool-selection).

