# Command cookbook {#chapter-commands}

Chương này dùng để tra nhanh. Ký hiệu rủi ro: **R0** chỉ đọc, **R1** tạo output
cục bộ, **R2** thay đổi service/dữ liệu có kiểm soát, **R3** có thể mất dữ liệu.

## Git, dependency và build

| Nơi | Lệnh | Mục đích | Risk/output |
|---|---|---|---|
| Local | `git status --short` | Xem thay đổi | R0 |
| Local/CI | `npm ci` | Cài đúng lockfile | R1, tạo `node_modules` |
| Local/CI | `npm run check` | JS check + typecheck | R0/R1 cache |
| Local/CI | `npm test` | Unit + architecture | R0 |
| Local/CI | `npm run build` | Tạo `dist/` | R1 |
| Test | `npm run test:integration` | API smoke trên DB cô lập | R2, bắt buộc `TEST_DATABASE_URL` |

`npm ci` phù hợp CI/release vì từ chối lockfile lệch; `npm install` phù hợp khi
cố ý thay dependency và cập nhật lockfile.

## PostgreSQL status và khám phá

```bash
pg_isready
psql "$DATABASE_URL" -XAtqc 'SELECT current_database(), current_user'
psql "$DATABASE_URL" -Xc '\dt'
psql "$DATABASE_URL" -Xc '\d users'
```

Nơi: local hoặc VPS. Risk R0. Output phải cho đúng database/user trước mọi thao
tác tiếp theo.

```bash
psql "$DATABASE_URL" -XAtqc \
  "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database();"
```

Risk R0; dùng để điều tra connection pressure.

## Database lifecycle

```bash
createdb ai_learn_jlpt_lab
DATABASE_URL=postgresql://localhost:5432/ai_learn_jlpt_lab npm run db:migrate
```

Nơi: local. Risk R2. Output migration phải là `APPLY` hoặc `SKIP` có chủ đích.

::: {.warning}
`dropdb` là R3. Chỉ chạy sau preflight:

```bash
target_db=ai_learn_jlpt_lab
case "$target_db" in
  *lab*|*test*)
    dropdb "$target_db"
    ;;
  *)
    echo 'Refused'
    exit 1
    ;;
esac
```
:::

## Backup và restore

```bash
pg_dump -Fc --no-owner --no-acl "$DATABASE_URL" -f app.dump
pg_restore --list app.dump >/dev/null
shasum -a 256 app.dump > app.dump.sha256
```

Nơi: local/VPS. Risk R1; đọc DB và tạo file chứa dữ liệu nhạy cảm. Output dump
phải quyền hạn chế và lưu ngoài Git.

```bash
createdb ai_learn_jlpt_restore_test
pg_restore --exit-on-error --no-owner --no-acl \
  -d postgresql://localhost:5432/ai_learn_jlpt_restore_test app.dump
```

Risk R2 trên DB mới. Không dùng `--clean` vào production nếu chưa có recovery
plan được review.

## HTTP và health

```bash
curl -i http://127.0.0.1:5050/health/live
curl -i http://127.0.0.1:5050/health/ready
curl --fail --silent --show-error https://learn.example.com/health/ready
```

Nơi: hai lệnh đầu trên VPS, lệnh cuối từ ngoài. Risk R0. So sánh internal và
public giúp khoanh vùng Nginx/DNS/TLS.

## systemd và journal

```bash
sudo systemctl status ai-learn-jlpt --no-pager
sudo journalctl -u ai-learn-jlpt -n 100 --no-pager
sudo journalctl -u ai-learn-jlpt -f
sudo systemctl list-timers 'ai-learn-jlpt*'
```

Risk R0. Restart là R2:

```bash
sudo systemctl restart ai-learn-jlpt
curl --fail http://127.0.0.1:5050/health/ready
```

Luôn theo restart bằng readiness; không coi command exit 0 là acceptance test.

## Port, process và resource

```bash
ss -ltnp
lsof -iTCP:5050 -sTCP:LISTEN
ps -ef | rg 'dist/server.js'
df -h
free -h
```

`ss/free` phổ biến trên Linux; `lsof` dùng tốt trên macOS. Risk R0.

## Nginx, DNS và TLS

```bash
sudo nginx -t
sudo systemctl reload nginx
dig +short learn.example.com
curl -Iv https://learn.example.com
sudo certbot renew --dry-run
```

`nginx -t`, DNS và curl là R0. Reload là R2 nhưng giữ connection tốt hơn restart.
Chỉ reload sau config test thành công.

## SSH và deploy

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
readlink -f /opt/ai-learn-jlpt/current
ls -lt /opt/ai-learn-jlpt/releases
```

Risk R0. Dùng fingerprint qua trusted console để tạo known-host secret.

Rollback app là R2 và phải xác nhận compatibility:

```bash
previous=/opt/ai-learn-jlpt/releases/REVIEWED_COMMIT_SHA
test -f "$previous/dist/server.js"
sudo -u deploy ln -sfn "$previous" /opt/ai-learn-jlpt/current.rollback
sudo -u deploy mv -Tf /opt/ai-learn-jlpt/current.rollback /opt/ai-learn-jlpt/current
sudo systemctl restart ai-learn-jlpt
curl --fail http://127.0.0.1:5050/health/ready
```

## Cách dùng cookbook khi incident

1. Bắt đầu R0: status, log, health, disk, DB connection.
2. Ghi evidence và release SHA.
3. Chọn action R2 nhỏ nhất có khả năng giảm impact.
4. R3 chỉ sau backup, target validation và peer review.

::: {.hint}
- Mọi lệnh automation cần `set -euo pipefail` và target cụ thể.
- Luôn phân biệt nơi chạy: local, CI, deploy user hay root.
- Lệnh thành công chưa phải hệ thống thành công; theo bằng checkpoint domain.
- Không copy lệnh R3 từ runbook mà bỏ preflight.
:::

Tiếp theo: [Capstone và checklist](#chapter-capstone).
