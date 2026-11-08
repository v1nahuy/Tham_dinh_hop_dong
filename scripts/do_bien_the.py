"""Đo Bước 1 (Số hóa qua OCR) trên các biến thể scan giả lập của TOSS (issue 14) và ghi báo cáo.

Chạy: .venv/Scripts/python scripts/do_bien_the.py [--bien-the scan-200-nghieng-3,den-trang-200] [--ca-file]
                 [--scan-that scan.pdf --trang-goc 3,8]
- Tạo PDF biến thể (chỉ có ảnh, seed cố định) vào eval/bien-the/ nếu chưa có.
- OCR các trang đo (mặc định 12 trang đại diện, khoảng 8 phút mỗi biến thể; --ca-file: cả 52 trang, khoảng 35 phút).
  Kết quả OCR lưu trong eval/bien-the/ket-qua/, đo lại không phải OCR lại.
- So từng trang với lớp text của PDF gốc (tỉ lệ lỗi ký tự, tỉ lệ từ có mặt) và so cấu trúc với Văn bản hiệu lực đang
  dùng trong <THAMDINH_DATA_DIR> (bản đã sửa tay nếu có): số Điều khoản nhận diện đúng, tỉ lệ lỗi ký tự theo Điều khoản.
- --scan-that: đo thêm một bản scan thật; --trang-goc là số trang gốc tương ứng với từng trang của bản scan.
Ghi eval/bien-the/bao-cao.md.
"""

import argparse
import json
import sys
import time
import warnings
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pypdfium2 as pdfium

from thamdinh.bien_the import CAU_HINH, tao_pdf_bien_the
from thamdinh.do_chat_luong import cer, chuan, so_ky_tu_sai, so_sanh_cau_truc, ty_le_tu
from thamdinh.settings import load_settings
from thamdinh.so_hoa import hash_noi_dung, hash_pdf, so_hoa
from thamdinh.so_hoa.cau_truc import Dong, dung_cau_truc
from thamdinh.so_hoa.lop_text import doc_trang
from thamdinh.so_hoa.ocr import BoOCRMacDinh, ocr_trang
from thamdinh.so_hoa.van_ban import nap_van_ban, nap_van_ban_goc

THU_MUC = Path("eval/bien-the")
TRANG_DAI_DIEN = [1, 2, 3, 4, 5, 8, 12, 14, 22, 41, 47, 51]
COMMENT = ("Commented", "Formatted:")


def ocr_co_luu(pdf: Path, ma: str, trang: list[tuple[int, int]], bo: BoOCRMacDinh) -> dict[int, dict]:
    """OCR các trang (số trang trong file, số trang gốc), lưu theo số trang gốc; trang đã OCR thì dùng lại."""
    file = THU_MUC / "ket-qua" / f"{ma}.json"
    da_co = {int(k): v for k, v in json.loads(file.read_text(encoding="utf-8")).items()} if file.is_file() else {}
    tai_lieu = pdfium.PdfDocument(pdf)
    for so_file, so_goc in trang:
        if so_goc in da_co:
            continue
        bat_dau = time.monotonic()
        kq = ocr_trang(tai_lieu[so_file - 1], so_goc, bo)
        da_co[so_goc] = {"dong": [asdict(d) for d in kq.dong], "goc": kq.goc_nghieng, "tin_cay": kq.do_tin_cay,
                         "co_khung": kq.co_khung_comment, "giay": round(time.monotonic() - bat_dau, 1)}
        print(f"  {ma}: trang {so_goc} xong ({da_co[so_goc]['giay']:.0f} giây)", flush=True)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(da_co, ensure_ascii=False), encoding="utf-8")
    tai_lieu.close()
    return da_co


