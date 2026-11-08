import re
from pathlib import Path

import pytest
import yaml

from thamdinh.checklist import load_checklist

FILE = Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml"


@pytest.fixture(scope="module")
def checklist():
    return load_checklist(FILE)


def test_du_17_muc_danh_so_lien_tuc(checklist):
    assert [m.so for m in checklist.muc] == list(range(1, 18))


def test_moi_muc_co_tieu_chi_dat_va_vi_pham(checklist):
    for muc in checklist.muc:
        assert muc.tieu_chi["dat"], f"Mục {muc.so} thiếu tiêu chí Đạt"
        assert muc.tieu_chi["vi_pham"], f"Mục {muc.so} thiếu tiêu chí Vi phạm"


def test_moi_muc_co_chu_de(checklist):
    for muc in checklist.muc:
        assert muc.chu_de, f"Mục {muc.so} chưa khai báo Chủ đề"


def test_muc_6_ghi_chu_xac_minh_lai_ear(checklist):
    assert checklist.muc[5].ghi_chu_khong_ro == "cần xác minh lại EAR"


def test_muc_11_dung_khong_chiu_thue_thay_cho_0_phan_tram(checklist):
    muc_11 = checklist.muc[10]
    mo_ta = " ".join(t.mo_ta for ds in muc_11.tieu_chi.values() for t in ds)
    assert "không chịu thuế" in mo_ta
    assert not re.search(r"(?<![\d,.])0\s*%", mo_ta)
    assert any("48/2024/QH15" in c for c in muc_11.can_cu_phap_ly)


def test_danh_muc_nganh_nghe_dang_ky_du_tu_v1(checklist):
    nganh = yaml.safe_load(checklist.danh_muc_tham_chieu["nganh-nghe-dang-ky"].read_text(encoding="utf-8"))
    ma_nganh = {n["ma"] for n in nganh["muc"]}
    assert nganh["trang_thai"] == "da-soan"
    assert len(ma_nganh) == 44
    assert {"6219", "4652", "9112", "7822"} <= ma_nganh


def _tieu_chi(checklist):
    return {t.ma: t for m in checklist.muc for ds in m.tieu_chi.values() for t in ds}


def test_muc_1_gia_tri_tren_2_ty_ma_nguoi_ky_khong_phai_giam_doc_la_vi_pham(checklist):
    muc_1 = checklist.muc[0]
    assert muc_1.tieu_chi["luu_y"] == []
    v2 = _tieu_chi(checklist)["1.V2"]
    assert (v2.dieu_kien.truong, v2.dieu_kien.phep_so_sanh, v2.dieu_kien.nguong) == ("gia_tri_hop_dong_vnd", ">", 2_000_000_000)


def test_muc_11_dieu_chinh_thue_bat_loi_la_vi_pham(checklist):
    ma = {t.ma for t in checklist.muc[10].tieu_chi["vi_pham"]}
    assert "11.V3" in ma
    assert "11.L4" not in _tieu_chi(checklist)


def test_tieu_chi_can_thong_tin_ngoai_hop_dong(checklist):
    co_co = {ma for ma, t in _tieu_chi(checklist).items() if t.can_thong_tin_ngoai}
    assert co_co == {"2.V2", "9.V1", "13.V2", "14.D1", "14.V1"}


@pytest.mark.parametrize("ma", ["nganh-nghe-dang-ky", "nganh-nghe-co-dieu-kien", "thue-gtgt", "dau-hieu-ear"])
def test_danh_muc_da_soan_va_moi_muc_co_nguon(checklist, ma):
    danh_muc = yaml.safe_load(checklist.danh_muc_tham_chieu[ma].read_text(encoding="utf-8"))
    assert danh_muc["trang_thai"] != "chua-soan"
    assert danh_muc["muc"], f"Danh mục {ma} rỗng"
    for muc in danh_muc["muc"]:
        assert muc.get("nguon") or danh_muc.get("nguon"), f"Danh mục {ma}, mục {muc['ma']}: thiếu nguồn"


def test_moi_tieu_chi_dinh_tinh_co_cau_hoi_su_kien(checklist):
    tieu_chi = {tc.ma: tc for m in checklist.muc for ds in m.tieu_chi.values() for tc in ds}
    assert all(tc.cau_hoi for tc in tieu_chi.values() if tc.loai == "dinh_tinh")
    assert tieu_chi["8.V2"].thoa_khi == "khong"  # "Không có điều khoản về hậu quả chấm dứt"
    assert tieu_chi["8.V2"].cau_hoi == "Hợp đồng có điều khoản về hậu quả chấm dứt Hợp đồng không?"
