# Capstone và checklist {#chapter-capstone}

## Mục tiêu

Ghép các phần thành một vòng đời duy nhất và tự đánh giá khả năng giải thích,
thực hiện, chẩn đoán và phục hồi hệ thống.

## Capstone: từ login tới recovery

```text
login -> cookie -> request context -> authorization -> create note
      -> PostgreSQL -> build -> release -> readiness -> backup/restore
```

::: {.warning}
Phần cleanup có `dropdb`. Chỉ chạy khi cả hai tên database hiển thị rõ ràng và
đều chứa `capstone_test`; không thay bằng biến hoặc URL production.
:::

::: {.lab}
**Môi trường:** local server và database có tên chứa `capstone_test`. Không dùng
credential/dump production.

### 1. Chuẩn bị

```bash
createdb ai_learn_jlpt_capstone_test
export TEST_DATABASE_URL=postgresql://localhost:5432/ai_learn_jlpt_capstone_test
DATABASE_URL="$TEST_DATABASE_URL" npm run db:migrate
```

### 2. Identity và ownership

Chạy app bằng test DB. Đăng ký A/B với hai cookie jar. A tạo note; B thử truy cập
ID đó; A đọc lại. Ghi status và query chứng minh owner không đổi.

### 3. Artifact

```bash
npm run check
npm test
npm run build
DATABASE_URL="$TEST_DATABASE_URL" SMOKE_ENTRY=dist/server.js \
  node scripts/qa/smoke-test.js
```

Xác nhận `dist/server.js`, public HTML và migration runner tồn tại.

### 4. Backup/recovery

```bash
pg_dump -Fc --no-owner --no-acl "$TEST_DATABASE_URL" -f /tmp/capstone.dump
pg_restore --list /tmp/capstone.dump >/dev/null
createdb ai_learn_jlpt_capstone_restore_test
pg_restore --exit-on-error --no-owner --no-acl \
  -d postgresql://localhost:5432/ai_learn_jlpt_capstone_restore_test \
  /tmp/capstone.dump
```

Chạy migration + smoke trên DB restore. So sánh marker data và migration count.

### 5. Cleanup

```bash
dropdb ai_learn_jlpt_capstone_restore_test
dropdb ai_learn_jlpt_capstone_test
rm -f /tmp/capstone.dump
unset TEST_DATABASE_URL
```
:::

::: {.checkpoint}
Capstone đạt khi bạn có evidence cho auth cookie, cross-user isolation, artifact,
health, backup validity và restored application — không chỉ một danh sách command
exit 0.
:::

## Maturity matrix

| Mức | Đặc điểm | Bước tiếp theo khi có signal |
|---|---|---|
| Local | Một process, local DB | Test DB, reproducible build |
| VPS production | Nginx, TLS, systemd, backup, CI/CD | External backup/monitoring |
| Resilient single region | DB managed/tách host, nhiều app replica | Pool/capacity/session review |
| Distributed | Queue/cache/object storage/observability | Chỉ thêm theo workload |

Không nhảy level vì xu hướng. Mỗi level làm tăng chi phí deploy, data consistency,
security và incident coordination.

## Checklist kiến thức

- [ ] Vẽ được request flow từ browser tới DB.
- [ ] Phân biệt authentication, authorization, role và ownership.
- [ ] Giải thích password salt/hash và session token hash.
- [ ] Giải thích 401, 403 và non-owner behavior.
- [ ] Viết private query luôn scope `user_id`.
- [ ] Dùng transaction trên cùng DB client.
- [ ] Đọc constraint, index và query plan cơ bản.
- [ ] Tính tổng pool connection khi tăng replica.
- [ ] Viết migration forward và review lock/compatibility.
- [ ] Backup, validate và restore vào database mới.
- [ ] Phân biệt source, artifact và active release.
- [ ] Phân biệt liveness, readiness và process status.
- [ ] Mô tả rollback app và giới hạn với database.
- [ ] Thu thập evidence trước action trong incident.

## Security review

- [ ] Password/token/credential không xuất hiện trong log hoặc response.
- [ ] Production cookie có `HttpOnly`, `Secure`, `SameSite` phù hợp.
- [ ] Login có rate limit/backoff theo threat model.
- [ ] Reset/verification token được hash, có TTL và one-time consume.
- [ ] Mọi private CRUD được test owner/non-owner.
- [ ] Admin action có access guard và audit.
- [ ] DB/app không public port không cần thiết.
- [ ] Deploy key và sudo theo least privilege.
- [ ] Secret không nằm trong source/artifact.

## Database và go-live review

- [ ] Constraint phản ánh invariant quan trọng.
- [ ] Query dùng parameter binding.
- [ ] Index gắn với query thật và đã xem plan.
- [ ] Migration đã thử trên bản sao dữ liệu.
- [ ] Predeploy backup verified.
- [ ] Restore drill thành công.
- [ ] DNS, TLS, Nginx và external readiness đều đúng.
- [ ] systemd service, health timer và backup timer active.
- [ ] Login, CMS, private data và image path được smoke test.
- [ ] Có bản backup ngoài VPS và owner nhận alert.

## Câu hỏi tình huống

1. `/live` 200 nhưng `/ready` 500: thu thập gì trước?
2. Release mới migration thành công nhưng app fail: điều kiện nào cho phép rollback?
3. User B update được note A nhưng không list được: boundary nào có khả năng sai?
4. Tăng từ 1 lên 8 replica và DB bắt đầu từ chối connection: tính lại gì?
5. Backup timer active nhưng file mới nhất ba ngày tuổi: hệ thống đang xanh không?

## Những thứ chưa cần vội dùng

- **JWT:** session DB đang đáp ứng browser app và revoke tốt.
- **Redis:** chưa có query/latency evidence hoặc cache policy.
- **ORM:** raw SQL nhỏ, rõ và được test.
- **Microservices:** module boundary chưa cần network boundary.
- **Kubernetes:** một VPS/systemd còn đáp ứng topology.
- **MFA:** ưu tiên rate limit, reset lifecycle và admin threat trước; thêm khi risk yêu cầu.

::: {.hint}
- Nắm invariant và failure mode trước syntax công cụ.
- Một hệ thống trưởng thành khi có thể thay đổi và phục hồi có kiểm chứng.
- “Chưa cần” là kết luận kỹ thuật, không phải thiếu tham vọng.
- Khi gặp codebase mới: vẽ request flow, data ownership, failure boundary và
  operational loop — bốn bản đồ này mở gần như mọi ngõ ngách.
:::
