"""Kiểm tra file Bộ chuẩn đã điền đủ và đúng chưa.

Chạy: .venv/Scripts/python scripts/kiem_tra_bo_chuan.py <bo_chuan.yaml> [checklist.yaml] [hop_dong.pdf]
Mặc định checklist là checklists/dau-ra-v1.1.yaml; có đường dẫn PDF thì kiểm tra thêm hash.
"""

import sys
from pathlib import Path

from thamdinh.bo_chuan import BoChuanError, nap_bo_chuan
from thamdinh.checklist import load_checklist

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    file = Path(sys.argv[1])
    checklist = load_checklist(sys.argv[2] if len(sys.argv) > 2 else "checklists/dau-ra-v1.1.yaml")
    pdf = sys.argv[3] if len(sys.argv) > 3 else None
    tong = sum(len(ds) for m in checklist.muc for ds in m.tieu_chi.values())
    try:
        bo = nap_bo_chuan(file, checklist, pdf=pdf)
    except BoChuanError as e:
        if any("cú pháp YAML" in l for l in e.loi):  # chưa đọc được file thì chưa đếm được tiến độ
            print("Chưa đọc được file:\n" + "\n".join(f"  - {l}" for l in e.loi))
            sys.exit(1)
        chua_dien = sum("chưa điền danh_gia" in l for l in e.loi)
        print(f"Đã điền danh_gia: {tong - chua_dien}/{tong} tiêu chí.")
        khac = [l for l in e.loi if "chưa điền danh_gia" not in l]
        if khac:
            print(f"\n{len(khac)} lỗi cần sửa:")
            print("\n".join(f"  - {l}" for l in khac))
        if chua_dien:
            print(f"\nCòn {chua_dien} tiêu chí chưa điền, ví dụ:")
            print("\n".join([f"  - {l}" for l in e.loi if "chưa điền danh_gia" in l][:5]))
        sys.exit(1)
    thieu_trich_dan = [ma for ma, dg in bo.danh_gia.items() if dg.danh_gia != "khong_ro" and not dg.trich_dan]
    print(f"Hoàn thành: {len(bo.danh_gia)}/{tong} tiêu chí đã có danh_gia.")
    if thieu_trich_dan:
        print(f"Lưu ý: {len(thieu_trich_dan)} tiêu chí chưa có trích dẫn: {', '.join(thieu_trich_dan)}")
