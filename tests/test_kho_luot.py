import sqlite3

import pytest
from test_tham_dinh import CHECKLIST, THAT, VAN_BAN, ModelGia, TruyXuatGia

from thamdinh.kho_luot import GhiDeError, KhoLuot
from thamdinh.tham_dinh import tham_dinh
from thamdinh.trich_dan import TrichDan


@pytest.fixture
def kho(tmp_path):
    return KhoLuot(tmp_path)


def muc(kq, so):
    return next(m for m in kq.muc if m.so == so)


def test_luu_roi_doc_lai_mot_luot_day_du(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}), model="qwen3.5")  # có cả Mục chưa đánh giá được

    kho.luu(kq)

    assert kho.nap(kq.ma) == kq


def test_luu_roi_doc_lai_luot_che_do_truy_xuat(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), truy_xuat=TruyXuatGia())

    kho.luu(kq)

    assert kho.nap(kq.ma) == kq


def test_luu_sau_moi_muc_roi_chay_lai_phan_loi_tren_cung_luot(kho):
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}), sau_moi_buoc=kho.luu)

    sau = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), luot_truoc=kho.nap(truoc.ma), sau_moi_buoc=kho.luu)

    assert sau.ma == truoc.ma
    assert kho.nap(truoc.ma) == sau and muc(sau, 7).ket_qua is not None
    assert [t.ma for t in kho.danh_sach()] == [truoc.ma]


def test_khong_ghi_de_ket_qua_de_xuat_da_co(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)
    sua = kq.__class__(**{**kq.__dict__, "muc": tuple(
        m.__class__(**{**m.__dict__, "cau_hoi": "đã sửa"}) if m.so == 3 else m for m in kq.muc)})

    with pytest.raises(GhiDeError, match="Mục 3"):
        kho.luu(sua)
    assert kho.nap(kq.ma) == kq


def test_co_so_du_lieu_tu_chan_sua_ket_qua_de_xuat(kho, tmp_path):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)

    with sqlite3.connect(kho.duong_dan) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE muc_de_xuat SET du_lieu = '{}' WHERE so = 3")
    with sqlite3.connect(kho.duong_dan) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM muc_de_xuat WHERE so = 3")


def test_chay_lai_muc_da_co_ket_qua_luu_thanh_luot_moi_giu_luot_cu(kho):
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), sau_moi_buoc=kho.luu)
    model = ModelGia(sua_muc={3: {"3.D1": {"danh_gia": "khong_thoa", "ly_do": "chạy lại", "trich_dan": [THAT]}}})

    moi = tham_dinh(VAN_BAN, CHECKLIST, model, luot_truoc=kho.nap(truoc.ma), chay_lai={3}, sau_moi_buoc=kho.luu)

    assert kho.nap(truoc.ma) == truoc
    assert kho.nap(moi.ma) == moi
    tom_tat = {t.ma: t for t in kho.danh_sach()}
    assert tom_tat[moi.ma].luot_goc == truoc.ma


def test_danh_sach_luot_moi_nhat_truoc_kem_tien_do(kho):
    a = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}), model="qwen3.5")
    b = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), truy_xuat=TruyXuatGia())
    kho.luu(a)
    kho.luu(b)
    kho.luu_duyet(a.ma, 1, "luu_y", "Người ký chưa rõ ủy quyền.", [], "Huy", VAN_BAN)

    ds = kho.danh_sach()

    assert [t.ma for t in ds] == [b.ma, a.ma]
    assert (ds[1].ten_file, ds[1].che_do, ds[1].model) == ("HĐ TOSS.pdf", "toan_van", "qwen3.5")
    assert (ds[1].so_muc, ds[1].so_muc_xong, ds[1].so_muc_da_duyet) == (17, 16, 1)
    assert ds[0].che_do == "truy_xuat"


def test_duyet_chi_them_co_lich_su_va_khong_doi_ket_qua_de_xuat(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)

    kho.luu_duyet(kq.ma, 7, "luu_y", "Lần 1", [], "Huy", VAN_BAN)
    lan_2 = kho.luu_duyet(kq.ma, 7, "vi_pham", "Lần 2", [TrichDan("Điều 10", THAT["nguyen_van"])], "Lan", VAN_BAN)

    assert kho.nap_duyet(kq.ma) == {7: lan_2}
    lich_su = kho.lich_su_duyet(kq.ma, 7)
    assert [(d.phien_ban, d.ket_qua, d.nguoi_duyet) for d in lich_su] == [(1, "luu_y", "Huy"), (2, "vi_pham", "Lan")]
    assert kho.nap(kq.ma) == kq  # Kết quả đề xuất vẫn nguyên


def test_trich_dan_da_sua_duoc_kiem_tra_lai(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)

    d = kho.luu_duyet(kq.ma, 7, "vi_pham", "…", [
        TrichDan("Điều 10", THAT["nguyen_van"]), TrichDan("Điều 10", "Bên A được miễn trừ mọi trách nhiệm")], "Huy", VAN_BAN)

    assert [t.trang_thai for t in d.trich_dan] == ["khop", "khong_xac_minh_duoc"]


def test_co_so_du_lieu_tu_chan_sua_ket_qua_da_duyet(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)
    kho.luu_duyet(kq.ma, 7, "luu_y", "…", [], "Huy", VAN_BAN)

    with sqlite3.connect(kho.duong_dan) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE duyet SET du_lieu = '{}'")


@pytest.mark.parametrize(
    "so_muc, ket_qua, nguoi, thong_bao",
    [
        (7, "tot", "Huy", "ket_qua"),
        (99, "dat", "Huy", "Mục 99"),
        (7, "dat", " ", "người duyệt"),
    ],
)
def test_duyet_sai_thi_bao_loi(kho, so_muc, ket_qua, nguoi, thong_bao):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)

    with pytest.raises(ValueError, match=thong_bao):
        kho.luu_duyet(kq.ma, so_muc, ket_qua, "…", [], nguoi, VAN_BAN)


def test_duyet_voi_van_ban_khac_ban_luot_da_dung_thi_bao_loi(kho):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    kho.luu(kq)
    da_sua = VAN_BAN.__class__(**{**VAN_BAN.__dict__, "canh_bao": ["đã sửa tay"]})

    with pytest.raises(ValueError, match="Văn bản hiệu lực"):
        kho.luu_duyet(kq.ma, 7, "dat", "…", [], "Huy", da_sua)


def test_luot_khong_ton_tai(kho):
    with pytest.raises(KeyError):
        kho.nap("khong-co")
