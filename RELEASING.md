# Phát hành bản cập nhật ZimTube

Trình cập nhật trong ZimTube đọc **GitHub Releases** của repository
`mxtmod-lab/ZimTube`. Mỗi release phải có đúng hai asset:

- `ZimTube-update.zip`
- `ZimTube-update.zip.sha256`

## 1. Tăng phiên bản

Sửa `APP_VERSION` trong `zt/version.py`, dùng Semantic Versioning:

- Patch: `1.0.0` → `1.0.1` cho sửa lỗi.
- Minor: `1.0.0` → `1.1.0` cho tính năng mới.
- Major: `1.0.0` → `2.0.0` cho thay đổi không tương thích.

Tag GitHub phải tương ứng, ví dụ `v1.1.0`.

## 2. Cấu trúc ZIP

Các file phải nằm ngay ở gốc ZIP, không lồng thêm thư mục bắt buộc:

```text
app.py
launch.sh
config.json
icon.png
assets/
bin/
libs/       (nếu có)
vendor/
zt/
```

Không đưa `.git`, cache, file người dùng hoặc video offline vào gói.

Ví dụ tạo gói từ thư mục cha của `ZimTube`:

```sh
zip -r ZimTube-update.zip \
  ZimTube/app.py ZimTube/launch.sh ZimTube/config.json \
  ZimTube/icon.png ZimTube/assets ZimTube/bin ZimTube/vendor ZimTube/zt
```

Trình cài chấp nhận cả cấu trúc có một thư mục `ZimTube/` bọc ngoài.

## 3. Tạo checksum

Trên macOS:

```sh
shasum -a 256 ZimTube-update.zip > ZimTube-update.zip.sha256
```

Trên Linux:

```sh
sha256sum ZimTube-update.zip > ZimTube-update.zip.sha256
```

## 4. Tạo GitHub Release

1. Push mã nguồn và tag phiên bản.
2. Mở **Releases → Draft a new release**.
3. Chọn tag như `v1.1.0`.
4. Ghi changelog ngắn gọn bằng tiếng Việt.
5. Đính kèm chính xác hai asset nói trên.
6. Publish release.

Sau khi phát hành, trên máy chọn:

**MENU → Kiểm tra cập nhật → A Tải bản mới → A Cập nhật**

## An toàn

- Gói chỉ được cài nếu SHA-256 khớp.
- ZIP có đường dẫn `..`, đường dẫn tuyệt đối hoặc symbolic link sẽ bị từ chối.
- App hiện tại được sao lưu trước khi thay thế.
- Nếu bản mới không compile được, installer tự rollback.
- `/mnt/SDCARD/.zimtube` và `/mnt/SDCARD/Videos/ZimTube` không bị thay đổi.
