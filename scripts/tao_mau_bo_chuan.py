"""Sinh file mẫu Bộ chuẩn (issue 13) từ một Phiên bản checklist để người dùng điền tay.

Chạy: .venv/Scripts/python scripts/tao_mau_bo_chuan.py <checklist.yaml> <hop_dong.pdf> <file_ra.yaml>
Không ghi đè file đã có, để không mất phần đã điền.
"""

import sys
from pathlib import Path

from thamdinh.bo_chuan import tao_mau_bo_chuan

if __name__ == "__main__":
    checklist, pdf, ra = map(Path, sys.argv[1:4])
    if ra.exists():
        sys.exit(f"{ra} đã tồn tại, không ghi đè.")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(tao_mau_bo_chuan(checklist, pdf), encoding="utf-8")
    print(f"Đã tạo {ra}")
