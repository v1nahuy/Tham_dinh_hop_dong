"""Chấm lại các Lượt đã lưu bằng code hiện tại, không gọi model (issue 25)."""

import json
from dataclasses import replace

from test_so_sanh import chuan
from test_tham_dinh import BIA, CHECKLIST, THAT, VAN_BAN, ModelGia

from thamdinh.cham_lai import ChamKho, ChamLuot, cham_lai, den_json, so_cham, tu_json
from thamdinh.kho_luot import KhoLuot
from thamdinh.so_hoa.van_ban import luu_van_ban
from thamdinh.trich_dan import TrichDanDaKiemTra
from thamdinh.tham_dinh import tham_dinh


def luu_luot(tmp_path, ma="luot-1", sua_muc=None, sua_tieu_chi=None, loi_muc=None, **sua_luot):
    """Chạy model giả, sửa Tiêu chí đã lưu như code cũ để lại, rồi lưu vào kho tạm."""
    luu_van_ban(VAN_BAN, tmp_path)
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(sua_muc=sua_muc, loi_muc=loi_muc), model="qwen3.5")
    kq = replace(kq, ma=ma, **sua_luot)
    sua_tieu_chi = sua_tieu_chi or {}
    kq = replace(kq, muc=tuple(
        replace(m, tieu_chi=tuple(replace(t, **sua_tieu_chi.get(t.ma, {})) for t in m.tieu_chi)) for m in kq.muc
    ))
    kho = KhoLuot(tmp_path)
    kho.luu(kq)
    return kho


