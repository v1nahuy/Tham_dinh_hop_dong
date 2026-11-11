"""Lượt thẩm định ↔ dict để lưu (issue 27): một chỗ quyết định định dạng lưu và cách xử lý khi định dạng đổi."""

import json
from dataclasses import replace

import pytest
from test_tham_dinh import CHECKLIST, VAN_BAN, ModelGia, TruyXuatGia

from thamdinh.luot import DinhDangLuotError, luot_den_dict, luot_tu_dict
from thamdinh.tham_dinh import tham_dinh


def luot_day_du():
    """Mọi trường khác mặc định: Mục lỗi, Mục có Điều khoản đưa vào và cảnh báo, Lượt tạo từ Lượt khác."""
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}), model="qwen3.5", truy_xuat=TruyXuatGia())
    return replace(kq, ma="luot-1", luot_goc="luot-0", canh_bao=("chỉ dùng BM25",))


def qua_json(d):
    return json.loads(json.dumps(d, ensure_ascii=False))


def test_chuyen_qua_lai_giu_nguyen_luot():
    kq = luot_day_du()

    assert luot_tu_dict(qua_json(luot_den_dict(kq))) == kq


def test_truong_la_o_tieu_chi_bao_loi_dinh_dang_neu_ro_cho():
    # Lượt lưu bằng code thử nghiệm đã revert (issue 19 thêm `cau_hoi` vào Tiêu chí)
    d = qua_json(luot_den_dict(luot_day_du()))
    d["muc"][2]["tieu_chi"][0]["cau_hoi"] = "Hợp đồng có ghi … không?"

    with pytest.raises(DinhDangLuotError) as loi:
        luot_tu_dict(d)

    assert all(x in str(loi.value) for x in ("luot-1", "3.D1", "cau_hoi"))


def test_truong_la_o_cap_luot_cung_bao_loi():
    d = {**qua_json(luot_den_dict(luot_day_du())), "suy_luan": True}

    with pytest.raises(DinhDangLuotError, match="suy_luan"):
        luot_tu_dict(d)


def test_dinh_dang_cu_thieu_truong_tuy_chon_thi_nhan_mac_dinh():
    # Lượt lưu trước khi có chế độ truy xuất và chạy lại Mục: chưa có các trường này
    kq = luot_day_du()
    d = qua_json(luot_den_dict(kq))
    for k in ("canh_bao", "luot_goc", "hash_van_ban"):
        del d[k]
    for m in d["muc"]:
        del m["dieu_khoan_dua_vao"], m["canh_bao"]

    cu = luot_tu_dict(d)

    assert (cu.canh_bao, cu.luot_goc, cu.hash_van_ban) == ((), None, "")
    assert all((m.dieu_khoan_dua_vao, m.canh_bao) == ((), ()) for m in cu.muc)
    assert [m.tieu_chi for m in cu.muc] == [m.tieu_chi for m in kq.muc]


@pytest.mark.parametrize("cho, bo", [
    ((), "model"), ((), "muc"),
    (("muc", 2), "tieu_chi"),  # Mục 3
    (("muc", 2, "tieu_chi", 0), "trich_dan"),  # Tiêu chí 3.D1
    (("cac_ben",), "ten_cong_ty"),
])
def test_thieu_truong_bat_buoc_o_moi_cap_bao_loi(cho, bo):
    d = qua_json(luot_den_dict(luot_day_du()))
    o = d
    for k in cho:
        o = o[k]
    del o[bo]

    with pytest.raises(DinhDangLuotError, match=f"thiếu trường {bo}"):
        luot_tu_dict(d)
