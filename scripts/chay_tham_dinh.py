"""Chạy một Lượt thẩm định bằng model local và in bảng tóm tắt.

Chạy: .venv/Scripts/python scripts/chay_tham_dinh.py <hop_dong.pdf> [--che-do toan_van|truy_xuat]
                 [--checklist checklist.yaml] [--tiep-tuc <mã Lượt>] [--chi-muc 14,15]
      .venv/Scripts/python scripts/chay_tham_dinh.py --danh-sach
Cần llama-server đang chạy (docs/chay-model-local.md); trang có lớp text kém được OCR (docs/cai-ocr.md).
Kết quả lưu vào <THAMDINH_DATA_DIR>/tham-dinh.sqlite3 sau mỗi Mục, nên tắt giữa chừng không mất các Mục đã xong.
- --danh-sach: liệt kê các Lượt đã lưu (mã Lượt, tiến độ).
- --tiep-tuc: chạy tiếp Lượt đã lưu, chỉ chạy Mục chưa chạy hoặc "chưa đánh giá được" (vẫn là Lượt đó).
- --chi-muc: cùng --tiep-tuc, chạy lại các Mục này dù đã có kết quả; tạo Lượt mới, Lượt cũ giữ nguyên.
- --che-do truy_xuat: gắn Chủ đề (lần đầu khoảng 40 phút với TOSS trên CPU, sau đó dùng lại), chọn Điều khoản cho từng
  Mục; máy chủ embedding bge-m3 không chạy thì lưới an toàn chỉ dùng BM25. Chạy tiếp thì theo chế độ của Lượt đã lưu.
"""

import argparse
import sys
from collections import Counter
from functools import partial
from pathlib import Path

from thamdinh.chay_luot import chay_luot
from thamdinh.kho_luot import KhoLuot
from thamdinh.settings import load_settings

TEN = {"dat": "Đạt", "luu_y": "Lưu ý", "vi_pham": "Vi phạm"}

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path, nargs="?")
    ap.add_argument("--danh-sach", action="store_true")
    ap.add_argument("--che-do", choices=["toan_van", "truy_xuat"])
    ap.add_argument("--checklist", default="checklists/dau-ra-v1.1.yaml")
    ap.add_argument("--tiep-tuc")
    ap.add_argument("--chi-muc", default="")
    args = ap.parse_args()
    settings = load_settings()
    kho = KhoLuot(settings.data_dir)
    if args.danh_sach:
        for t in kho.danh_sach():
            goc = f" (tạo từ {t.luot_goc})" if t.luot_goc else ""
            print(f"{t.ma}  {t.ten_file}  {t.che_do}  {t.model}  {t.so_muc_xong}/{t.so_muc} Mục, "
                  f"đã duyệt {t.so_muc_da_duyet}{goc}")
        sys.exit(0)
    if args.pdf is None:
        ap.error("cần đường dẫn PDF Hợp đồng")
    if args.chi_muc and not args.tiep_tuc:
        ap.error("--chi-muc cần đi cùng --tiep-tuc")
    kq = chay_luot(
        args.pdf, checklist=args.checklist, settings=settings, che_do=args.che_do, tiep_tuc=args.tiep_tuc,
        chi_muc={int(x) for x in args.chi_muc.split(",") if x.strip()}, in_ra=partial(print, flush=True),
    )

    print(f"\nChế độ: {kq.che_do}")
    if kq.cac_ben:
        print(f"Công ty: {kq.cac_ben.cong_ty} ({kq.cac_ben.ten_cong_ty}); Khách hàng: {kq.cac_ben.ten_khach_hang}")
    else:
        print(kq.loi_cac_ben)
    for m in kq.muc:
        if m.ket_qua is None:
            print(f"Mục {m.so:>2}: CHƯA ĐÁNH GIÁ ĐƯỢC - {m.loi}")
            continue
        trich_dan = Counter(td.trang_thai for t in m.tieu_chi for td in t.trich_dan)
        print(f"Mục {m.so:>2}: {TEN[m.ket_qua.ket_qua]:<8} {m.ket_qua.giai_thich}  trích dẫn: {dict(trich_dan)}")
        if kq.che_do == "truy_xuat":
            print(f"         đọc {len(m.dieu_khoan_dua_vao)} Điều khoản" + "".join(f"; {c}" for c in m.canh_bao))
    goc = f", tạo từ Lượt {kq.luot_goc}" if kq.luot_goc else ""
    print(f"\nĐã lưu Lượt {kq.ma}{goc} vào {kho.duong_dan}")
