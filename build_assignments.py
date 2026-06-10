# -*- coding: utf-8 -*-
"""
Tạo assignments.json từ file phân cụm (salon -> salesup phụ trách + cụm + online/offline).
Đây là dữ liệu MỤC TIÊU (mỗi salon được salesup phụ trách đi tối thiểu N lần).

Chạy: python build_assignments.py
Cập nhật phân cụm hàng tháng: thay file CSV nguồn rồi chạy lại.
"""
import csv
import json
import os

TARGET_VISITS = 3  # mỗi salon: salesup phụ trách đi tối thiểu 3 lần

HERE = os.path.dirname(os.path.abspath(__file__))
# ưu tiên bản copy trong repo; nếu không có thì đọc từ thư mục cha
CANDIDATES = [
    os.path.join(HERE, "assignments_source.csv"),
    os.path.join(os.path.dirname(HERE), "Chia salon cụm Salesup - phân cụm mới tháng 5.csv"),
]

COL_SALON = "Tên Salon"
COL_SUP   = "Tên Supervisor"
COL_CLUSTER = "Phân cụm - Care chính target & trách nhiệm "  # lưu ý dấu cách cuối
COL_ONLINE = "Hỗ trợ Online - Nhận target"


def main():
    src = next((p for p in CANDIDATES if os.path.exists(p)), None)
    if not src:
        raise SystemExit("Khong tim thay file phan cum CSV.")
    rows = []
    with open(src, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            salon = (r.get(COL_SALON) or "").strip()
            sup = (r.get(COL_SUP) or "").strip()
            if not salon:
                continue
            rows.append({
                "salon": salon,
                "supervisor": sup,
                "cluster": (r.get(COL_CLUSTER) or "").strip(),
                "online": (r.get(COL_ONLINE) or "").strip(),  # "online"/"offline"/""
            })
    data = {"target_visits": TARGET_VISITS, "assignments": rows}
    out = os.path.join(HERE, "assignments.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(rows)} salon -> assignments.json (target={TARGET_VISITS})")


if __name__ == "__main__":
    main()
