"""So sánh chế độ toàn văn, chế độ truy xuất và Bộ chuẩn; tạo báo cáo và danh sách gửi pháp chế (issue 15).

Chạy: .venv/Scripts/python scripts/so_sanh_ba_nguon.py <hop_dong.pdf> [--bo-chuan eval/chuan/toss.yaml]
                 [--chay] [--toan-van <mã Lượt>] [--truy-xuat <mã Lượt>] [--checklist checklist.yaml] [--ra eval/so-sanh]
- Mặc định không gọi model: lấy Lượt đủ Mục mới nhất của mỗi chế độ trong kho.
- --chay: chế độ nào chưa có Lượt đủ Mục thì chạy (hoặc chạy tiếp Lượt dang dở) trước, cần llama-server.
- Bộ chuẩn chưa điền xong: so trên các Tiêu chí đã điền; file sai thì báo lỗi và chỉ so hai chế độ.
- Danh sách gửi pháp chế chỉ được tạo khi Bộ chuẩn đã điền đủ.
"""

import argparse
import sys
from functools import partial
from pathlib import Path

from thamdinh.bo_chuan import BoChuanError, doc_trich_dan_chuan, nap_bo_chuan
from thamdinh.chay_luot import chay_luot
from thamdinh.checklist import load_checklist
from thamdinh.kho_luot import KhoLuot, TomTatLuot
from thamdinh.phap_che import ChuaDuBoChuanError, tao_danh_sach_phap_che
from thamdinh.settings import load_settings
from thamdinh.so_hoa import hash_pdf, so_hoa
from thamdinh.so_hoa.ocr import BoOCRMacDinh
from thamdinh.so_sanh import bao_cao_so_sanh, do_phu_tu_luot, so_sanh_nguon

CHE_DO = ("toan_van", "truy_xuat")


def cac_luot(kho: KhoLuot, hash_hop_dong: str, che_do: str) -> list[TomTatLuot]:
    return [t for t in kho.danh_sach() if t.hash_pdf == hash_hop_dong and t.che_do == che_do]


def luot_du(kho: KhoLuot, hash_hop_dong: str, che_do: str, so_muc: int) -> str | None:
    return next((t.ma for t in cac_luot(kho, hash_hop_dong, che_do) if t.so_muc_xong == so_muc), None)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--bo-chuan", type=Path, default=Path("eval/chuan/toss.yaml"))
    ap.add_argument("--checklist", default="checklists/dau-ra-v1.1.yaml")
    ap.add_argument("--toan-van")
    ap.add_argument("--truy-xuat")
    ap.add_argument("--chay", action="store_true")
    ap.add_argument("--ra", type=Path, default=Path("eval/so-sanh"))
    args = ap.parse_args()
    settings = load_settings()
    kho = KhoLuot(settings.data_dir)
    checklist = load_checklist(args.checklist)
    so_muc = len(checklist.muc)
    hash_hop_dong = hash_pdf(args.pdf)

    ma = {"toan_van": args.toan_van, "truy_xuat": args.truy_xuat}
    for che_do in CHE_DO:
        ma[che_do] = ma[che_do] or luot_du(kho, hash_hop_dong, che_do, so_muc)
        if ma[che_do] is None and args.chay:
            dang_do = next(iter(cac_luot(kho, hash_hop_dong, che_do)), None)
            ma[che_do] = chay_luot(args.pdf, args.checklist, settings, che_do=che_do,
                                   tiep_tuc=dang_do.ma if dang_do else None, in_ra=partial(print, flush=True)).ma
        if ma[che_do] is None:
            sys.exit(f"Chưa có Lượt {che_do} đủ {so_muc} Mục; chạy với --chay hoặc chỉ rõ mã Lượt.")

    van_ban = so_hoa(args.pdf, thu_muc_luu=settings.data_dir,
                     bo_ocr=BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model))
    toan_van, truy_xuat = kho.nap(ma["toan_van"]), kho.nap(ma["truy_xuat"])

    bo_chuan, do_phu, canh_bao = None, [], []
    try:
        bo_chuan = nap_bo_chuan(args.bo_chuan, checklist, pdf=args.pdf, mot_phan=True)
        do_phu = do_phu_tu_luot(doc_trich_dan_chuan(args.bo_chuan), checklist, van_ban, truy_xuat)
    except (BoChuanError, FileNotFoundError) as e:
        canh_bao.append(f"Chưa dùng được Bộ chuẩn: {e}")
        print(canh_bao[-1])

    kq = so_sanh_nguon(checklist, toan_van, truy_xuat, bo_chuan)
    args.ra.mkdir(parents=True, exist_ok=True)
    (args.ra / "bao-cao.md").write_text(bao_cao_so_sanh(kq, toan_van, truy_xuat, do_phu, canh_bao), encoding="utf-8")
    print(f"Báo cáo: {args.ra / 'bao-cao.md'}")
    print(f"Toàn văn – truy xuất: {kq.toan_van_truy_xuat.khop}/{kq.toan_van_truy_xuat.tong} Tiêu chí khớp")
    try:
        file = args.ra / "danh-sach-phap-che.docx"
        file.write_bytes(tao_danh_sach_phap_che(kq, checklist, van_ban))
        print(f"Danh sách gửi pháp chế: {file} ({len(kq.bat_dong)} Tiêu chí)")
    except ChuaDuBoChuanError as e:
        print(f"Chưa tạo danh sách gửi pháp chế: {e}")
