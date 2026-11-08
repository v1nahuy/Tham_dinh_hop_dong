"""So sánh ba nguồn: chế độ toàn văn, chế độ truy xuất, Bộ chuẩn (issue 15)."""

from dataclasses import replace

import pytest
from test_tham_dinh import CHECKLIST, THAT, VAN_BAN, ModelGia

from thamdinh.bo_chuan import BoChuan, DanhGiaChuan
from thamdinh.so_sanh import do_phu_tu_luot, so_sanh_lan_chay, so_sanh_nguon
from thamdinh.tham_dinh import tham_dinh

TONG = sum(len(ds) for m in CHECKLIST.muc for ds in m.tieu_chi.values())


def luot(che_do="toan_van", sua_muc=None, loi_muc=None):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(sua_muc=sua_muc, loi_muc=loi_muc), model="qwen3.5")
    return replace(kq, che_do=che_do, ma=f"luot-{che_do}")


def tl(danh_gia, **kw):
    return {"danh_gia": danh_gia, "ly_do": "…", "trich_dan": [THAT], **kw}


def chuan(danh_gia: dict[str, str], gia_tri=None, ket_qua=None) -> BoChuan:
    gia_tri = gia_tri or {}
    return BoChuan("HĐ TOSS.pdf", "abc123", "dau-ra 1.1", "", "",
                   {ma: DanhGiaChuan(ma, dg, gia_tri.get(ma), (), "", "") for ma, dg in danh_gia.items()},
                   ket_qua or {})


def test_hai_lan_chay_giong_nhau_thi_khop_het():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat"))

    assert (kq.toan_van_truy_xuat.khop, kq.toan_van_truy_xuat.tong) == (TONG, TONG)
    assert kq.bat_dong == ()


def test_tieu_chi_khac_danh_gia_la_bat_dong_giua_hai_che_do():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat", sua_muc={3: {"3.D1": tl("khong_ro")}}))

    assert (kq.toan_van_truy_xuat.khop, kq.toan_van_truy_xuat.tong) == (TONG - 1, TONG)
    assert [d.ma for d in kq.bat_dong] == ["3.D1"]
    d = kq.bat_dong[0]
    assert (d.so_muc, d.toan_van.danh_gia, d.truy_xuat.danh_gia) == (3, "thoa", "khong_ro")


def test_muc_chua_danh_gia_duoc_tinh_khong_khop_va_ghi_rieng():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat", loi_muc={3: 2}))

    so_tc_muc_3 = sum(len(ds) for ds in CHECKLIST.muc[2].tieu_chi.values())
    assert kq.toan_van_truy_xuat.khop == TONG - so_tc_muc_3
    assert kq.chua_danh_gia == {"truy_xuat": (3,)}
    assert kq.muc_toan_van_truy_xuat.khop == len(CHECKLIST.muc) - 1


def test_so_voi_bo_chuan_chi_tinh_tieu_chi_da_dien():
    tv = luot()
    tx = luot("truy_xuat", sua_muc={1: {"1.D1": tl("khong_thoa")}})

    kq = so_sanh_nguon(CHECKLIST, tv, tx, chuan({"1.D1": "thoa", "1.V1": "thoa"}))

    assert kq.so_tieu_chi_chuan == 2
    assert (kq.toan_van_chuan.khop, kq.toan_van_chuan.tong) == (1, 2)  # 1.V1: model giả trả khong_thoa
    assert (kq.truy_xuat_chuan.khop, kq.truy_xuat_chuan.tong) == (0, 2)
    assert (kq.toan_van_truy_xuat.khop, kq.toan_van_truy_xuat.tong) == (TONG - 1, TONG)  # không phụ thuộc Bộ chuẩn


def test_chua_co_bo_chuan_thi_khong_co_ty_le_so_voi_chuan():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat"))

    assert kq.so_tieu_chi_chuan == 0
    assert (kq.toan_van_chuan.khop, kq.toan_van_chuan.tong) == (0, 0)


def test_bat_dong_tinh_ca_khi_hai_che_do_giong_nhau_nhung_khac_bo_chuan():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat"), chuan({"1.D1": "khong_ro"}))

    assert [d.ma for d in kq.bat_dong] == ["1.D1"]


def test_ket_qua_muc_so_voi_bo_chuan():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat"), chuan({}, ket_qua={1: "vi_pham", 2: "dat", 3: None}))

    de_xuat_1 = luot().muc[0].ket_qua.ket_qua
    assert kq.muc_toan_van_chuan.tong == 2  # Mục 3 chưa điền ket_qua
    assert kq.muc[0].so == 1
    assert kq.muc[0].toan_van == de_xuat_1
    assert kq.muc[0].chuan == "vi_pham"


