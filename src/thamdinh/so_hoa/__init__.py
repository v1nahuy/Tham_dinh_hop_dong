"""Bước 1: Số hóa Dự thảo thành Văn bản hiệu lực (không dùng LLM)."""

import hashlib
from collections.abc import Callable, Collection
from pathlib import Path

import pypdfium2 as pdfium

from thamdinh.so_hoa.cau_truc import Dong, dung_cau_truc
from thamdinh.so_hoa.lop_text import danh_gia_lop_text, doc_trang
from thamdinh.so_hoa.ocr import BoOCR, ocr_trang
from thamdinh.so_hoa.van_ban import TrangSoHoa, VanBanHieuLuc, hash_noi_dung, luu_pdf, luu_van_ban, nap_van_ban

# Độ tin cậy nhận dạng trung bình của trang OCR dưới ngưỡng này thì trang bị đánh dấu tin cậy thấp (TOSS: 0,91–0,93).
NGUONG_TIN_CAY_OCR = 0.85


class CanOCRError(Exception):
    """Có trang lớp text kém, phải OCR nhưng không có bộ OCR."""


def hash_pdf(duong_dan: str | Path) -> str:
    return hashlib.sha256(Path(duong_dan).read_bytes()).hexdigest()


def so_hoa(
    duong_dan: str | Path,
    thu_muc_luu: str | Path | None = None,
    bo_ocr: BoOCR | None = None,
    ep_ocr: Collection[int] = (),
    tien_trinh: Callable[[str], None] = lambda _: None,
    lam_lai: bool = False,
) -> VanBanHieuLuc:
    """Số hóa PDF thành Văn bản hiệu lực: trang có lớp text tốt đọc lớp text, trang còn lại OCR bằng `bo_ocr`.

    - Có `thu_muc_luu` thì dùng lại bản đã lưu (kể cả bản đã sửa tay). OCR chậm (khoảng 1 phút/trang trên CPU), nên kết
      quả được lưu theo hash PDF và chỉ chạy một lần.
    - `ep_ocr`: số trang bắt buộc đi đường OCR dù lớp text tốt (để kiểm thử); khi đó không dùng, không ghi bản lưu.
    - `lam_lai`: số hóa lại từ đầu, bỏ bản đang dùng (kể cả bản đã sửa tay); các bản theo nội dung cũ vẫn còn.
    """
    duong_dan = Path(duong_dan)
    luu = thu_muc_luu is not None and not ep_ocr
    if luu:
        luu_pdf(duong_dan, hash_pdf(duong_dan), thu_muc_luu)
        if not lam_lai and (da_luu := nap_van_ban(hash_pdf(duong_dan), thu_muc_luu)):
            return da_luu
    pdf = pdfium.PdfDocument(duong_dan)
    trang_so_hoa: list[TrangSoHoa] = []
    dong: list[Dong] = []
    can_ocr: list[str] = []
    for i in range(len(pdf)):
        so = i + 1
        trang = doc_trang(pdf[i], so)
        danh_gia = danh_gia_lop_text("\n".join(d.noi_dung for d in trang.dong))
        if danh_gia.dung_lop_text and so not in ep_ocr:
            thap, ly_do = _danh_gia_trang(trang.so_doan_redline, trang.co_khung_comment)
            trang_so_hoa.append(TrangSoHoa(so, "lop_text", thap, tuple(ly_do)))
            dong.extend(trang.dong)
            continue
        if bo_ocr is None:
            can_ocr.append(f"trang {so}: {danh_gia.ly_do or 'ép OCR'}")
            continue
        tien_trinh(f"OCR trang {so}/{len(pdf)}")
        kq = ocr_trang(pdf[i], so, bo_ocr)
        thap, ly_do = _danh_gia_trang(kq.so_doan_redline, kq.co_khung_comment)
        if kq.do_tin_cay < NGUONG_TIN_CAY_OCR:
            thap = True
            ly_do.append(f"độ tin cậy OCR thấp ({kq.do_tin_cay:.0%})")
        trang_so_hoa.append(TrangSoHoa(so, "ocr", thap, tuple(ly_do)))
        dong.extend(kq.dong)
    pdf.close()
    if can_ocr:
        raise CanOCRError("Lớp text kém, cần OCR nhưng chưa có bộ OCR: " + "; ".join(can_ocr))

    cau_truc = dung_cau_truc(dong)
    van_ban = VanBanHieuLuc(hash_pdf(duong_dan), duong_dan.name, trang_so_hoa, cau_truc.dieu_khoan, cau_truc.canh_bao)
    if luu:
        luu_van_ban(van_ban, thu_muc_luu, ban_goc=True)
    return van_ban


def _danh_gia_trang(so_doan_redline: int, co_khung_comment: bool) -> tuple[bool, list[str]]:
    """(tin cậy thấp, ghi chú). Redline làm trang tin cậy thấp vì nhãn có thể sai; khung comment đã bị bỏ hẳn nên chỉ
    ghi chú, không làm trang tin cậy thấp."""
    ly_do = []
    if so_doan_redline:
        ly_do.append(f"có redline ({so_doan_redline} đoạn đã gắn nhãn)")
    if co_khung_comment:
        ly_do.append("có khung comment (đã bỏ)")
    return bool(so_doan_redline), ly_do