def do_mot_bien_the(ten: str, mo_ta: str, ket_qua: dict[int, dict], trang: list[int], lop_text: dict, tham_chieu):
    dong = [Dong(**{**d, "toa_do": tuple(d["toa_do"]) if d["toa_do"] else None})
            for so in trang for d in ket_qua[so]["dong"]]
    sai = tong = 0
    tung_trang = {}
    for so in trang:
        ocr = _van_ban(ket_qua[so])
        a = chuan(lop_text[so])
        sai += so_ky_tu_sai(a, chuan(ocr))
        tong += len(a)
        tung_trang[so] = cer(lop_text[so], ocr)
    toan_van = "\n".join(d.noi_dung for d in dong)
    cau_truc = so_sanh_cau_truc(tham_chieu, dung_cau_truc(dong).dieu_khoan, trang)
    return {
        "ten": ten, "mo_ta": mo_ta,
        "cer": sai / max(tong, 1),
        "tu": ty_le_tu("\n".join(lop_text[s] for s in trang), toan_van),
        "dieu_khoan": f"{cau_truc.dung}/{cau_truc.tong}",
        "cer_dieu_khoan": cau_truc.cer,
        "thieu": cau_truc.thieu,
        "goc": [ket_qua[s]["goc"] for s in trang],
        "lan_comment": [s for s in trang if any(c in _van_ban(ket_qua[s]) for c in COMMENT)],
        "xoa": toan_van.count("[xóa:"),
        "giay": sum(ket_qua[s].get("giay", 0) for s in trang),
        "tung_trang": tung_trang,
    }


def _van_ban(trang_ocr: dict) -> str:
    return "\n".join(d["noi_dung"] for d in trang_ocr["dong"])


