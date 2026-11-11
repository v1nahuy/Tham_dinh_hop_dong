"""Từ câu trả lời model của một Mục checklist ra Kết quả đề xuất của Mục (code thuần, issue 26).

Dùng chung cho Lượt thẩm định (`tham_dinh`, ngay sau lần gọi model) và chấm lại Lượt đã lưu (`cham_lai`).
"""

from dataclasses import dataclass
from typing import Any

from thamdinh.checklist import MucChecklist
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.tong_hop import DanhGiaTieuChi, KetQuaMuc, tong_hop_muc
from thamdinh.trich_dan import TrichDan, TrichDanDaKiemTra, kiem_tra_va_ghi

# Độ dài tối đa một câu trích model được viết (schema ép `maxLength`); câu dài đúng bằng ngưỡng là đã bị cắt
TOI_DA_KY_TU_TRICH_DAN = 300


@dataclass(frozen=True)
class DanhGiaDeXuat:
    ma: str
    muc_ket_qua: str  # dat | luu_y | vi_pham
    mo_ta: str
    danh_gia: str  # sau khi code so sánh định lượng / điều kiện
    danh_gia_llm: str
    gia_tri: float | None
    gia_tri_dieu_kien: float | None
    ly_do: str
    trich_dan: tuple[TrichDanDaKiemTra, ...]
    khong_tim_thay_dieu_khoan: bool


@dataclass(frozen=True)
class KetQuaMucDeXuat:
    so: int
    cau_hoi: str
    ket_qua: KetQuaMuc | None  # None khi chưa đánh giá được
    tieu_chi: tuple[DanhGiaDeXuat, ...]
    loi: str | None
    dieu_khoan_dua_vao: tuple[str, ...] = ()  # số hiệu các Điều khoản model được đọc
    canh_bao: tuple[str, ...] = ()  # chế độ truy xuất: Điều khoản bị bỏ vì vượt ngân sách…


def ket_qua_de_xuat_muc(muc: MucChecklist, tra_loi: dict[str, dict[str, Any]], van_ban: VanBanHieuLuc) -> KetQuaMucDeXuat:
    """`tra_loi`: câu trả lời model theo mã Tiêu chí, đủ mọi Tiêu chí của Mục, đúng dạng JSON model trả
    (`danh_gia`, `ly_do`, `trich_dan`, và `gia_tri` / `gia_tri_dieu_kien` khi Tiêu chí có trường đó)."""
    tong_hop = tong_hop_muc(muc, [
        DanhGiaTieuChi(ma, t["danh_gia"], gia_tri=t.get("gia_tri"), gia_tri_dieu_kien=t.get("gia_tri_dieu_kien"),
                       ly_do=t["ly_do"])
        for ma, t in tra_loi.items()
    ])
    tieu_chi = []
    for muc_kq, ds in muc.tieu_chi.items():
        for tc in ds:
            t = tra_loi[tc.ma]
            trich_dan = tuple(
                _kiem_tra_cau_model(TrichDan(td["so_hieu"], td["nguyen_van"]), van_ban)
                for td in t["trich_dan"]
                if td["nguyen_van"].strip()
            )
            tieu_chi.append(DanhGiaDeXuat(
                ma=tc.ma, muc_ket_qua=muc_kq, mo_ta=tc.mo_ta, danh_gia=tong_hop.danh_gia[tc.ma],
                danh_gia_llm=t["danh_gia"], gia_tri=t.get("gia_tri"), gia_tri_dieu_kien=t.get("gia_tri_dieu_kien"),
                ly_do=t["ly_do"], trich_dan=trich_dan, khong_tim_thay_dieu_khoan=not trich_dan,
            ))
    return KetQuaMucDeXuat(muc.so, muc.cau_hoi, tong_hop, tuple(tieu_chi), None)


def _kiem_tra_cau_model(trich_dan: TrichDan, van_ban: VanBanHieuLuc) -> TrichDanDaKiemTra:
    if len(trich_dan.nguyen_van) >= TOI_DA_KY_TU_TRICH_DAN:
        # Bị llama-server cắt ở maxLength: từ cuối dở dang, ký tự cuối thường là rác
        trich_dan = TrichDan(trich_dan.so_hieu, trich_dan.nguyen_van.rsplit(" ", 1)[0] + " …")
    return kiem_tra_va_ghi(trich_dan, van_ban)


def tra_loi_da_luu(muc: KetQuaMucDeXuat) -> dict[str, dict[str, Any]]:
    """Dựng lại câu trả lời model từ Kết quả đề xuất đã lưu, để chấm lại bằng luật hiện tại (`cham_lai`).

    Câu trích rỗng đã bị bỏ và câu bị cắt đã được rút gọn lúc lưu, nên chấm lại cho cùng Đánh giá, Kết quả và Trích dẫn.
    `dieu_khoan_dua_vao` và `canh_bao` không thuộc câu trả lời: người gọi giữ lại từ Mục đã lưu nếu cần.
    """
    return {
        t.ma: {"danh_gia": t.danh_gia_llm, "ly_do": t.ly_do, "gia_tri": t.gia_tri,
               "gia_tri_dieu_kien": t.gia_tri_dieu_kien,
               "trich_dan": [{"so_hieu": td.so_hieu, "nguyen_van": td.nguyen_van} for td in t.trich_dan]}
        for t in muc.tieu_chi
    }
