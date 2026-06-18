# -*- coding: utf-8 -*-
"""
Đồng bộ dữ liệu từ Lark Base (Bitable) -> data.json + tải ảnh nghiệm thu về thư mục images/.
Chạy local hoặc trong GitHub Actions.

Biến môi trường cần có (đặt trong GitHub Secrets):
  LARK_APP_ID      - App ID của Lark custom app
  LARK_APP_SECRET  - App Secret
  LARK_APP_TOKEN   - app_token của Base (lấy từ URL Base)
  LARK_TABLE_ID    - table_id của bảng (lấy từ URL Base)
  LARK_DOMAIN      - (tùy chọn) open.larksuite.com (mặc định, bản quốc tế) hoặc open.feishu.cn

Chạy:  python sync_lark.py
"""
import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")  # tránh lỗi encoding tiếng Việt trên console Windows
except Exception:
    pass

# ------- CẤU HÌNH CHECKLIST: key -> (tên cột trong Lark, nhãn hiển thị) -------
CHECKLIST = [
    ("front",         "Nghiệm thu trưng bày SP: Quầy mặt tiền",       "Trưng bày - Quầy mặt tiền"),
    ("reception",     "Nghiệm thu quầy trưng bày: Quầy lễ tân",       "Trưng bày - Quầy lễ tân"),
    ("stylist",       "Nghiệm thu quầy trưng bày: Khu Stylist",       "Trưng bày - Khu Stylist"),
    ("relax",         "Vật tư Relax/Spa",                             "Vật tư Relax/Spa"),
    ("und",           "Vật tư UND",                                   "Vật tư UND"),
    ("ctkm",          "Nghiệm thu triển khai CTKM",                   "Triển khai CTKM"),
    ("training",      "Nghiệm thu training/đào tạo tại salon",        "Training tại salon"),
    ("price",         "Nghiệm thu ấn phẩm - Bảng giá",                "Ấn phẩm - Bảng giá"),
    ("skinner_equip", "Nghiệm thu vật tư máy móc, quy trình Skinner", "Vật tư/máy móc Skinner"),
]
COL_DATE     = "Ngày Training"
COL_SUBMIT   = "Submitted on"
COL_SALESUP  = "Nhân sự Training"
COL_SALON    = "Chọn Salon:"
COL_MISSING  = "Vật tư, Sản phẩm bán thiếu"
COL_SK_CHECK = "Số skinner chấm trong ngày"
COL_SK_TRAIN = "Số nhân sự đào tạo trong ngày"
COL_MENU     = "Salon có gặp vấn đề nào về Menu, Ấn phẩm không"

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "images")

DOMAIN = os.environ.get("LARK_DOMAIN", "open.larksuite.com").strip()
APP_ID = os.environ.get("LARK_APP_ID", "").strip()
APP_SECRET = os.environ.get("LARK_APP_SECRET", "").strip()
APP_TOKEN = os.environ.get("LARK_APP_TOKEN", "").strip()
TABLE_ID = os.environ.get("LARK_TABLE_ID", "").strip()
# Chỉ sync nghiệm thu của tháng này. Dạng "YYYY-MM" (vd 2026-06) hoặc "MM" (vd 06 = tháng 6 bất kỳ năm).
SYNC_MONTH = os.environ.get("SYNC_MONTH", "").strip() or "2026-06"


def api(method, path, token=None, body=None, raw=False):
    url = f"https://{DOMAIN}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        if raw:
            return r.read()
        return json.loads(r.read().decode("utf-8"))


def get_token():
    res = api("POST", "/open-apis/auth/v3/tenant_access_token/internal",
              body={"app_id": APP_ID, "app_secret": APP_SECRET})
    if res.get("code") != 0:
        raise RuntimeError(f"Lấy token thất bại: {res}")
    return res["tenant_access_token"]


def list_records(token):
    records, page = [], None
    while True:
        q = {"page_size": 200}
        if page:
            q["page_token"] = page
        path = (f"/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
                f"?{urllib.parse.urlencode(q)}")
        res = api("GET", path, token=token)
        if res.get("code") != 0:
            raise RuntimeError(f"Đọc records thất bại: {res}")
        d = res.get("data", {})
        records.extend(d.get("items", []))
        if d.get("has_more") and d.get("page_token"):
            page = d["page_token"]
        else:
            break
    return records


def safe_name(s):
    return re.sub(r'[^0-9A-Za-z._-]', '_', s)[:120]


def download_media(token, file_token, name):
    """Tải 1 file đính kèm về images/. Trả về đường dẫn tương đối hoặc None."""
    ext = os.path.splitext(name or "")[1] or ".jpg"
    fname = safe_name(file_token) + ext
    fpath = os.path.join(IMG_DIR, fname)
    rel = "images/" + fname
    if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
        return rel  # đã tải trước đó -> bỏ qua
    try:
        # đính kèm trong Bitable cần tham số extra=bitablePerm để được phép tải
        extra = urllib.parse.quote(json.dumps({"bitablePerm": {"tableId": TABLE_ID, "rev": 0}}))
        blob = api("GET", f"/open-apis/drive/v1/medias/{file_token}/download?extra={extra}",
                   token=token, raw=True)
        with open(fpath, "wb") as f:
            f.write(blob)
        return rel
    except Exception as e:
        print(f"  ! Loi tai anh {file_token}: {e}")
        return None


