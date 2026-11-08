"""Đo chất lượng Bước 1 (Số hóa) so với bản đúng: dùng cho `scripts/do_cer_ocr.py` và `scripts/do_bien_the.py`."""

import difflib
import re
import unicodedata
from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass

from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan

NHAN = re.compile(r"\[(xóa|thêm|sửa): ")
# VietOCR không có ký tự ngoặc kép cong, đọc thành "?" hoặc bỏ mất: không tính vào lỗi.
NGOAC_KEP = re.compile(r"[“”\"'‘’?]")


def chuan(s: str) -> str:
    """Chỉ giữ chữ để so: bỏ nhãn redline, ngoặc kép, khoảng trắng."""
    s = NHAN.sub("", unicodedata.normalize("NFC", s)).replace("]", "")
    return re.sub(r"\s+", "", NGOAC_KEP.sub("", s))


def so_ky_tu_sai(dung: str, doc_duoc: str) -> int:
    khop = difflib.SequenceMatcher(None, dung, doc_duoc, autojunk=False).get_matching_blocks()
    return len(dung) - sum(m.size for m in khop)


def cer(dung: str, doc_duoc: str) -> float:
    """Tỉ lệ ký tự của bản đúng không khớp được theo thứ tự (sau `chuan`)."""
    a = chuan(dung)
    return so_ky_tu_sai(a, chuan(doc_duoc)) / max(len(a), 1)


def tu(s: str) -> Counter:
    s = unicodedata.normalize("NFC", NHAN.sub(" ", s).replace("]", " ")).lower()
    return Counter(re.findall(r"\w+", s))


def ty_le_tu(dung: str, doc_duoc: str) -> float:
    """Tỉ lệ từ của bản đúng có trong bản đọc được, không xét thứ tự (trang bảng: thứ tự đọc ô có thể khác)."""
    a = tu(dung)
    return sum((a & tu(doc_duoc)).values()) / max(sum(a.values()), 1)


@dataclass(frozen=True)
class SoSanhCauTruc:
    dung: int  # Điều khoản của bản đúng được nhận diện (cùng số hiệu)
    tong: int
    cer: float  # theo ký tự, trên các Điều khoản của bản đúng; Điều khoản không nhận diện được tính sai hết
    thieu: list[str]
    thua: list[str]


def so_sanh_cau_truc(tham_chieu: VanBanHieuLuc, dieu_khoan: list[DieuKhoan], trang: Collection[int]) -> SoSanhCauTruc:
    """So các Điều khoản đọc được với bản đúng, chỉ xét Điều khoản của bản đúng nằm trọn trong các trang đã đo."""
    trang = set(trang)
    can_co = [d for d in tham_chieu.dieu_khoan if d.trang_bat_dau in trang and d.trang_ket_thuc in trang]
    doc_duoc: dict[str, list[DieuKhoan]] = {}
    for d in dieu_khoan:
        doc_duoc.setdefault(d.so_hieu, []).append(d)
    sai = tong_ky_tu = dung = 0
    thieu = []
    for d in can_co:
        a = chuan(d.noi_dung)
        tong_ky_tu += len(a)
        if doc_duoc.get(d.so_hieu):
            dung += 1
            sai += so_ky_tu_sai(a, chuan(doc_duoc[d.so_hieu].pop(0).noi_dung))
        else:
            thieu.append(d.so_hieu)
            sai += len(a)
    so_hieu_dung = {d.so_hieu for d in tham_chieu.dieu_khoan}
    thua = sorted({d.so_hieu for d in dieu_khoan if d.so_hieu not in so_hieu_dung})
    return SoSanhCauTruc(dung, len(can_co), sai / max(tong_ky_tu, 1), thieu, thua)
