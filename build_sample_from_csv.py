# -*- coding: utf-8 -*-
"""
Tạo data.json MẪU từ file CSV export (dùng để xem trước báo cáo khi chưa nối Lark).
Khi GitHub Action chạy sync_lark.py, data.json sẽ được ghi đè bằng dữ liệu thật + ảnh thật.

Chạy: python build_sample_from_csv.py
"""
import csv
import json
import os

# Cấu hình checklist: key -> tên cột trong form/CSV
CHECKLIST = [
    ("front",         "Nghiệm thu trưng bày SP: Quầy mặt tiền",      "Trưng bày - Quầy mặt tiền"),
    ("reception",     "Nghiệm thu quầy trưng bày: Quầy lễ tân",      "Trưng bày - Quầy lễ tân"),
    ("stylist",       "Nghiệm thu quầy trưng bày: Khu Stylist",      "Trưng bày - Khu Stylist"),
    ("relax",         "Vật tư Relax/Spa",                            "Vật tư Relax/Spa"),
    ("und",           "Vật tư UND",                                  "Vật tư UND"),
    ("ctkm",          "Nghiệm thu triển khai CTKM",                  "Triển khai CTKM"),
    ("training",      "Nghiệm thu training/đào tạo tại salon",       "Training tại salon"),
    ("price",         "Nghiệm thu ấn phẩm - Bảng giá",               "Ấn phẩm - Bảng giá"),
    ("skinner_equip", "Nghiệm thu vật tư máy móc, quy trình Skinner","Vật tư/máy móc Skinner"),
]

COL_DATE     = "Ngày Training"
COL_SUBMIT   = "Submitted on"
COL_SALESUP  = "Nhân sự Training"
COL_SALON    = "Chọn Salon:"
COL_MISSING  = "Vật tư thiếu"
COL_SK_CHECK = "Số skinner chấm trong ngày"
COL_SK_TRAIN = "Số skinner đào tạo trong ngày"
# cột "ghi chú skinner" không có header rõ ràng - bỏ qua nếu thiếu

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(os.path.dirname(HERE),
    "FORM ĐÁNH GIÁ HIỆN TRẠNG SALON 2026_FORM CHẤM ĐIỂM SALON SUPERVISOR NGÀNH HÀNG UỐN NHUỘM DƯỠNG_Results.csv")


def split_images(cell):
    """Cột ảnh trong CSV là chuỗi các tên file ngăn cách bởi dấu phẩy."""
    if not cell:
        return []
    parts = [p.strip() for p in cell.split(",")]
    # chỉ giữ phần trông như tên file ảnh/video
    out = []
    for p in parts:
        if not p:
            continue
        low = p.lower()
        if low.endswith((".jpeg", ".jpg", ".png", ".mp4", ".heic", ".webp")):
            out.append(p)
    return out


def is_done(cell, imgs):
    if imgs:
        return True
    # field số/checkbox: coi là done nếu có giá trị khác rỗng
    return bool(cell and cell.strip())


def main():
    visits = []
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            salon = (row.get(COL_SALON) or "").strip()
            date = (row.get(COL_DATE) or "").strip()
            salesup = (row.get(COL_SALESUP) or "").strip()
            if not salon and not salesup:
                continue
            items = {}
            done = 0
            for key, col, _label in CHECKLIST:
                cell = row.get(col) or ""
                imgs = split_images(cell)
                d = is_done(cell, imgs)
                if d:
                    done += 1
                items[key] = {
                    "done": d,
                    # ảnh mẫu: chỉ lưu tên file (chưa có ảnh thật cho tới khi sync Lark)
                    "images": [],
                    "count": len(imgs),
                    "raw": cell.strip(),
                }
            visits.append({
                "id": f"r{i+1}",
                "date": date,
                "submitted_on": (row.get(COL_SUBMIT) or "").strip(),
                "salesup": salesup,
                "salon": salon,
                "missing_materials": (row.get(COL_MISSING) or "").strip(),
                "skinner_checked": (row.get(COL_SK_CHECK) or "").strip(),
                "skinner_trained": (row.get(COL_SK_TRAIN) or "").strip(),
                "items": items,
                "completion": round(done / len(CHECKLIST), 4),
            })

    data = {
        "generated_at": "MẪU (chưa nối Lark)",
        "source": "csv-sample",
        "checklist_items": [{"key": k, "label": lbl} for k, _c, lbl in CHECKLIST],
        "visits": visits,
    }
    out = os.path.join(HERE, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK: wrote {out} with {len(visits)} visits.")


if __name__ == "__main__":
    main()
