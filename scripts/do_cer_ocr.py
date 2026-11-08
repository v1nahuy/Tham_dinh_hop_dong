"""Đo chất lượng OCR trên một PDF có lớp text tốt: OCR từng trang rồi so với lớp text.

Chạy: .venv/Scripts/python scripts/do_cer_ocr.py "Sample/HĐ TOSS v 12.5.2026.pdf" [--trang 2,3,8]
In từng trang: CER (bỏ nhãn redline, ngoặc kép, khoảng trắng), tỉ lệ từ của lớp text có trong OCR (không xét thứ tự:
trang bảng có CER cao chủ yếu vì thứ tự đọc ô khác lớp text), tỉ lệ số hiệu khoản đọc đúng, số đoạn redline (OCR / lớp
text), độ tin cậy, thời gian; cuối cùng in CER trung bình theo số ký tự. Với TOSS 52 trang, khoảng 45 phút trên CPU.
Đo cả file thì dựng thêm cấu trúc Điều khoản từ kết quả OCR và so số hiệu với bản lớp text.
"""

import argparse
import re
import sys
import time
import warnings
from pathlib import Path

import pypdfium2 as pdfium

from thamdinh.do_chat_luong import chuan, so_ky_tu_sai, ty_le_tu
from thamdinh.settings import load_settings
from thamdinh.so_hoa import so_hoa
from thamdinh.so_hoa.cau_truc import dung_cau_truc
from thamdinh.so_hoa.lop_text import danh_gia_lop_text, doc_trang
from thamdinh.so_hoa.ocr import BoOCRMacDinh, ocr_trang

SO_HIEU = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d{1,2})+)\.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--trang", default="", help="ví dụ 2,3,8; bỏ trống là mọi trang")
    args = ap.parse_args()
    settings = load_settings()
    bo = BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model)
    pdf = pdfium.PdfDocument(args.pdf)
    chon = [int(x) for x in args.trang.split(",") if x.strip()] or range(1, len(pdf) + 1)

    print(f"Model {settings.ocr_model}")
    print(f"{'trang':>5} {'CER':>6} {'từ':>5} {'số hiệu':>8} {'redline':>8} {'tin cậy':>8} {'giây':>5}")
    tong_sai = tong_ky_tu = 0
    dong_ocr = []
    for so in chon:
        trang = pdf[so - 1]
        lop_text = doc_trang(trang, so)
        goc = "\n".join(d.noi_dung for d in lop_text.dong)
        if not danh_gia_lop_text(goc).dung_lop_text:
            print(f"{so:>5} lớp text kém, không có bản đúng để so")
            continue
        bat_dau = time.monotonic()
        kq = ocr_trang(trang, so, bo)
        dong_ocr.extend(kq.dong)
        ocr = "\n".join(d.noi_dung for d in kq.dong)
        sai = so_ky_tu_sai(chuan(goc), chuan(ocr))
        tong_sai += sai
        tong_ky_tu += len(chuan(goc))
        so_hieu = set(SO_HIEU.findall(goc))
        dung = f"{len(so_hieu & set(SO_HIEU.findall(ocr)))}/{len(so_hieu)}" if so_hieu else "-"
        print(
            f"{so:>5} {sai / max(len(chuan(goc)), 1):>6.1%} {ty_le_tu(goc, ocr):>5.0%} {dung:>8} "
            f"{kq.so_doan_redline:>3} /{lop_text.so_doan_redline:>3} {kq.do_tin_cay:>8.3f} "
            f"{time.monotonic() - bat_dau:>5.0f}",
            flush=True,
        )
    print(f"CER trung bình: {tong_sai / max(tong_ky_tu, 1):.2%}")
    if args.trang:
        sys.exit(0)

    # Cấu trúc dựng từ OCR so với lớp text
    so_hieu_ocr = [dk.so_hieu for dk in dung_cau_truc(dong_ocr).dieu_khoan]
    so_hieu_goc = [dk.so_hieu for dk in so_hoa(args.pdf).dieu_khoan]
    dieu = [s for s in so_hieu_ocr if re.fullmatch(r"(Điều|Phụ lục) \S+", s)]
    print(f"Điều và Phụ lục đọc được: {', '.join(dieu)}")
    print(f"Số hiệu: OCR {len(so_hieu_ocr)}, lớp text {len(so_hieu_goc)}")
    print(f"Thiếu so với lớp text: {sorted(set(so_hieu_goc) - set(so_hieu_ocr))}")
    print(f"Thừa so với lớp text: {sorted(set(so_hieu_ocr) - set(so_hieu_goc))}")
    toan_van = "\n".join(d.noi_dung for d in dong_ocr)
    print(f"Lẫn chữ khung comment: {'Commented' in toan_van or 'Formatted:' in toan_van}")
