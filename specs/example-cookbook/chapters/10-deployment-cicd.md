# Deploy và CI/CD {#chapter-deployment}

## Mục tiêu

Hiểu release như một state transition có checkpoint, không phải thao tác copy
file. Mỗi bước phải fail closed và để lại đường phục hồi.

## Topology VPS đơn

```text
DNS -> VPS :443 -> Nginx -> Node 127.0.0.1:5050 -> PostgreSQL localhost:5432
                         |                         |
                         + systemd restart        + daily backup

GitHub Actions -> SSH deploy user -> versioned release directories
```

Chỉ SSH/80/443 mở ở firewall. Node và PostgreSQL nghe loopback/private network.
Nginx kết thúc TLS và giữ public boundary nhỏ.

## Artifact và release directory

CI chạy `npm ci`, check, test và build. Artifact gồm `dist`, manifest/lockfile và
ops scripts. Host giải nén vào:

```text
/opt/ai-learn-jlpt/
  releases/<commit-sha>/
  current -> releases/<active-sha>/
  shared/
  incoming/
```

Versioned directory làm switch/rollback mã bằng symlink atomic. Không chép đè
file process đang dùng; không `git pull` và build tuỳ ý trên production.

## Thứ tự release

```text
verify artifact
  -> acquire deploy lock
  -> install production dependencies
  -> backup database
  -> apply forward migration
  -> atomically switch current
  -> restart service
  -> wait /health/ready
  -> keep or rollback application symlink
```

Backup trước migration vì migration là thay đổi state khó đảo. Switch sau
migration vì app mới có thể cần schema mới. Health gate sau restart vì
`systemctl restart` thành công chỉ chứng minh process được tạo, chưa chứng minh
app dùng được.

::: {.current}
`.github/workflows/deploy-production.yml` serialize production workflow, build
artifact rồi upload qua SSH. `remote-deploy.sh` dùng `flock`, backup predeploy,
migrate, switch symlink, chờ readiness và rollback app nếu release mới không
ready. systemd tự restart khi process crash; timer restart sau nhiều readiness
failure liên tiếp.
:::

## Secret và least privilege

GitHub environment giữ host, port, user, private key, known hosts và production
URL. `known_hosts` phải được đối chiếu fingerprint qua console tin cậy; nếu chỉ
chạy `ssh-keyscan` trên cùng network chưa xác minh, ta vẫn có thể lưu key của
attacker.

Deploy user sở hữu release directory nhưng sudo chỉ được start/stop/restart đúng
service/timer. App bind loopback port nên không cần root. Environment file DB có
quyền đọc hạn chế và không nằm trong artifact.

## systemd và Nginx

systemd định nghĩa command, user, working directory, environment, restart và
sandbox. Nginx proxy `Host`, client IP/proto và giới hạn body/timeout. Certbot
quản lý certificate lifecycle.

Cookie `Secure` phụ thuộc HTTPS end-to-end từ browser tới Nginx. Node có thể nhận
HTTP loopback nhưng public URL phải là HTTPS.

## Rollback nào?

Rollback application đổi symlink về artifact cũ. Migration forward đã chạy vẫn
còn đó. Vì vậy migration phải backward-compatible trong cửa sổ rollback hoặc
cần recovery procedure riêng.

Pattern expand/contract:

1. Expand schema, app cũ và mới cùng chạy được.
2. Deploy app dùng schema mới.
3. Backfill/quan sát.
4. Contract ở release sau khi không còn reader cũ.

## Lab: đọc release như state machine

::: {.lab}
Không deploy. Mở `.github/workflows/deploy-production.yml` và
`scripts/ops/remote-deploy.sh`, lập bảng cho từng bước: input, state mutation,
checkpoint, failure cleanup và rollback. Tìm các điểm trước/sau migration và
trước/sau switch symlink.
:::

::: {.checkpoint}
Bạn phải mô tả được trạng thái host nếu npm install, backup, migration, restart
hoặc readiness lần lượt thất bại. Nếu có trạng thái không rõ, automation chưa đủ
an toàn.
:::

## Failure modes

- CI xanh nhưng artifact thiếu migration/static assets.
- Hai workflow production chạy đồng thời.
- Host key không được pin.
- Migration destructive làm app cũ không rollback được.
- Public health check qua CDN vẫn xanh trong khi origin sai release.

## Tự kiểm tra

1. Vì sao build trên CI tốt hơn build lại trên host?
2. `systemctl restart` thành công khác readiness 200 thế nào?
3. Tại sao application rollback không tự động rollback database?

::: {.hint}
- Release là chuỗi checkpoint có state rõ ràng.
- Deploy lock và concurrency control giải quyết hai lớp khác nhau.
- Migration tương thích ngược là nền tảng rollback an toàn.
- Secret không được đóng gói cùng artifact mà nó bảo vệ.
:::

Tiếp theo: [Vận hành và xử lý sự cố](#chapter-operations).

