"""Lượt thẩm định và định dạng lưu của nó (issue 27).

Mọi chuyển đổi Lượt ↔ dict (JSON trong `kho_luot`) nằm ở đây, kể cả cách xử lý khi định dạng đổi: Lượt lưu bằng code
khác (ví dụ một thử nghiệm đã revert thêm trường) báo `DinhDangLuotError` nêu rõ trường nào, không đoán.
"""

from dataclasses import MISSING, asdict, dataclass, fields
from typing import Any

from thamdinh.ket_qua_de_xuat import DanhGiaDeXuat, KetQuaMucDeXuat
from thamdinh.tong_hop import KetQuaMuc
from thamdinh.trich_dan import TrichDan, TrichDanDaKiemTra


class DinhDangLuotError(ValueError):
    """Lượt đã lưu không đúng định dạng của code hiện tại (trường lạ hoặc thiếu trường bắt buộc)."""


@dataclass(frozen=True)
class CacBen:
    cong_ty: str  # Bên A | Bên B | không rõ
    ten_cong_ty: str
    ten_khach_hang: str
    trich_dan: tuple[TrichDan, ...]


@dataclass(frozen=True)
class KetQuaLuot:
    hash_pdf: str
    ten_file: str
    checklist: str
    model: str
    che_do: str
    bat_dau: str
    ket_thuc: str
    cac_ben: CacBen | None
    loi_cac_ben: str | None
    muc: tuple[KetQuaMucDeXuat, ...]
    canh_bao: tuple[str, ...] = ()  # cảnh báo chung của Lượt (gắn Chủ đề lỗi, chỉ dùng BM25…)
    ma: str = ""  # mã Lượt, duy nhất
    luot_goc: str | None = None  # Lượt mà Lượt này được tạo từ đó (chạy lại Mục đã có Kết quả đề xuất)
    hash_van_ban: str = ""  # hash nội dung Văn bản hiệu lực đã dùng (bản sửa tay sau đó không ảnh hưởng)


def luot_den_dict(luot: KetQuaLuot) -> dict[str, Any]:
    return asdict(luot)


def luot_tu_dict(d: dict[str, Any]) -> KetQuaLuot:
    """Dựng lại Lượt từ `luot_den_dict` (đã qua JSON). Trường lạ hoặc thiếu trường bắt buộc: `DinhDangLuotError`."""
    ma = d.get("ma", "?")
    con = _con(d, cac_ben=lambda cb: cb and _dung(CacBen, cb, ma, "các bên", **_con(
                   cb, trich_dan=lambda ds: tuple(_dung(TrichDan, t, ma, "Trích dẫn các bên") for t in ds))),
               muc=lambda ds: tuple(_muc(m, ma) for m in ds), canh_bao=tuple)
    return _dung(KetQuaLuot, d, ma, "Lượt", **con)


def _muc(m: dict[str, Any], ma: str) -> KetQuaMucDeXuat:
    cho = f"Mục {m.get('so', '?')}"

    def tieu_chi(t: dict[str, Any]) -> DanhGiaDeXuat:
        o = f"Tiêu chí {t.get('ma', '?')}"
        return _dung(DanhGiaDeXuat, t, ma, o, **_con(
            t, trich_dan=lambda ds: tuple(_dung(TrichDanDaKiemTra, td, ma, f"Trích dẫn của {o}") for td in ds)))

    con = _con(m, ket_qua=lambda kq: kq and _dung(KetQuaMuc, kq, ma, f"Kết quả {cho}",
                                                 **_con(kq, tieu_chi_quyet_dinh=tuple, ghi_chu=tuple)),
               tieu_chi=lambda ds: tuple(tieu_chi(t) for t in ds), dieu_khoan_dua_vao=tuple, canh_bao=tuple)
    return _dung(KetQuaMucDeXuat, m, ma, cho, **con)


def _con(d: dict[str, Any], **dung) -> dict[str, Any]:
    """Dựng các trường con có trong `d` (trường thiếu để `_dung` báo hoặc lấy mặc định)."""
    return {k: f(d[k]) for k, f in dung.items() if k in d}


def _dung(kieu, d: dict[str, Any], ma: str, cho: str, **da_dung):
    """`kieu(**d)` với các trường con đã dựng; trường thiếu mà có mặc định thì lấy mặc định."""
    ten = {f.name for f in fields(kieu)}
    if la := sorted(d.keys() - ten):
        raise DinhDangLuotError(f"Lượt {ma}: trường lạ {', '.join(la)} ở {cho} (lưu bằng code khác?)")
    bat_buoc = {f.name for f in fields(kieu) if f.default is MISSING and f.default_factory is MISSING}
    if thieu := sorted(bat_buoc - d.keys() - da_dung.keys()):
        raise DinhDangLuotError(f"Lượt {ma}: thiếu trường {', '.join(thieu)} ở {cho}")
    return kieu(**{**d, **da_dung})
