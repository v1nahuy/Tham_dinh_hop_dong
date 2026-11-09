"""Kiểm tra Trích dẫn: câu LLM trích có thật sự nằm trong Văn bản hiệu lực không (code thuần)."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import NHAN_GIU, NHAN_XOA, DieuKhoan, Vung

KHOP, KHOP_SAI_SO_HIEU, KHONG_XAC_MINH_DUOC = "khop", "khop_sai_so_hieu", "khong_xac_minh_duoc"

NHAN_BAT_KY = re.compile(r"\[(?:xóa|thêm|sửa): ([^\]]*)\]")
NHAN_MO = re.compile(r"\[(?:xóa|thêm|sửa): ")
NGOAC_KEP = re.compile(r"[“”„‟\"'‘’‚‛«»]")
GACH_NGANG = re.compile(r"[‐‑‒–—―−]")
LUOC = re.compile(r"…|\.\.\.")
TIEN_TO_SO_HIEU = re.compile(r"^(#+\s*)?((khoản|điểm)\s+)?", re.IGNORECASE)
CACH_SAT_DAU_CAU = re.compile(r" ?([^\w\s]) ?")


@dataclass(frozen=True)
class TrichDan:
    so_hieu: str
    nguyen_van: str


@dataclass(frozen=True)
class KetQuaTrichDan:
    trang_thai: str  # khop | khop_sai_so_hieu | khong_xac_minh_duoc
    so_hieu_dung: str | None = None


def chuan_hoa(van_ban: str) -> str:
    van_ban = unicodedata.normalize("NFC", van_ban)
    van_ban = NGOAC_KEP.sub('"', van_ban)
    van_ban = GACH_NGANG.sub("-", van_ban)
    return re.sub(r"\s+", " ", van_ban).strip()


def _chuan_hoa_noi_dung(van_ban: str) -> str:
    """Như `chuan_hoa`, thêm bỏ dấu cách sát dấu câu: LLM hay chép "10. Đầu mối" khi Hợp đồng ghi "10.Đầu mối"."""
    return CACH_SAT_DAU_CAU.sub(r"\1", chuan_hoa(van_ban))


def _cac_doan(nguyen_van: str) -> list[str]:
    """Các đoạn cần tìm của câu trích: LLM có thể chép cả nhãn sửa đổi, hoặc gộp nhiều dòng nhãn thành một nhãn không đóng."""
    van_ban = NHAN_BAT_KY.sub(r"\1", unicodedata.normalize("NFC", nguyen_van))
    if NHAN_MO.search(van_ban):
        van_ban = NHAN_MO.sub("", van_ban).replace("]", "")
    doan = [_chuan_hoa_noi_dung(d) for d in LUOC.split(van_ban)]
    return [d for d in doan if d]


def kiem_tra_trich_dan(trich_dan: TrichDan, van_ban: VanBanHieuLuc) -> KetQuaTrichDan:
    doan = _cac_doan(trich_dan.nguyen_van)
    if not doan:
        return KetQuaTrichDan(KHONG_XAC_MINH_DUOC)

    pham_vi = _pham_vi(trich_dan.so_hieu, van_ban.dieu_khoan)
    if pham_vi and _co_trong(doan, pham_vi):
        return KetQuaTrichDan(KHOP)
    for dk in van_ban.dieu_khoan:
        if _co_trong(doan, [dk]):
            return KetQuaTrichDan(KHOP_SAI_SO_HIEU, dk.so_hieu)
    return KetQuaTrichDan(KHONG_XAC_MINH_DUOC)


def _pham_vi(so_hieu: str, dieu_khoan: list[DieuKhoan]) -> list[DieuKhoan]:
    """Các Điều khoản mang số hiệu được trích (có thể trùng số hiệu) cùng mọi Điều khoản con cháu."""
    so_hieu = TIEN_TO_SO_HIEU.sub("", chuan_hoa(so_hieu)).casefold()
    goc = {dk.ma for dk in dieu_khoan if dk.so_hieu.casefold() == so_hieu}
    ket_qua = []
    for dk in dieu_khoan:  # cha luôn đứng trước con
        if dk.ma in goc or dk.cha in goc:
            goc.add(dk.ma)
            ket_qua.append(dk)
    return ket_qua


def _co_trong(doan: list[str], dieu_khoan: list[DieuKhoan]) -> bool:
    noi_dung = "\n".join(dk.noi_dung for dk in dieu_khoan)
    # LLM có thể trích bản còn chữ redline hoặc bản đã chấp nhận thay đổi
    ban_giu_het = _chuan_hoa_noi_dung(NHAN_BAT_KY.sub(r"\1", noi_dung))
    ban_sach = _chuan_hoa_noi_dung(NHAN_GIU.sub(r"\1", NHAN_XOA.sub("", noi_dung)))
    return _theo_thu_tu(doan, ban_giu_het) or _theo_thu_tu(doan, ban_sach)


def _theo_thu_tu(doan: list[str], van_ban: str) -> bool:
    vi_tri = 0
    for d in doan:
        tim = van_ban.find(d, vi_tri)
        if tim < 0:
            return False
        vi_tri = tim + len(d)
    return True


class TrichDanCoTrangThai(Protocol):
    so_hieu: str
    nguyen_van: str
    trang_thai: str
    so_hieu_dung: str | None


def dieu_khoan_chua_trich_dan(trich_dan: TrichDanCoTrangThai, van_ban: VanBanHieuLuc) -> list[DieuKhoan]:
    """Các Điều khoản chứa câu trích (để xem vị trí, ghi vị trí trong báo cáo).

    Trong phạm vi số hiệu (theo số hiệu đúng nếu LLM ghi sai), chọn các Điều khoản chứa trọn câu trích; câu trích trải
    qua nhiều Điều khoản thì lấy cả phạm vi. Trích dẫn không xác minh được: không có.
    """
    if trich_dan.trang_thai == KHONG_XAC_MINH_DUOC:
        return []
    doan = _cac_doan(trich_dan.nguyen_van)
    pham_vi = _pham_vi(trich_dan.so_hieu_dung or trich_dan.so_hieu, van_ban.dieu_khoan)
    return [dk for dk in pham_vi if _co_trong(doan, [dk])] or pham_vi


def vung_trich_dan(trich_dan: TrichDanCoTrangThai, van_ban: VanBanHieuLuc) -> list[Vung]:
    """Vùng trên trang để tô khi xem Trích dẫn: vùng của Điều khoản chứa câu trích (chưa biết tọa độ từng câu)."""
    return [v for dk in dieu_khoan_chua_trich_dan(trich_dan, van_ban) for v in dk.vung]
