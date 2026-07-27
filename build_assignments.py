# -*- coding: utf-8 -*-
"""
Tạo assignments.json (phân cụm + mục tiêu đi salon) cho TỪNG THÁNG.

Mục tiêu đi salon / tháng — mỗi tháng có quy tắc riêng:
  Tháng 2026-06 (rule "classify"):
    - online: 1 lần; offline Phương Anh: 3; offline khác: theo Phân loại (Phát triển 3, Bền vững 2, Định hình 1)
  Tháng 2026-07 (rule "simple"):
    - offline: 3 lần; online: 1 lần; riêng "36 N1 BD": 1 lần (override)
  Salon chưa có salesup: không có mục tiêu (0).

Cập nhật hàng tháng: thêm file CSV nguồn + 1 dòng vào MONTHS rồi chạy: python build_assignments.py
"""
import csv
import json
import os

NO_SUP_LABEL = "không có salesup"

COL_SALON   = "Tên Salon"
COL_SUP     = "Tên Supervisor"
COL_CLUSTER = "Phân cụm - Care chính target & trách nhiệm "  # lưu ý dấu cách cuối
COL_ONLINE  = "Hỗ trợ Online - Nhận target"                  # "online"/"offline"/""
COL_LOAI    = "Phân loại"

# --- Quy tắc mục tiêu ---
TARGET_BY_LOAI = {"Phát triển": 3, "Bền vững": 2, "Định hình": 1}
KEEP_OLD_SUP = "Nguyễn Thị Phương Anh"


def target_classify(sup, typ, loai, salon):   # tháng 6
    if not sup:
        return 0
    if typ == "online":
        return 1
    if typ == "offline":
        return 3 if sup == KEEP_OLD_SUP else TARGET_BY_LOAI.get(loai, 3)
    return 0


def target_simple(sup, typ, loai, salon):     # tháng 7
    if not sup:
        return 0
    if typ == "online":
        return 1
    if typ == "offline":
        return 3
    return 0


HERE = os.path.dirname(os.path.abspath(__file__))

# Cấu hình từng tháng: file CSV nguồn + hàm tính mục tiêu + override theo tên salon.
MONTHS = [
    {"ym": "2026-06", "csv": "assignments_source.csv",         "target": target_classify, "overrides": {}},
    {"ym": "2026-07", "csv": "assignments_source_2026-07.csv", "target": target_simple,   "overrides": {"36 N1 BD": 1}},
]


def build_month(csv_path, target_fn, overrides):
    rows = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            salon = (r.get(COL_SALON) or "").strip()
            if not salon:
                continue
            sup = (r.get(COL_SUP) or "").strip()
            typ = (r.get(COL_ONLINE) or "").strip().lower()   # offline / online / ""
            loai = (r.get(COL_LOAI) or "").strip()
            if not sup:
                typ = ""   # chưa có salesup -> không phân loại mục tiêu
            if salon in overrides:
                target = overrides[salon]
            else:
                target = target_fn(sup, typ, loai, salon)
            rows.append({
                "salon": salon,
                "supervisor": sup if sup else NO_SUP_LABEL,
                "has_sup": bool(sup),
                "cluster": (r.get(COL_CLUSTER) or "").strip(),
                "type": typ,
                "target": target,
                "phanloai": loai,
            })
    return {"target_offline": 3, "target_online": 1, "assignments": rows}


def main():
    months = {}
    for m in MONTHS:
        path = os.path.join(HERE, m["csv"])
        if not os.path.exists(path):
            print(f"BO QUA {m['ym']}: khong thay {m['csv']}")
            continue
        blk = build_month(path, m["target"], m["overrides"])
        months[m["ym"]] = blk
        rows = blk["assignments"]
        off = sum(1 for x in rows if x["type"] == "offline")
        on = sum(1 for x in rows if x["type"] == "online")
        nosup = sum(1 for x in rows if not x["has_sup"])
        tgt = sum(x["target"] for x in rows)
        print(f"  {m['ym']}: {len(rows)} salon | offline={off} online={on} chua_sup={nosup} | tong muc tieu={tgt}")

    data = {"months": months, "month_list": [m["ym"] for m in MONTHS if m["ym"] in months]}
    out = os.path.join(HERE, "assignments.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK -> assignments.json ({len(months)} thang)")


if __name__ == "__main__":
    main()
