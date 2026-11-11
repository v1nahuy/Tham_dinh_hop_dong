"""Từ câu trả lời model của một Mục ra Kết quả đề xuất của Mục, không gọi model (issue 26)."""

from test_tham_dinh import BIA, CHECKLIST, THAT, VAN_BAN

from thamdinh.ket_qua_de_xuat import ket_qua_de_xuat_muc, tra_loi_da_luu

MUC_1 = CHECKLIST.muc[0]  # 1.D1, 1.V1–1.V3 định tính; 1.V2 có điều kiện giá trị Hợp đồng > 2 tỷ đồng


def tl(danh_gia, *trich_dan, **them):
    return {"danh_gia": danh_gia, "ly_do": "…", "trich_dan": list(trich_dan), **them}


def test_tong_hop_ket_qua_va_kiem_tra_trich_dan():
    tra_loi = {"1.D1": tl("thoa", THAT), "1.V1": tl("khong_thoa", BIA), "1.V2": tl("thoa", gia_tri_dieu_kien=1_000_000_000),
               "1.V3": tl("khong_thoa", THAT)}

    kq = ket_qua_de_xuat_muc(MUC_1, tra_loi, VAN_BAN)

    assert (kq.so, kq.loi, kq.ket_qua.ket_qua) == (1, None, "dat")
    tc = {t.ma: t for t in kq.tieu_chi}
    assert [t.ma for t in kq.tieu_chi] == ["1.D1", "1.V1", "1.V2", "1.V3"]
    assert (tc["1.D1"].muc_ket_qua, tc["1.D1"].danh_gia, tc["1.D1"].danh_gia_llm) == ("dat", "thoa", "thoa")
    assert [d.trang_thai for d in tc["1.D1"].trich_dan] == ["khop"]
    assert [d.trang_thai for d in tc["1.V1"].trich_dan] == ["khong_xac_minh_duoc"]
    assert (tc["1.V2"].trich_dan, tc["1.V2"].khong_tim_thay_dieu_khoan) == ((), True)


def tra_loi_muc_1(**sua):
    return {"1.D1": tl("thoa", THAT), "1.V1": tl("khong_thoa"), "1.V2": tl("khong_thoa", gia_tri_dieu_kien=1e9),
            "1.V3": tl("khong_thoa"), **sua}


def test_cau_trich_bi_cat_o_300_ky_tu_thi_bo_tu_cuoi_do_dang():
    # llama-server cắt ở maxLength 300: phần còn lại vẫn đúng chữ Hợp đồng nhưng từ cuối dở dang
    cat = THAT["nguyen_van"] + " " + "x" * (300 - len(THAT["nguyen_van"]) - 1)
    kq = ket_qua_de_xuat_muc(MUC_1, tra_loi_muc_1(**{"1.D1": tl("thoa", {"so_hieu": "Điều 10", "nguyen_van": cat})}), VAN_BAN)

    (td,) = kq.tieu_chi[0].trich_dan
    assert td.nguyen_van == THAT["nguyen_van"] + " …"
    assert td.trang_thai == "khop"


def test_cau_trich_rong_bi_bo():
    kq = ket_qua_de_xuat_muc(MUC_1, tra_loi_muc_1(**{"1.D1": tl("thoa", {"so_hieu": "Điều 10", "nguyen_van": "  "})}),
                             VAN_BAN)

    assert (kq.tieu_chi[0].trich_dan, kq.tieu_chi[0].khong_tim_thay_dieu_khoan) == ((), True)


def test_tieu_chi_dinh_luong_giu_gia_tri_va_code_so_voi_nguong():
    muc_7 = CHECKLIST.muc[6]  # 7.D1, 7.V1 định lượng (mức phạt so với ngưỡng)
    tra_loi = {tc.ma: tl("khong_thoa", THAT) for ds in muc_7.tieu_chi.values() for tc in ds}
    tra_loi["7.D1"] = tl("khong_ro", THAT, gia_tri=8)

    kq = ket_qua_de_xuat_muc(muc_7, tra_loi, VAN_BAN)

    d1 = next(t for t in kq.tieu_chi if t.ma == "7.D1")
    assert (d1.gia_tri, d1.danh_gia_llm, d1.danh_gia) == (8, "khong_ro", "thoa")  # 8% ≤ ngưỡng: code quyết, không theo model


def test_cham_lai_muc_da_luu_tu_cau_tra_loi_dung_lai_ra_dung_muc_do():
    # cham_lai không có câu trả lời gốc của model, chỉ có Mục đã lưu: dựng lại rồi chấm phải ra y như cũ
    cat = THAT["nguyen_van"] + " " + "x" * (300 - len(THAT["nguyen_van"]) - 1)
    goc = ket_qua_de_xuat_muc(MUC_1, tra_loi_muc_1(**{
        "1.D1": tl("thoa", {"so_hieu": "Điều 10", "nguyen_van": cat}, BIA, {"so_hieu": "Điều 10", "nguyen_van": ""}),
        "1.V2": tl("thoa", gia_tri_dieu_kien=3e9),
    }), VAN_BAN)

    assert ket_qua_de_xuat_muc(MUC_1, tra_loi_da_luu(goc), VAN_BAN) == goc
