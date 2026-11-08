import pytest

from thamdinh.checklist import GHI_CHU_CAN_THONG_TIN_NGOAI, DieuKien, MucChecklist, TieuChi
from thamdinh.tong_hop import DanhGiaTieuChi, tong_hop_muc


def dinh_tinh(ma, mo_ta=None, **kw):
    return TieuChi(ma=ma, mo_ta=mo_ta or f"mô tả {ma}", loai="dinh_tinh", **kw)


def muc(dat, luu_y=(), vi_pham=(), ghi_chu_khong_ro=None):
    return MucChecklist(
        so=7,
        cau_hoi="?",
        chu_de=[],
        danh_muc=[],
        tieu_chi={"dat": list(dat), "luu_y": list(luu_y), "vi_pham": list(vi_pham)},
        can_cu_phap_ly=[],
        ghi_chu_khong_ro=ghi_chu_khong_ro,
    )


MUC_7 = muc(dat=[dinh_tinh("D1"), dinh_tinh("D2")], luu_y=[dinh_tinh("L1")], vi_pham=[dinh_tinh("V1")])


def danh_gia(**theo_ma):
    return [DanhGiaTieuChi(ma, d) for ma, d in theo_ma.items()]


@pytest.mark.parametrize(
    "dg, ket_qua, quyet_dinh",
    [
        # Mọi tiêu chí Đạt thỏa, không Lưu ý / Vi phạm nào thỏa
        (danh_gia(D1="thoa", D2="thoa", L1="khong_thoa", V1="khong_thoa"), "dat", ("D1", "D2")),
        # Vi phạm thắng mọi thứ khác
        (danh_gia(D1="thoa", D2="thoa", L1="thoa", V1="thoa"), "vi_pham", ("V1",)),
        (danh_gia(D1="khong_ro", D2="khong_thoa", L1="khong_ro", V1="thoa"), "vi_pham", ("V1",)),
        # Lưu ý: tiêu chí Lưu ý thỏa
        (danh_gia(D1="thoa", D2="thoa", L1="thoa", V1="khong_thoa"), "luu_y", ("L1",)),
        # Lưu ý: tiêu chí Đạt không thỏa / không rõ
        (danh_gia(D1="khong_thoa", D2="thoa", L1="khong_thoa", V1="khong_thoa"), "luu_y", ("D1",)),
        (danh_gia(D1="thoa", D2="khong_ro", L1="khong_thoa", V1="khong_thoa"), "luu_y", ("D2",)),
        # Lưu ý: tiêu chí Lưu ý / Vi phạm không rõ (Q42)
        (danh_gia(D1="thoa", D2="thoa", L1="khong_ro", V1="khong_thoa"), "luu_y", ("L1",)),
        (danh_gia(D1="thoa", D2="thoa", L1="khong_thoa", V1="khong_ro"), "luu_y", ("V1",)),
        # Nhiều lý do Lưu ý cùng lúc
        (danh_gia(D1="khong_thoa", D2="khong_ro", L1="thoa", V1="khong_ro"), "luu_y", ("L1", "D1", "D2", "V1")),
        # Thiếu Đánh giá tiêu chí coi là không rõ
        (danh_gia(D1="thoa", L1="khong_thoa", V1="khong_thoa"), "luu_y", ("D2",)),
    ],
)
def test_muc_xau_nhat_thang(dg, ket_qua, quyet_dinh):
    kq = tong_hop_muc(MUC_7, dg)

    assert kq.ket_qua == ket_qua
    assert kq.tieu_chi_quyet_dinh == quyet_dinh


def test_giai_thich_neu_tieu_chi_quyet_dinh():
    kq = tong_hop_muc(MUC_7, danh_gia(D1="khong_thoa", D2="thoa", L1="thoa", V1="khong_thoa"))

    assert "L1 thỏa" in kq.giai_thich
    assert "D1 không thỏa" in kq.giai_thich


def test_danh_gia_khong_hop_le_bi_tu_choi():
    with pytest.raises(ValueError, match="D1"):
        tong_hop_muc(MUC_7, danh_gia(D1="dat", D2="thoa", L1="khong_thoa", V1="khong_thoa"))


# --- Ghi chú --------------------------------------------------------------------------------------


