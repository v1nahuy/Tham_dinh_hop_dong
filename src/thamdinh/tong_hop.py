"""Tổng hợp Kết quả của một Mục checklist từ các Đánh giá tiêu chí (code thuần, không dùng LLM)."""

import operator
from dataclasses import dataclass

from thamdinh.checklist import GHI_CHU_CAN_THONG_TIN_NGOAI, MucChecklist, TieuChi

THOA, KHONG_THOA, KHONG_RO = "thoa", "khong_thoa", "khong_ro"
DANH_GIA_HOP_LE = (THOA, KHONG_THOA, KHONG_RO)
TEN_DANH_GIA = {THOA: "thỏa", KHONG_THOA: "không thỏa", KHONG_RO: "không rõ"}
TEN_KET_QUA = {"dat": "Đạt", "luu_y": "Lưu ý", "vi_pham": "Vi phạm"}
SO_SANH = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}


@dataclass(frozen=True)
class DanhGiaTieuChi:
    """Đánh giá một Tiêu chí như LLM trả về.

    `danh_gia` dùng cho tiêu chí định tính (và phần định tính của tiêu chí có điều kiện).
    `gia_tri` là giá trị trích xuất cho tiêu chí định lượng; `gia_tri_dieu_kien` là giá trị của trường điều kiện.
    """

    ma: str
    danh_gia: str | None = None
    gia_tri: float | None = None
    gia_tri_dieu_kien: float | None = None
    ly_do: str = ""


@dataclass(frozen=True)
class KetQuaMuc:
    so: int
    ket_qua: str  # dat | luu_y | vi_pham
    danh_gia: dict[str, str]  # Đánh giá tiêu chí cuối cùng (sau khi code so sánh), theo mã
    tieu_chi_quyet_dinh: tuple[str, ...]
    giai_thich: str
    ghi_chu: tuple[str, ...]


def so_sanh(gia_tri: float | None, phep_so_sanh: str, nguong: float) -> str:
    if gia_tri is None:
        return KHONG_RO
    return THOA if SO_SANH[phep_so_sanh](gia_tri, nguong) else KHONG_THOA


def tong_hop_muc(muc: MucChecklist, danh_gia: list[DanhGiaTieuChi]) -> KetQuaMuc:
    theo_ma = {dg.ma: dg for dg in danh_gia}
    cuoi: dict[str, str] = {}
    for muc_kq, ds in muc.tieu_chi.items():
        for tc in ds:
            cuoi[tc.ma] = _danh_gia_cuoi(tc, muc_kq, theo_ma.get(tc.ma))

    def loc(muc_kq: str, *gia_tri: str) -> list[TieuChi]:
        return [tc for tc in muc.tieu_chi[muc_kq] if cuoi[tc.ma] in gia_tri]

    vi_pham = loc("vi_pham", THOA)
    if vi_pham:
        ket_qua, quyet_dinh = "vi_pham", vi_pham
    else:
        quyet_dinh = (
            loc("luu_y", THOA)
            + loc("dat", KHONG_THOA, KHONG_RO)
            + loc("luu_y", KHONG_RO)
            + loc("vi_pham", KHONG_RO)
        )
        ket_qua = "luu_y" if quyet_dinh else "dat"
        if not quyet_dinh:
            quyet_dinh = muc.tieu_chi["dat"]

    ghi_chu: list[str] = []
    if ket_qua == "vi_pham" and any(tc.can_thong_tin_ngoai for tc in quyet_dinh):
        ghi_chu.append(GHI_CHU_CAN_THONG_TIN_NGOAI)
    if ket_qua == "luu_y":
        khong_ro = [tc for tc in quyet_dinh if cuoi[tc.ma] == KHONG_RO]
        if khong_ro and muc.ghi_chu_khong_ro:
            ghi_chu.append(muc.ghi_chu_khong_ro)
        elif khong_ro:
            ghi_chu += [f"chưa xác định được: {tc.mo_ta}" for tc in khong_ro]

    if ket_qua == "dat":
        giai_thich = "Đạt: mọi tiêu chí Đạt đều thỏa."
    else:
        ly_do = "; ".join(f"{tc.ma} {TEN_DANH_GIA[cuoi[tc.ma]]}" for tc in quyet_dinh)
        giai_thich = f"{TEN_KET_QUA[ket_qua]} do: {ly_do}."

    return KetQuaMuc(
        so=muc.so,
        ket_qua=ket_qua,
        danh_gia=cuoi,
        tieu_chi_quyet_dinh=tuple(tc.ma for tc in quyet_dinh),
        giai_thich=giai_thich,
        ghi_chu=tuple(ghi_chu),
    )


def _danh_gia_cuoi(tc: TieuChi, muc_kq: str, dg: DanhGiaTieuChi | None) -> str:
    if dg is None:
        return KHONG_RO
    if tc.dieu_kien:
        ap_dung = so_sanh(dg.gia_tri_dieu_kien, tc.dieu_kien.phep_so_sanh, tc.dieu_kien.nguong)
        if ap_dung == KHONG_RO:
            return KHONG_RO
        if ap_dung == KHONG_THOA:
            # Tiêu chí không áp dụng: Đạt coi là thỏa, Lưu ý / Vi phạm coi là không thỏa
            return THOA if muc_kq == "dat" else KHONG_THOA
    if tc.loai == "dinh_luong":
        if dg.gia_tri is None:
            # Hợp đồng không nêu giá trị: Đạt không được đáp ứng, rủi ro Lưu ý / Vi phạm không xảy ra
            return KHONG_THOA
        return so_sanh(dg.gia_tri, tc.phep_so_sanh, tc.nguong)
    if dg.danh_gia is None:
        return KHONG_RO
    if dg.danh_gia not in DANH_GIA_HOP_LE:
        raise ValueError(f"Tiêu chí {tc.ma}: danh_gia '{dg.danh_gia}' không hợp lệ, phải là một trong {DANH_GIA_HOP_LE}")
    return dg.danh_gia
