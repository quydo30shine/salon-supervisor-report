# -*- coding: utf-8 -*-
"""
Tạo assignments.json từ file phân cụm (salon -> salesup phụ trách + cụm + loại + mục tiêu).

Mục tiêu nghiệm thu / tháng:
  - salon offline: tối thiểu 3 lần
  - salon online : tối thiểu 1 lần (nghiệm thu online)
  - salon chưa có salesup: không có mục tiêu (ghi "không có salesup")

Chạy: python build_assignments.py
Cập nhật hàng tháng: thay file CSV nguồn (assignments_source.csv) rồi chạy lại.
"""
import csv
import json
import os

TARGET_OFFLINE = 3
TARGET_ONLINE = 1
NO_SUP_LABEL = "không có salesup"

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    os.path.join(HERE, "assignments_source.csv"),
    os.path.join(os.path.dirname(HERE), "Chia salon cụm Salesup - phân cụm mới tháng 6.csv"),
]

COL_SALON   = "Tên Salon"
COL_SUP     = "Tên Supervisor"
COL_CLUSTER = "Phân cụm - Care chính target & trách nhiệm "  # lưu ý dấu cách cuối
COL_ONLINE  = "Hỗ trợ Online - Nhận target"                  # "online"/"offline"/""
COL_LOAI    = "Phân loại"


def main():
    src = next((p for p in CANDIDATES if os.path.exists(p)), None)
    if not src:
        raise SystemExit("Khong tim thay file phan cum CSV.")
    rows = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            salon = (r.get(COL_SALON) or "").strip()
            if not salon:
                continue
            sup = (r.get(COL_SUP) or "").strip()
            typ = (r.get(COL_ONLINE) or "").strip().lower()  # offline / online / ""
            if not sup:
                typ = ""  # chưa có salesup -> không phân loại mục tiêu
            target = TARGET_OFFLINE if typ == "offline" else TARGET_ONLINE if typ == "online" else 0
            rows.append({
                "salon": salon,
                "supervisor": sup if sup else NO_SUP_LABEL,
                "has_sup": bool(sup),
                "cluster": (r.get(COL_CLUSTER) or "").strip(),
                "type": typ,              # "offline" | "online" | ""
                "target": target,         # 3 | 1 | 0
                "phanloai": (r.get(COL_LOAI) or "").strip(),
            })
    data = {
        "target_offline": TARGET_OFFLINE,
        "target_online": TARGET_ONLINE,
        "assignments": rows,
    }
    out = os.path.join(HERE, "assignments.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    off = sum(1 for x in rows if x["type"] == "offline")
    on = sum(1 for x in rows if x["type"] == "online")
    nosup = sum(1 for x in rows if not x["has_sup"])
    print(f"OK: {len(rows)} salon -> assignments.json | offline={off} online={on} chua_co_salesup={nosup}")


if __name__ == "__main__":
    main()