def test_tong_hop_lai_danh_gia_theo_luat_hien_tai(tmp_path):
    # 7.D1 định lượng, Hợp đồng không nêu giá trị: luật hiện tại (issue 20) là không thỏa; code cũ đã lưu không rõ
    kho = luu_luot(
        tmp_path,
        sua_muc={7: {"7.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [THAT], "gia_tri": None}}},
        sua_tieu_chi={"7.D1": {"danh_gia": "khong_ro"}},
    )

    kq = cham_lai(kho, CHECKLIST, tmp_path)

    assert kq.loi == {}
    assert kq.luot["luot-1"].danh_gia["7.D1"] == "khong_thoa"
    assert kq.luot["luot-1"].ket_qua_muc[7] == "luu_y"


def test_kiem_lai_trich_dan_voi_van_ban_luot_da_dung(tmp_path):
    # Trạng thái đã lưu do code cũ để lại, ngược với Văn bản hiệu lực
    kho = luu_luot(tmp_path, sua_tieu_chi={"1.D1": {"trich_dan": (
        TrichDanDaKiemTra(THAT["so_hieu"], THAT["nguyen_van"], "khong_xac_minh_duoc", None),
        TrichDanDaKiemTra(BIA["so_hieu"], BIA["nguyen_van"], "khop", None),
    )}})

    kq = cham_lai(kho, CHECKLIST, tmp_path)

    assert kq.luot["luot-1"].trich_dan["1.D1"] == ("khop", "khong_xac_minh_duoc")


class KhoCoLuotHong(KhoLuot):
    """Như kho thật, nhưng một Lượt lưu bằng code đã revert nên không nạp được (issue 19)."""

    def nap(self, ma):
        if ma == "luot-hong":
            raise TypeError("DanhGiaDeXuat.__init__() got an unexpected keyword argument 'cau_hoi'")
        return super().nap(ma)


def test_luot_khong_nap_duoc_ghi_vao_loi_va_cham_tiep(tmp_path):
    luu_luot(tmp_path, ma="luot-hong")
    luu_luot(tmp_path, ma="luot-tot")

    kq = cham_lai(KhoCoLuotHong(tmp_path), CHECKLIST, tmp_path)

    assert list(kq.luot) == ["luot-tot"]
    assert "cau_hoi" in kq.loi["luot-hong"]


def test_luot_cua_phien_ban_checklist_khac_ghi_vao_loi(tmp_path):
    luu_luot(tmp_path, ma="luot-khac", checklist="dau-ra 9.9")
    kho = luu_luot(tmp_path, ma="luot-tot")

    kq = cham_lai(kho, CHECKLIST, tmp_path)

    assert list(kq.luot) == ["luot-tot"]
    assert "dau-ra 9.9" in kq.loi["luot-khac"]


def test_ghi_hash_pdf_va_danh_dau_luot_thieu_van_ban(tmp_path):
    luu_luot(tmp_path, ma="co-van-ban")
    kho = luu_luot(tmp_path, ma="thieu-van-ban", hash_pdf="hd-khac")  # không có Văn bản hiệu lực của PDF này

    kq = cham_lai(kho, CHECKLIST, tmp_path)

    assert (kq.luot["co-van-ban"].hash_pdf, kq.luot["thieu-van-ban"].hash_pdf) == ("abc123", "hd-khac")
    assert kq.luot["co-van-ban"].trich_dan["1.D1"] == ("khop",)
    assert kq.luot["thieu-van-ban"].trich_dan is None
    assert kq.luot["thieu-van-ban"].danh_gia == kq.luot["co-van-ban"].danh_gia  # vẫn tổng hợp lại được


def test_muc_chua_danh_gia_duoc_khong_co_ket_qua_va_danh_gia(tmp_path):
    kho = luu_luot(tmp_path, loi_muc={3: 2})  # model trả JSON sai hai lần: Mục 3 chưa đánh giá được

    kq = cham_lai(kho, CHECKLIST, tmp_path).luot["luot-1"]

    assert kq.ket_qua_muc[3] is None
    assert not [ma for ma in kq.danh_gia if ma.startswith("3.")]
    assert kq.ket_qua_muc[4] is not None


def test_so_cham_dem_chuyen_trang_thai_so_voi_bo_chuan():
    truoc = ChamKho({"l": ChamLuot({"1.D1": "thoa", "1.D2": "khong_thoa", "1.V1": "thoa"}, {1: "vi_pham"},
                                   {"1.D1": ("khop", "khong_xac_minh_duoc")})}, {})
    sau = ChamKho({"l": ChamLuot({"1.D1": "thoa", "1.D2": "thoa", "1.V1": "khong_thoa"}, {1: "dat"},
                                 {"1.D1": ("khop", "khop")})}, {})
    bc = chuan({"1.D1": "thoa", "1.D2": "thoa", "1.V1": "thoa"}, ket_qua={1: "dat"})

    kq = so_cham(truoc, sau, bc)

    l = kq.luot["l"]
    assert (l.dung_truoc, l.dung_sau) == (2, 2)
    assert (l.sai_thanh_dung, l.dung_thanh_sai) == (("1.D2",), ("1.V1",))
    assert l.muc_doi == ((1, "vi_pham", "dat"),)
    assert (l.muc_dung_truoc, l.muc_dung_sau) == (0, 1)
    assert kq.trich_dan == {("khop", "khop"): 1, ("khong_xac_minh_duoc", "khop"): 1}


def test_ket_qua_cham_qua_json_van_nhu_cu(tmp_path):
    # Lần chấm bằng code cũ chạy trong worktree khác, gửi kết quả về qua JSON
    luu_luot(tmp_path, ma="luot-tot")
    luu_luot(tmp_path, ma="luot-hong")
    luu_luot(tmp_path, ma="thieu-van-ban", hash_pdf="hd-khac")
    kq = cham_lai(KhoCoLuotHong(tmp_path), CHECKLIST, tmp_path)

    assert tu_json(json.loads(json.dumps(den_json(kq)))) == kq


def test_so_cham_bo_qua_trich_dan_cua_luot_thieu_van_ban_nhung_van_dem_tieu_chi():
    truoc = ChamKho({"l": ChamLuot({"1.D1": "khong_thoa"}, {1: "luu_y"}, None)}, {})
    sau = ChamKho({"l": ChamLuot({"1.D1": "thoa"}, {1: "dat"}, None)}, {})

    kq = so_cham(truoc, sau, chuan({"1.D1": "thoa"}, ket_qua={1: "dat"}))

    assert kq.luot["l"].sai_thanh_dung == ("1.D1",)
    assert kq.trich_dan == {}
