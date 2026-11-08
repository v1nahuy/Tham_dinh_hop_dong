"""Bảng 17 Mục của trang Kết quả (issue 11, Q79)."""

from test_tham_dinh import CHECKLIST, VAN_BAN, ModelGia

from thamdinh.bang_ket_qua import bang_ket_qua
from thamdinh.kho_luot import KetQuaDuyet
from thamdinh.tham_dinh import TrichDanDaKiemTra, tham_dinh

BIA = {"so_hieu": "Điều 1", "nguyen_van": "Câu này không có trong hợp đồng"}
LUOT = tham_dinh(
    VAN_BAN, CHECKLIST,
    ModelGia(loi_muc={7: 2}, sua_muc={1: {"1.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [BIA]}}}),
)


def dong(bang, so):
    return next(d for d in bang if d.so == so)


def test_moi_muc_mot_dong_theo_thu_tu():
    bang = bang_ket_qua(LUOT, {})

    assert [d.so for d in bang] == list(range(1, 18))
    assert dong(bang, 2).cau_hoi.startswith("Công ty có được thực hiện")
    assert dong(bang, 2).de_xuat in ("dat", "luu_y", "vi_pham")
    assert dong(bang, 2).da_duyet is None


def test_muc_chua_danh_gia_duoc_hien_loi():
    d = dong(bang_ket_qua(LUOT, {}), 7)

    assert d.de_xuat is None
    assert "JSON sai" in d.loi


def test_dem_trich_dan_khong_xac_minh_duoc():
    assert dong(bang_ket_qua(LUOT, {}), 1).khong_xac_minh == 1
    assert dong(bang_ket_qua(LUOT, {}), 2).khong_xac_minh == 0


def test_muc_da_duyet_lay_ket_qua_va_trich_dan_cua_ban_duyet():
    duyet = KetQuaDuyet(1, "vi_pham", "Người ký chưa được ủy quyền",
                        (TrichDanDaKiemTra("Điều 10", "Mức phạt", "khop", None),), "Huy", "2026-10-30T10:00:00", 2)

    d = dong(bang_ket_qua(LUOT, {1: duyet}), 1)

    assert d.de_xuat == LUOT.muc[0].ket_qua.ket_qua
    assert d.da_duyet == "vi_pham"
    assert d.khong_xac_minh == 0
