"""Bảng tóm tắt các Mục checklist của một Lượt (trang Kết quả, báo cáo)."""

from dataclasses import dataclass

from thamdinh.kho_luot import KetQuaDuyet
from thamdinh.luot import KetQuaLuot
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC


@dataclass(frozen=True)
class DongBang:
    so: int
    cau_hoi: str
    de_xuat: str | None  # dat | luu_y | vi_pham; None khi chưa đánh giá được
    da_duyet: str | None  # None khi chưa duyệt
    khong_xac_minh: int  # số Trích dẫn không xác minh được (của bản duyệt nếu đã duyệt)
    loi: str | None


def bang_ket_qua(luot: KetQuaLuot, duyet: dict[int, KetQuaDuyet]) -> list[DongBang]:
    bang = []
    for m in sorted(luot.muc, key=lambda m: m.so):
        if m.so in duyet:
            trich_dan = duyet[m.so].trich_dan
        else:
            trich_dan = [td for tc in m.tieu_chi for td in tc.trich_dan]
        bang.append(DongBang(
            so=m.so,
            cau_hoi=m.cau_hoi,
            de_xuat=m.ket_qua.ket_qua if m.ket_qua else None,
            da_duyet=duyet[m.so].ket_qua if m.so in duyet else None,
            khong_xac_minh=sum(td.trang_thai == KHONG_XAC_MINH_DUOC for td in trich_dan),
            loi=m.loi,
        ))
    return bang
