# -*- coding: utf-8 -*-
"""
Chỉ ĐỌC: liệt kê tên cột thật trong bảng Lark + kiểu dữ liệu mẫu.
Không ghi data.json, không tải ảnh. Dùng để đối chiếu sau khi đổi tên cột nguồn.

Chạy trong GitHub Actions (workflow "Inspect Lark fields") hoặc local nếu có biến môi trường.
"""
import os
import sys
import json
import urllib.request
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DOMAIN = os.environ.get("LARK_DOMAIN", "open.larksuite.com").strip() or "open.larksuite.com"
APP_ID = os.environ.get("LARK_APP_ID", "").strip()
APP_SECRET = os.environ.get("LARK_APP_SECRET", "").strip()
APP_TOKEN = os.environ.get("LARK_APP_TOKEN", "").strip()
TABLE_ID = os.environ.get("LARK_TABLE_ID", "").strip()


def api(method, path, token=None, body=None):
    url = f"https://{DOMAIN}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def get_token():
    res = api("POST", "/open-apis/auth/v3/tenant_access_token/internal",
              body={"app_id": APP_ID, "app_secret": APP_SECRET})
    if res.get("code") != 0:
        raise RuntimeError(f"Lay token that bai: {res}")
    return res["tenant_access_token"]


def describe(val):
    """Mô tả ngắn gọn kiểu + giá trị mẫu của 1 field."""
    if val is None:
        return "None"
    if isinstance(val, bool):
        return f"bool({val})"
    if isinstance(val, (int, float)):
        return f"number({val})"
    if isinstance(val, str):
        s = val[:40].replace("\n", " ")
        return f'text("{s}")'
    if isinstance(val, list):
        if val and isinstance(val[0], dict) and val[0].get("file_token"):
            return f"ATTACHMENT x{len(val)} (ten vd: {val[0].get('name','?')[:30]})"
        if val and isinstance(val[0], dict):
            keys = ",".join(sorted(val[0].keys()))[:40]
            return f"list[dict]{{{keys}}} x{len(val)} -> {str(val[0])[:60]}"
        return f"list x{len(val)} -> {str(val[:2])[:60]}"
    if isinstance(val, dict):
        return f"dict{{{','.join(sorted(val.keys()))[:40]}}} -> {str(val)[:60]}"
    return f"{type(val).__name__}({str(val)[:40]})"


def main():
    missing = [k for k, v in {"LARK_APP_ID": APP_ID, "LARK_APP_SECRET": APP_SECRET,
                              "LARK_APP_TOKEN": APP_TOKEN, "LARK_TABLE_ID": TABLE_ID}.items() if not v]
    if missing:
        print("THIEU bien moi truong: " + ", ".join(missing))
        sys.exit(1)

    token = get_token()

    # 1) Schema chính thức của bảng
    print("=" * 70)
    print("A. SCHEMA CAC COT (tu API fields)")
    print("=" * 70)
    try:
        res = api("GET", f"/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/fields?page_size=200", token=token)
        for f in res.get("data", {}).get("items", []):
            print(f"  [{f.get('type')}] {f.get('field_name')}")
    except Exception as e:
        print("  Khong doc duoc schema:", e)

    # 2) Field thực tế xuất hiện trong bản ghi + giá trị mẫu
    q = urllib.parse.urlencode({"page_size": 20})
    res = api("GET", f"/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records?{q}", token=token)
    items = res.get("data", {}).get("items", [])
    print()
    print("=" * 70)
    print(f"B. FIELD XUAT HIEN TRONG {len(items)} BAN GHI DAU + GIA TRI MAU")
    print("=" * 70)
    names = sorted({k for r in items for k in (r.get("fields") or {})})
    for n in names:
        sample = None
        for r in items:
            v = (r.get("fields") or {}).get(n)
            if v not in (None, "", []):
                sample = v
                break
        print(f"  - {n}")
        print(f"      {describe(sample)}")
    print()
    print(f"Tong: {len(names)} field co du lieu.")


if __name__ == "__main__":
    main()
