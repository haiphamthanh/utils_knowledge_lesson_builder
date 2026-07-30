# Vận hành và xử lý sự cố {#chapter-operations}

## Mục tiêu

Giữ hệ thống có thể quan sát, phục hồi và thay đổi an toàn sau go-live. Operations
không chỉ là restart; nó là vòng lặp detect → diagnose → mitigate → learn.

## Bốn tín hiệu đầu tiên

- **Traffic:** request rate và pattern.
- **Errors:** HTTP 5xx, auth anomalies, job failure.
- **Latency:** p50/p95/p99; tách app và database khi có thể.
- **Saturation:** CPU, RAM, disk, DB connections, event loop/pool queue.

VPS nhỏ chưa cần monitoring stack lớn. Structured journal, health check, disk
alert và external uptime check đã tạo giá trị. Thêm metrics stack khi câu hỏi vận
hành không còn trả lời được từ những nguồn đó.

## Evidence trước action

```bash
sudo systemctl status ai-learn-jlpt --no-pager
sudo journalctl -u ai-learn-jlpt --since '15 minutes ago' --no-pager
curl -i http://127.0.0.1:5050/health/live
curl -i http://127.0.0.1:5050/health/ready
df -h
free -h
```

Ghi timestamp, symptom, release SHA và action đã làm. Restart có thể giảm impact
nhưng xoá evidence tạm thời; thu thập log/status trước nếu incident cho phép.

## Playbook: app crash

1. Kiểm tra exit reason và restart count trong systemd/journal.
2. Xác định lỗi startup config, DB hay runtime exception.
3. Nếu liên quan release mới, xác nhận `current` và rollback artifact.
4. Nếu crash loop, dừng traffic/restart storm rồi điều tra.
5. Sau mitigate, thêm regression test hoặc guard.

## Playbook: PostgreSQL không ready

1. `/live` và `/ready` phân biệt process với dependency.
2. `pg_isready`, `systemctl status postgresql`, journal và disk.
3. Kiểm tra connection count/long transaction, không tăng pool mù quáng.
4. Không restart DB nếu chưa biết recovery/checkpoint impact.
5. Nếu corruption/loss, phục hồi vào database mới từ backup verified.

## Playbook: disk đầy

Disk đầy có thể làm app log lỗi, PostgreSQL ngừng write và backup fail. Xác định
consumer bằng `du` với target cụ thể. Không xoá PostgreSQL data/WAL thủ công.
Giảm log/backup cũ theo retention đã thiết kế, mở rộng disk nếu growth hợp lệ.

::: {.warning}
Không chạy lệnh xoá recursive trên `/`, `$HOME`, PostgreSQL data directory hoặc
path ghép từ biến chưa validate. “Giải phóng disk nhanh” có thể biến outage thành
mất dữ liệu.
:::

## Playbook: migration/release lỗi

- Migration transaction fail trước commit: app cũ vẫn active; sửa migration mới.
- Migration commit nhưng app mới fail: rollback app chỉ khi schema compatible.
- Release không ready: xem journal của đúng SHA, DB connectivity và assets.
- Không sửa migration đã apply; tạo migration correction.

## TLS và certificate

Theo dõi expiry từ bên ngoài. `certbot renew --dry-run` kiểm tra renewal path.
Nếu TLS lỗi, phân biệt DNS sai, port 80/443 bị chặn, Nginx config sai và rate limit
CA. Không tắt HTTPS để “tạm chạy” auth production.

## Backup operations

Backup hằng ngày giữ 14 ngày là baseline, không phải chiến lược hoàn chỉnh. Có
ít nhất một copy ngoài VPS và định kỳ restore drill. Theo dõi tuổi file backup,
size bất thường và exit status timer.

Recovery Point Objective (RPO) là lượng dữ liệu có thể mất; Recovery Time
Objective (RTO) là thời gian phục hồi chấp nhận được. Tần suất backup và runbook
phải xuất phát từ hai con số này.

## Khi nào scale

- Tách PostgreSQL khi tài nguyên/backup/availability cần failure domain riêng.
- Thêm replica app khi CPU/availability cần, sau khi session/data đã shared.
- Thêm cache khi query plan/index không đủ và cache invalidation rõ.
- Thêm queue khi công việc dài/retry làm request không ổn định.

## Lab: game day không phá dữ liệu

::: {.lab}
Trên môi trường test, lần lượt dừng app process, dùng DB URL sai và deploy một
artifact cố ý thiếu config. Với mỗi tình huống ghi: alert/symptom, lệnh thu thập
bằng chứng, automatic recovery, manual mitigation và regression guard.

Không mô phỏng disk full hoặc kill PostgreSQL production.
:::

## Tự kiểm tra

1. Vì sao restart không phải root-cause analysis?
2. RPO/RTO ảnh hưởng backup thế nào?
3. Khi nào thêm replica app chưa giải quyết availability?

::: {.hint}
- Quan sát theo traffic, errors, latency và saturation.
- Mọi incident nên tạo một guard mới: test, alert, limit hoặc runbook.
- Backup age là metric quan trọng hơn việc timer “active”.
- Scale sau khi đo bottleneck; thêm thành phần cũng thêm failure mode.
:::

Tiếp theo: [Command cookbook](#chapter-commands).