def ghi_bao_cao(dong: list[dict], trang: list[int], moc: dict, ghi_chu_tham_chieu: str) -> Path:
    phan = [
        "# Đo Bước 1 trên biến thể scan giả lập của TOSS (issue 14)",
        "",
        f"Ngày đo {datetime.now():%d/%m/%Y %H:%M}. Model OCR {load_settings().ocr_model}. Trang đo: "
        f"{', '.join(map(str, trang))}. {ghi_chu_tham_chieu}",
        "",
        "- **Lỗi ký tự (trang):** so với lớp text của PDF gốc, bỏ nhãn redline, ngoặc kép và khoảng trắng.",
        "- **Từ có mặt:** tỉ lệ từ của lớp text có trong kết quả OCR, không xét thứ tự (trang bảng đọc ô khác thứ tự).",
        "- **Điều khoản đúng / lỗi ký tự (Điều khoản):** so với Văn bản hiệu lực, chỉ các Điều khoản nằm trọn trong "
        "các trang đo; Điều khoản không nhận diện được tính sai hết.",
        f"- **Đoạn [xóa:]:** lớp text gốc có {moc['xoa']} đoạn trên các trang đo.",
        "- **Dòng mốc (lớp text gốc)** cho biết giới hạn của chính phép đo: khi đo các trang rời, Điều khoản ở trang không"
        " liền với trang chứa Điều cha (ví dụ khoản 9.2 ở trang 22) không ghép được vào cây, nên mốc chưa đạt 100%. So "
        "các biến thể với dòng mốc; đo cả file (`--ca-file`) thì không còn hiện tượng này.",
        "",
        "| Biến thể | Mô tả | Lỗi ký tự (trang) | Từ có mặt | Điều khoản đúng | Lỗi ký tự (Điều khoản) | Góc đo được "
        "| Lẫn comment (trang) | Đoạn [xóa:] | Thời gian OCR |",
        "|---|---|---|---|---|---|---|---|---|---|",
        f"| lớp text gốc | mốc | 0% | 100% | {moc['dieu_khoan']} | {moc['cer_dieu_khoan']:.1%} | – | – "
        f"| {moc['xoa']} | – |",
    ]
    for d in dong:
        goc = ", ".join(f"{g:g}°" for g in sorted(set(round(g, 1) for g in d["goc"])))
        lan_comment = ", ".join(map(str, d["lan_comment"])) or "không"
        phan.append(
            f"| {d['ten']} | {d['mo_ta']} | {d['cer']:.1%} | {d['tu']:.1%} | {d['dieu_khoan']} "
            f"| {d['cer_dieu_khoan']:.1%} | {goc} | {lan_comment} | {d['xoa']} | {d['giay'] / 60:.0f} phút |"
        )
    phan += ["", "## Lỗi ký tự từng trang", "", "| Trang | " + " | ".join(d["ten"] for d in dong) + " |",
             "|---|" + "---|" * len(dong)]
    for so in trang:
        phan.append(f"| {so} | " + " | ".join(f"{d['tung_trang'][so]:.1%}" if so in d["tung_trang"] else "–"
                                              for d in dong) + " |")
    phan += ["", "## Điều khoản không nhận diện được", ""]
    for d in [moc, *dong]:
        phan.append(f"- **{d['ten']}:** {', '.join(d['thieu']) or 'không có'}")
    ra = THU_MUC / "bao-cao.md"
    ra.write_text("\n".join(phan) + "\n", encoding="utf-8")
    return ra


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", type=Path, default=next(Path("Sample").glob("*TOSS*.pdf")))
    ap.add_argument("--bien-the", default=",".join(CAU_HINH))
    ap.add_argument("--ca-file", action="store_true")
    ap.add_argument("--trang", default="", help="chỉ đo các trang này (chạy thử), ví dụ 2,3")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--scan-that", type=Path)
    ap.add_argument("--trang-goc", default="")
    args = ap.parse_args()
    settings = load_settings()
    bo = BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model)

    goc = pdfium.PdfDocument(args.pdf)
    trang = list(range(1, len(goc) + 1)) if args.ca_file else TRANG_DAI_DIEN
    if args.trang:
        trang = [int(x) for x in args.trang.split(",") if x.strip()]
    lop_text = {so: "\n".join(d.noi_dung for d in doc_trang(goc[so - 1], so).dong) for so in range(1, len(goc) + 1)}
    tham_chieu = nap_van_ban(hash_pdf(args.pdf), settings.data_dir)
    if tham_chieu is None:
        tham_chieu = so_hoa(args.pdf)
        ghi_chu = "Bản đúng về cấu trúc: Văn bản hiệu lực số hóa từ lớp text (chưa có bản lưu)."
    else:
        da_sua = tham_chieu != nap_van_ban_goc(hash_pdf(args.pdf), settings.data_dir)
        ghi_chu = (f"Bản đúng về cấu trúc: Văn bản hiệu lực đang dùng ({'đã sửa tay' if da_sua else 'chưa sửa tay'}, "
                   f"mã nội dung {hash_noi_dung(tham_chieu)[:12]}).")
    dong_goc = [d for so in trang for d in doc_trang(goc[so - 1], so).dong]
    cau_truc_goc = so_sanh_cau_truc(tham_chieu, dung_cau_truc(dong_goc).dieu_khoan, trang)
    moc = {"ten": "lớp text gốc", "dieu_khoan": f"{cau_truc_goc.dung}/{cau_truc_goc.tong}",
           "cer_dieu_khoan": cau_truc_goc.cer, "thieu": cau_truc_goc.thieu,
           "xoa": "\n".join(lop_text[s] for s in trang).count("[xóa:")}

    ket_qua = []
    for ma in [m.strip() for m in args.bien_the.split(",") if m.strip()]:
        ch = CAU_HINH[ma]
        pdf = THU_MUC / f"{ma}.pdf"
        if not pdf.is_file():
            print(f"Tạo {pdf}", flush=True)
            tao_pdf_bien_the(args.pdf, ch, pdf, seed=args.seed)
        print(f"OCR {ma} ({len(trang)} trang)", flush=True)
        kq = ocr_co_luu(pdf, ma, [(so, so) for so in trang], bo)
        ket_qua.append(do_mot_bien_the(ma, ch.mo_ta, kq, trang, lop_text, tham_chieu))
    if args.scan_that:
        trang_goc = [int(x) for x in args.trang_goc.split(",") if x.strip()]
        print(f"OCR bản scan thật {args.scan_that} ({len(trang_goc)} trang)", flush=True)
        kq = ocr_co_luu(args.scan_that, f"scan-that-{hash_pdf(args.scan_that)[:8]}", list(enumerate(trang_goc, 1)), bo)
        ket_qua.append(do_mot_bien_the("scan thật", args.scan_that.name, kq, trang_goc, lop_text, tham_chieu))
        trang = sorted(set(trang) | set(trang_goc))

    print(f"Đã ghi {ghi_bao_cao(ket_qua, trang, moc, ghi_chu)}")
