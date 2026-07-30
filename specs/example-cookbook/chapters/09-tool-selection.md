# Chọn framework, OS và plugin {#chapter-tool-selection}

## Mục tiêu

Chọn công cụ theo constraint và operational cost. “Phổ biến” không có nghĩa phù
hợp; dependency mới luôn tạo thêm update, security và failure surface.

## Framework HTTP

| Lựa chọn | Điểm mạnh | Chi phí | Dùng khi |
|---|---|---|---|
| Native Node HTTP | Ít dependency, hiểu rõ protocol | Tự xây routing/middleware | API nhỏ, contract ổn định |
| Express | Ecosystem lớn, quen thuộc | Middleware quality không đồng đều | Team cần convention phổ biến |
| Fastify | Validation/plugin model, hiệu năng | Học lifecycle/plugin | API tăng nhanh, cần schema |
| NestJS | DI/module/convention mạnh | Nặng và nhiều abstraction | Team lớn, domain/module phức tạp |

Native HTTP hiện tại không phải thiếu framework; nó là một lựa chọn có chủ đích.
Chuyển framework chỉ đáng giá nếu vấn đề lặp lại như validation, plugin lifecycle
hoặc team convention lớn hơn migration cost.

## Database access

Raw SQL với `pg` cho query rõ, tận dụng PostgreSQL và ít abstraction. Query
builder hỗ trợ composition/type nhưng vẫn cần hiểu SQL. ORM tăng tốc CRUD và
relation phổ biến nhưng không xoá nhu cầu hiểu transaction, index hoặc plan.

Chọn ORM khi productivity/schema tooling thắng chi phí generated query và
migration convention. Không thêm ORM chỉ để tránh học SQL — người trực production
vẫn phải đọc query và lock.

## Process và packaging

- **systemd**: có sẵn trên Ubuntu, restart, log, sandbox, timer; phù hợp VPS.
- **PM2**: tiện cho Node cluster/UI nhưng trùng nhiều trách nhiệm với systemd.
- **Docker**: artifact và isolation nhất quán; thêm registry, image, volume,
  network và update lifecycle.

Một VPS đơn không cần đồng thời PM2, Docker và systemd quản lý cùng process.
Trong case study, systemd chạy Node artifact là đường ngắn và dễ điều tra.

## Reverse proxy và OS

Nginx mature, explicit và có hệ sinh thái lớn. Caddy đơn giản hoá automatic TLS.
Nếu provision/runbook đã dùng Nginx ổn định, đổi proxy chỉ vì config ngắn hơn ít
tạo giá trị.

Ubuntu/Debian có package/documentation phù hợp server phổ thông. Alpine nhỏ hơn
nhưng musl và package khác có thể làm native dependency khó debug. Image nhỏ
không tự động đồng nghĩa hệ thống rẻ hơn nếu thời gian vận hành tăng.

## Khi nào thêm thành phần

| Thành phần | Signal thực tế |
|---|---|
| Redis cache | Đã đo query nóng, cache semantics/invalidations rõ |
| Queue/worker | Công việc chậm cần retry, không nằm trong request latency |
| Object storage | Binary lớn, cần CDN/lifecycle/scale độc lập DB |
| External IdP | SSO doanh nghiệp, federation hoặc compliance |
| Multiple replicas | Availability/throughput đã vượt một process |
| Kubernetes | Nhiều service/team cần orchestration chuẩn, không phải một VPS |

## Dependency gate

Trước khi cài package/plugin, trả lời:

1. Vấn đề cụ thể và metric nào chứng minh?
2. Có thể giải bằng platform/20 dòng code rõ ràng không?
3. Package có maintainer, release và security policy còn hoạt động không?
4. Có bao nhiêu transitive dependency và quyền runtime nào?
5. Test/upgrade/rollback ai sở hữu?
6. Nếu package dừng, exit strategy là gì?

::: {.current}
Runtime dự án chỉ có dependency `pg`. esbuild, TypeScript và `tsx` là development
dependencies. Nginx/systemd/PostgreSQL xử lý trách nhiệm hạ tầng thay vì thêm
package Node tương đương.
:::

## Bộ cài tối thiểu

**Development:** Git, Node 22, npm, PostgreSQL client/server, editor. Pandoc và
XeLaTeX chỉ cần nếu build sách.

**VPS đơn:** Node runtime, PostgreSQL, Nginx, Certbot, curl và systemd có sẵn.
Không cài compiler/dev dependency sau khi artifact đã build.

**CI:** checkout, Node, npm; build/test/package rồi dùng OpenSSH có sẵn để deploy.

## Lab: architecture decision record

::: {.lab}
Chọn một đề xuất như “thêm Redis” và viết ADR một trang: context, decision,
alternatives, evidence, operational cost, rollback và trigger review lại. Nếu
không có metric/constraint cụ thể, decision mặc định là chưa thêm.
:::

## Tự kiểm tra

1. Docker giải quyết vấn đề nào mà systemd deployment hiện tại chưa giải quyết?
2. ORM có loại bỏ nhu cầu migration review không?
3. Signal nào hợp lý để thêm queue?

::: {.hint}
- Tối ưu tổng chi phí sở hữu, không tối ưu số dòng config.
- Ưu tiên primitive của OS/database trước dependency cùng chức năng.
- Một công cụ mới phải có owner, upgrade path và failure playbook.
- Trì hoãn dependency là quyết định kiến trúc hợp lệ khi evidence chưa đủ.
:::

Tiếp theo: [Deploy và CI/CD](#chapter-deployment).

