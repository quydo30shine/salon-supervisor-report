# Báo cáo nghiệm thu Salon Supervisor (Uốn Nhuộm Dưỡng)

Báo cáo web tương tác hiển thị: salesup đi salon nào ngày nào, tiến độ hoàn thành checklist nghiệm thu, và ảnh nghiệm thu thật tải từ Lark Base. Tự động cập nhật mỗi ngày qua GitHub Actions.

## Cách hoạt động

```
Lark Base ──(GitHub Actions chạy theo lịch)──> sync_lark.py
   │  gọi Lark API, tải dữ liệu + ảnh
   ▼
data.json + images/  ──commit──> repo  ──GitHub Pages──> link báo cáo
```

- `index.html` — báo cáo (web tĩnh, không cần server).
- `sync_lark.py` — gọi Lark API, ghi `data.json` và tải ảnh vào `images/`.
- `.github/workflows/sync.yml` — chạy `sync_lark.py` mỗi ngày 09:00 (giờ VN) hoặc bấm tay.
- `data.json` — dữ liệu báo cáo (hiện đang là MẪU từ CSV; sẽ bị ghi đè khi sync Lark).
- `build_sample_from_csv.py` — chỉ để tạo data MẪU từ file CSV (không cần sau khi nối Lark).

## Cài đặt 1 lần

### 1. Tạo Lark custom app & lấy thông tin
Trên Lark Developer (https://open.larksuite.com/app):
1. Tạo **Custom App** → lấy **App ID** và **App Secret**.
2. Vào *Permissions*, bật quyền: `bitable:app:readonly` (đọc Base) và `drive:drive:readonly` (tải file đính kèm). Publish app.
3. Mở Base cần báo cáo, bấm **... → Add collaborator / share** thêm app vừa tạo với quyền đọc.
4. Lấy `app_token` và `table_id` từ URL của Base:
   `https://xxx.larksuite.com/base/<APP_TOKEN>?table=<TABLE_ID>&view=...`

### 2. Đẩy code lên GitHub
```bash
cd salon-report
git init
git add .
git commit -m "Khởi tạo báo cáo nghiệm thu salon"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

### 3. Khai báo Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**, thêm:

| Tên | Giá trị |
|-----|---------|
| `LARK_APP_ID` | App ID |
| `LARK_APP_SECRET` | App Secret |
| `LARK_APP_TOKEN` | app_token của Base |
| `LARK_TABLE_ID` | table_id của bảng |
| `LARK_DOMAIN` | *(tùy chọn)* `open.larksuite.com` (mặc định) hoặc `open.feishu.cn` |

### 4. Bật GitHub Pages
Repo → **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` / `/ (root)` → Save.
Link báo cáo: `https://<USER>.github.io/<REPO>/`

### 5. Chạy đồng bộ lần đầu
Repo → tab **Actions** → workflow *"Sync Lark -> Báo cáo"* → **Run workflow**.
Sau khi chạy xong, `data.json` và `images/` được cập nhật, mở link Pages để xem.

## Cập nhật hàng ngày
Tự động chạy lúc 09:00 VN mỗi ngày. Muốn cập nhật ngay: vào **Actions → Run workflow**.

## Chạy thử ở máy (tùy chọn)
```bash
set LARK_APP_ID=...        # Windows: dùng set; Linux/Mac: export
set LARK_APP_SECRET=...
set LARK_APP_TOKEN=...
set LARK_TABLE_ID=...
python sync_lark.py
# rồi mở index.html (hoặc: python -m http.server 8000 và mở http://localhost:8000)
```

## Chỉnh sửa danh mục checklist
Sửa danh sách `CHECKLIST` trong cả `sync_lark.py` (và `build_sample_from_csv.py` nếu dùng) — đổi tên cột cho khớp tên field trong Lark, hoặc thêm/bớt mục.