def test_khong_ro_dung_ghi_chu_cua_muc():
    m = muc(dat=[dinh_tinh("6.D1")], luu_y=[dinh_tinh("6.L1")], vi_pham=[dinh_tinh("6.V1")], ghi_chu_khong_ro="cần xác minh lại EAR")

    kq = tong_hop_muc(m, danh_gia(**{"6.D1": "khong_ro", "6.L1": "khong_ro", "6.V1": "khong_thoa"}))

    assert kq.ket_qua == "luu_y"
    assert kq.ghi_chu == ("cần xác minh lại EAR",)


def test_khong_ro_khi_muc_khong_co_ghi_chu_thi_neu_tieu_chi():
    kq = tong_hop_muc(MUC_7, danh_gia(D1="thoa", D2="thoa", L1="khong_thoa", V1="khong_ro"))

    assert kq.ghi_chu == ("chưa xác định được: mô tả V1",)


def test_vi_pham_do_tieu_chi_can_thong_tin_ngoai_hop_dong():
    m = muc(dat=[dinh_tinh("D1")], vi_pham=[dinh_tinh("V1", can_thong_tin_ngoai=True), dinh_tinh("V2")])

    ngoai = tong_hop_muc(m, danh_gia(D1="thoa", V1="thoa", V2="khong_thoa"))
    trong = tong_hop_muc(m, danh_gia(D1="thoa", V1="khong_thoa", V2="thoa"))

    assert GHI_CHU_CAN_THONG_TIN_NGOAI in ngoai.ghi_chu
    assert GHI_CHU_CAN_THONG_TIN_NGOAI not in trong.ghi_chu


# --- Tiêu chí định lượng: code so sánh ------------------------------------------------------------

MUC_PHAT = muc(
    dat=[TieuChi("7.D1", "Phạt ≤ 8%", "dinh_luong", truong="muc_phat", phep_so_sanh="<=", nguong=8)],
    vi_pham=[TieuChi("7.V1", "Phạt > 8%", "dinh_luong", truong="muc_phat", phep_so_sanh=">", nguong=8)],
)


@pytest.mark.parametrize(
    "gia_tri, ket_qua",
    [(8, "dat"), (5.5, "dat"), (12, "vi_pham"), (None, "luu_y")],
)
def test_tieu_chi_dinh_luong_do_code_so_sanh(gia_tri, ket_qua):
    # LLM có trả danh_gia sai cũng không ảnh hưởng: chỉ giá trị trích xuất được dùng
    dg = [DanhGiaTieuChi("7.D1", "khong_thoa", gia_tri=gia_tri), DanhGiaTieuChi("7.V1", "thoa", gia_tri=gia_tri)]

    assert tong_hop_muc(MUC_PHAT, dg).ket_qua == ket_qua


# --- Tiêu chí có điều kiện (1.V2) -----------------------------------------------------------------

TREN_2_TY = DieuKien("gia_tri_hop_dong_vnd", ">", 2_000_000_000)
MUC_1 = muc(
    dat=[dinh_tinh("1.D1")],
    vi_pham=[dinh_tinh("1.V2", "Trên 2 tỷ, người ký không phải Giám đốc", dieu_kien=TREN_2_TY)],
)


@pytest.mark.parametrize(
    "gia_tri_hd, nguoi_ky_khong_phai_gd, ket_qua",
    [
        (39_820_000_000, "thoa", "vi_pham"),  # áp dụng, Phó GĐ ký
        (39_820_000_000, "khong_thoa", "dat"),  # áp dụng, Giám đốc ký
        (1_500_000_000, "thoa", "dat"),  # không áp dụng: dưới 2 tỷ thì xét tiêu chí Đạt
        (None, "thoa", "luu_y"),  # thiếu giá trị Hợp đồng: không rõ
    ],
)
def test_tieu_chi_co_dieu_kien(gia_tri_hd, nguoi_ky_khong_phai_gd, ket_qua):
    dg = [
        DanhGiaTieuChi("1.D1", "thoa"),
        DanhGiaTieuChi("1.V2", nguoi_ky_khong_phai_gd, gia_tri_dieu_kien=gia_tri_hd),
    ]

    assert tong_hop_muc(MUC_1, dg).ket_qua == ket_qua


def test_tieu_chi_dat_co_dieu_kien_khong_ap_dung_thi_thoa():
    m = muc(dat=[dinh_tinh("D1", dieu_kien=TREN_2_TY)])

    kq = tong_hop_muc(m, [DanhGiaTieuChi("D1", "khong_thoa", gia_tri_dieu_kien=1_000_000_000)])

    assert kq.ket_qua == "dat"