def field_text(val):
    """Chuyển field text/number/select về chuỗi."""
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        parts = []
        for x in val:
            if isinstance(x, dict):
                parts.append(x.get("text") or x.get("name") or "")
            else:
                parts.append(str(x))
        return ", ".join(p for p in parts if p).strip()
    if isinstance(val, dict):
        return (val.get("text") or val.get("name") or "").strip()
    return str(val)


def field_attachments(val):
    """Nếu field là đính kèm -> trả list (file_token, name); không thì []."""
    out = []
    if isinstance(val, list):
        for x in val:
            if isinstance(x, dict) and x.get("file_token"):
                out.append((x["file_token"], x.get("name", "")))
    return out


def fmt_date(val):
    if isinstance(val, (int, float)) and val > 10_000_000_000:  # ms timestamp
        t = time.gmtime(val / 1000 + 7 * 3600)  # UTC+7
        return time.strftime("%d/%m/%Y", t)
    return field_text(val)


def parse_ym(val):
    """Trả (year, month) từ field ngày; (None, None) nếu không đọc được."""
    if isinstance(val, (int, float)) and val > 10_000_000_000:
        t = time.gmtime(val / 1000 + 7 * 3600)
        return (t.tm_year, t.tm_mon)
    s = field_text(val)
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)  # dd/mm/yyyy
    if m:
        return (int(m.group(3)), int(m.group(2)))
    m = re.search(r'(\d{4})[/-](\d{1,2})', s)         # yyyy/mm hoặc yyyy-mm
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (None, None)


def match_month(y, mo):
    if mo is None:
        return False
    if "-" in SYNC_MONTH:
        yy, mm = SYNC_MONTH.split("-")
        return y == int(yy) and mo == int(mm)
    return mo == int(SYNC_MONTH)


def main():
    missing = [k for k, v in {
        "LARK_APP_ID": APP_ID, "LARK_APP_SECRET": APP_SECRET,
        "LARK_APP_TOKEN": APP_TOKEN, "LARK_TABLE_ID": TABLE_ID}.items() if not v]
    if missing:
        print("THIEU bien moi truong: " + ", ".join(missing))
        print("Hay dat trong GitHub Secrets hoac export truoc khi chay.")
        sys.exit(1)

    os.makedirs(IMG_DIR, exist_ok=True)
    print(f"Domain: {DOMAIN}")
    token = get_token()
    print("Da lay tenant_access_token.")
    records = list_records(token)
    print(f"Doc duoc {len(records)} ban ghi.")

    visits = []
    img_total = 0
    skipped = 0
    skipped_dates = []
    for i, rec in enumerate(records):
        f = rec.get("fields", {})
        salon = field_text(f.get(COL_SALON))
        salesup = field_text(f.get(COL_SALESUP))
        if not salon and not salesup:
            continue
        # chỉ giữ nghiệm thu của tháng cần sync
        y, mo = parse_ym(f.get(COL_DATE))
        if not match_month(y, mo):
            skipped += 1
            skipped_dates.append(fmt_date(f.get(COL_DATE)) or "(trống)")
            continue
        items, done = {}, 0
        for key, col, _label in CHECKLIST:
            val = f.get(col)
            atts = field_attachments(val)
            images = []
            for ftok, name in atts:
                rel = download_media(token, ftok, name)
                if rel:
                    images.append(rel)
                    img_total += 1
            is_done = bool(atts) or bool(field_text(val))
            if is_done:
                done += 1
            items[key] = {
                "done": is_done,
                "images": images,
                "count": len(atts),
                "raw": "" if atts else field_text(val),
            }
        visits.append({
            "id": rec.get("record_id", f"r{i+1}"),
            "date": fmt_date(f.get(COL_DATE)),
            "submitted_on": field_text(f.get(COL_SUBMIT)),
            "salesup": salesup,
            "salon": salon,
            "missing_materials": field_text(f.get(COL_MISSING)),
            "menu_issue": field_text(f.get(COL_MENU)),
            "skinner_checked": field_text(f.get(COL_SK_CHECK)),
            "skinner_trained": field_text(f.get(COL_SK_TRAIN)),
            "items": items,
            "completion": round(done / len(CHECKLIST), 4),
        })

    data = {
        "generated_at": time.strftime("%d/%m/%Y %H:%M", time.gmtime(time.time() + 7 * 3600)),
        "source": "lark",
        "month": SYNC_MONTH,
        "checklist_items": [{"key": k, "label": lbl} for k, _c, lbl in CHECKLIST],
        "visits": visits,
    }
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    print(f"OK: thang {SYNC_MONTH} | {len(visits)} luot di salon, {img_total} anh | bo qua {skipped} ban ghi ngoai thang")
    if skipped_dates:
        uniq = sorted(set(skipped_dates))
        print("  Ngay bi bo qua (mau):", ", ".join(uniq[:15]))


if __name__ == "__main__":
    main()