def test_gia_tri_dinh_luong_so_rieng_va_phai_dung_con_so():
    tx = luot("truy_xuat", sua_muc={7: {"7.D1": tl("thoa", gia_tri=5)}})

    kq = so_sanh_nguon(CHECKLIST, luot(), tx, chuan({"7.D1": "thoa", "1.V2": "khong_thoa"},
                                                    gia_tri={"7.D1": 8, "1.V2": 39_820_000_000}))

    # 1.V2: giá trị nằm ở điều kiện của Tiêu chí (gia_tri_dieu_kien)
    assert (kq.gia_tri_toan_van_chuan.khop, kq.gia_tri_toan_van_chuan.tong) == (2, 2)
    assert (kq.gia_tri_truy_xuat_chuan.khop, kq.gia_tri_truy_xuat_chuan.tong) == (1, 2)
    assert kq.gia_tri_toan_van_truy_xuat.tong == sum(
        tc.truong is not None or tc.dieu_kien is not None for m in CHECKLIST.muc for ds in m.tieu_chi.values() for tc in ds
    )


def test_liet_ke_trich_dan_khong_xac_minh_duoc_cua_tung_che_do():
    bia = {"so_hieu": "Điều 10", "nguyen_van": "Câu này không có trong hợp đồng"}
    tx = luot("truy_xuat", sua_muc={3: {"3.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [bia]}}})

    kq = so_sanh_nguon(CHECKLIST, luot(), tx)

    assert kq.khong_xac_minh["toan_van"] == ()
    assert [(ma, td.nguyen_van) for ma, td in kq.khong_xac_minh["truy_xuat"]] == [("3.D1", bia["nguyen_van"])]


def test_hai_luot_khac_hop_dong_thi_bao_loi():
    with pytest.raises(ValueError, match="Hợp đồng khác"):
        so_sanh_nguon(CHECKLIST, luot(), replace(luot("truy_xuat"), hash_pdf="khac"))


def test_ghi_canh_bao_khi_hai_luot_dung_van_ban_khac_nhau():
    kq = so_sanh_nguon(CHECKLIST, luot(), replace(luot("truy_xuat"), hash_van_ban="khac"))

    assert any("Văn bản hiệu lực" in c for c in kq.canh_bao)


def test_do_phu_theo_dieu_khoan_luot_da_doc():
    cau = "Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm"
    tx = luot("truy_xuat")
    da_doc = replace(tx, muc=tuple(replace(m, dieu_khoan_dua_vao=("Điều 10",) if m.so == 7 else ()) for m in tx.muc))

    kq = do_phu_tu_luot({"7.D2": (cau,), "1.D1": (cau,), "1.V1": ("Câu chép sai",)}, CHECKLIST, VAN_BAN, da_doc)

    assert {(d.ma, d.trang_thai) for d in kq} == {
        ("7.D2", "co"), ("1.D1", "thieu"), ("1.V1", "khong_co_trong_van_ban"),
    }


# --- So hai lần chạy cùng chế độ (trước / sau khi đổi prompt) theo Bộ chuẩn (issue 17) ----------------


def test_lan_chay_dem_so_dung_va_cac_tieu_chi_doi_chieu():
    truoc = luot("truy_xuat")  # model giả: Tiêu chí Đạt là thoa, còn lại khong_thoa
    sau = luot("truy_xuat", sua_muc={3: {"3.D1": tl("khong_thoa"), "3.D2": tl("khong_thoa")}})

    kq = so_sanh_lan_chay(CHECKLIST, truoc, sau, chuan({"3.D1": "khong_thoa", "3.D2": "thoa", "3.V1": "khong_thoa"}), [3])

    assert (kq.truoc.khop, kq.truoc.tong) == (2, 3)
    assert (kq.sau.khop, kq.sau.tong) == (2, 3)
    assert [d.ma for d in kq.sai_thanh_dung] == ["3.D1"]
    assert [d.ma for d in kq.dung_thanh_sai] == ["3.D2"]


def test_lan_chay_chi_tinh_cac_muc_duoc_chon():
    sau = luot("truy_xuat", sua_muc={4: {"4.D1": tl("khong_thoa")}})

    kq = so_sanh_lan_chay(CHECKLIST, luot("truy_xuat"), sau, chuan({"3.D1": "thoa", "4.D1": "thoa"}), [3])

    assert (kq.sau.khop, kq.sau.tong) == (1, 1)
    assert kq.dung_thanh_sai == ()


def test_lan_chay_canh_bao_khi_muc_doc_dieu_khoan_khac_nhau():
    def doc(l, dieu_khoan):
        return replace(l, muc=tuple(replace(m, dieu_khoan_dua_vao=dieu_khoan.get(m.so, ("Điều 10",))) for m in l.muc))

    truoc = doc(luot("truy_xuat"), {})
    sau = doc(luot("truy_xuat"), {3: ("Điều 10", "Phần mở đầu"), 5: ()})

    kq = so_sanh_lan_chay(CHECKLIST, truoc, sau, chuan({"3.D1": "thoa"}), [3, 4])

    assert len(kq.canh_bao) == 1  # Mục 5 khác nhưng không được chọn
    assert "Mục 3" in kq.canh_bao[0] and "Phần mở đầu" in kq.canh_bao[0]
