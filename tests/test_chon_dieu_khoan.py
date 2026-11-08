from pathlib import Path

from thamdinh.checklist import load_checklist
from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.tham_dinh import uoc_tinh_token
from thamdinh.truy_xuat import ChuDeVanBan, cau_truy_van, chon_dieu_khoan, do_phu_ngu_canh

CHECKLIST = load_checklist(Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml")
MUC = {m.so: m for m in CHECKLIST.muc}  # Mục 7: phat-vi-pham, boi-thuong; Mục 4: du-lieu-ca-nhan, bao-mat-thong-tin


def dk(ma, so_hieu, noi_dung, cha=None, loai="khoan"):
    return DieuKhoan(ma, so_hieu, loai, None, cha, 1, 1, noi_dung)


VAN_BAN = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        dk(0, "Phần mở đầu", "BÊN A: TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM", loai="mo_dau"),
        dk(1, "Điều 4", "ĐIỀU 4: GIÁ TRỊ VÀ THANH TOÁN\nNội dung chung của Điều 4 không được đưa vào.", loai="dieu"),
        dk(2, "4.1", "Thanh toán trong vòng 30 ngày.", cha=1),
        dk(3, "Điều 10", "ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG\nCác bên thống nhất như sau.", loai="dieu"),
        dk(4, "10.1", "Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm.", cha=3),
        dk(5, "10.1.1", "Phạt chậm tiến độ 0,1% mỗi ngày.", cha=4),
        dk(6, "10.2", "Bên vi phạm bồi thường toàn bộ thiệt hại thực tế.", cha=3),
        dk(7, "Phụ lục 03", "PHỤ LỤC 03: BẢO VỆ DỮ LIỆU CÁ NHÂN", loai="phu_luc"),
        dk(8, "Phụ lục 03, 1.1", "Bên B xử lý dữ liệu cá nhân theo Nghị định 13.", cha=7),
        dk(9, "Phụ lục 03, 1.2", "Bên B thông báo vi phạm dữ liệu trong 72 giờ.", cha=7),
        dk(10, "11.1", "Bất khả kháng là sự kiện xảy ra khách quan.", loai="khoan"),
        dk(11, "12.1", "Bên A được đơn phương chấm dứt hợp đồng.", loai="khoan"),
    ],
    canh_bao=[],
)
CHU_DE = ChuDeVanBan("k", {d.ma: () for d in VAN_BAN.dieu_khoan} | {
    4: ("phat-vi-pham",), 6: ("boi-thuong",), 7: ("du-lieu-ca-nhan",), 2: ("thanh-toan",)}, ())


class TimGia:
    """Bộ tìm kiếm giả: trả mọi Điều khoản theo thứ tự cho trước."""

    def __init__(self, thu_tu):
        self.thu_tu = thu_tu
        self.cau_hoi = []

    def tim(self, cau_truy_van):
        self.cau_hoi.append(cau_truy_van)
        return self.thu_tu + [d.ma for d in VAN_BAN.dieu_khoan if d.ma not in self.thu_tu]


def chon(so, tim_kiem=(), ngan_sach=16000, chu_de=CHU_DE):
    return chon_dieu_khoan(MUC[so], VAN_BAN, chu_de, list(tim_kiem), ngan_sach)


def test_lay_dieu_khoan_mang_chu_de_cua_muc_kem_con_chau():
    nc = chon(7)

    assert nc.dieu_khoan == ("10.1", "10.1.1", "10.2")
    assert "Phạt chậm tiến độ 0,1% mỗi ngày." in nc.van_ban


def test_dieu_khoan_cha_chi_dua_dong_tieu_de_va_giu_thu_tu_hop_dong():
    nc = chon(7)

    assert nc.van_ban.startswith("### Điều 10\nĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG\n\n### 10.1\n")
    assert "Các bên thống nhất như sau." not in nc.van_ban
    assert nc.van_ban.index("### 10.1.1") < nc.van_ban.index("### 10.2")


def test_chon_dieu_khoan_cha_thi_lay_ca_phu_luc():
    nc = chon(4)

    assert nc.dieu_khoan == ("Phụ lục 03", "Phụ lục 03, 1.1", "Phụ lục 03, 1.2")


def test_luoi_an_toan_lay_top_5_moi_bo_tim_kiem_bo_dieu_khoan_da_co():
    bm25 = TimGia([4, 10, 11, 0, 8, 9, 2])  # 4 đã có theo Chủ đề nên không tính vào top-5
    nhung = TimGia([2, 1, 10, 11, 0])  # trùng với BM25 thì gộp

    nc = chon(7, [bm25, nhung])

    assert set(nc.dieu_khoan) == {"10.1", "10.1.1", "10.2", "11.1", "12.1", "Phần mở đầu",
                                  "Phụ lục 03, 1.1", "Phụ lục 03, 1.2", "Điều 4", "4.1"}
    assert bm25.cau_hoi == [cau_truy_van(MUC[7])]


def test_cau_truy_van_gom_cau_hoi_va_mo_ta_tieu_chi():
    q = cau_truy_van(MUC[7])

    assert MUC[7].cau_hoi in q
    assert all(tc.mo_ta in q for ds in MUC[7].tieu_chi.values() for tc in ds)


def test_vuot_ngan_sach_bo_nguyen_dieu_khoan_uu_tien_thap_va_ghi_canh_bao():
    tim = TimGia([11, 10])
    du = chon(7, [tim])
    ngan_sach = uoc_tinh_token(du.van_ban) - 5  # thiếu một chút: phải bỏ Điều khoản cuối của lưới an toàn

    nc = chon(7, [tim], ngan_sach=ngan_sach)

    assert nc.so_token <= ngan_sach
    assert "10.1" in nc.dieu_khoan and "12.1" in nc.dieu_khoan  # theo Chủ đề và lưới an toàn hạng cao vẫn giữ
    assert nc.bo_qua and nc.bo_qua[-1] not in nc.dieu_khoan
    assert any("ngân sách" in c for c in nc.canh_bao)
    for so_hieu in nc.dieu_khoan:  # không cắt giữa Điều khoản
        d = next(d for d in VAN_BAN.dieu_khoan if d.so_hieu == so_hieu)
        assert f"### {so_hieu}\n{d.noi_dung}" in nc.van_ban


def test_dieu_khoan_theo_chu_de_uu_tien_hon_luoi_an_toan():
    vua_chu_de = uoc_tinh_token(chon(7).van_ban)

    nc = chon(7, [TimGia([10, 11])], ngan_sach=vua_chu_de)

    assert "10.1" in nc.dieu_khoan
    assert "11.1" not in nc.dieu_khoan and "11.1" in nc.bo_qua


def test_trong_nhom_chu_de_diem_lien_quan_cao_duoc_giu_truoc():
    chu_de = ChuDeVanBan("k", {**CHU_DE.chu_de, 10: ("phat-vi-pham",)}, ())
    tim = TimGia([10, 4])  # 11.1 liên quan hơn 10.1 theo bộ tìm kiếm

    nc = chon(7, [tim], ngan_sach=40, chu_de=chu_de)

    assert "11.1" in nc.dieu_khoan and "10.1" in nc.bo_qua


def test_canh_bao_khi_khong_dieu_khoan_nao_mang_chu_de_cua_muc():
    nc = chon(5)  # bao-mat-thong-tin: không Điều khoản nào được gắn

    assert nc.dieu_khoan == ()
    assert any("Chủ đề" in c for c in nc.canh_bao)


PHU_LUC_LON = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        dk(0, "Phụ lục 02", "PHỤ LỤC 02: YÊU CẦU KỸ THUẬT", loai="phu_luc"),
        dk(1, "Phụ lục 02, Mục A", "Bảng tiêu chí kỹ thuật. " * 40, cha=0, loai="muc_phu_luc"),  # lớn
        dk(2, "Phụ lục 02, Mục B", "Phạm vi dịch vụ triển khai.", cha=0, loai="muc_phu_luc"),
        dk(3, "Phụ lục 02, Mục C", "Phạm vi dịch vụ vận hành.", cha=0, loai="muc_phu_luc"),
        dk(4, "1.1", "Đối tượng hợp đồng là dịch vụ thuê phần mềm.", loai="khoan"),
    ],
    canh_bao=[],
)
MUC_2 = MUC[2]  # doi-tuong-pham-vi


def dem_tu(van_ban):
    """Bộ đếm token giả: mỗi từ một token (thay cho /tokenize của llama-server)."""
    return len(van_ban.split())


def chon_lon(chu_de, ngan_sach, tim_kiem=()):
    return chon_dieu_khoan(MUC_2, PHU_LUC_LON, ChuDeVanBan("k", chu_de, ()), list(tim_kiem), ngan_sach, dem=dem_tu)


def test_cay_khong_vua_ngan_sach_thi_lay_tung_dieu_khoan_con():
    # Mục 2 TOSS từng bỏ trọn Phụ lục 02 chỉ vì cả cây không vừa
    nc = chon_lon({0: ("doi-tuong-pham-vi",), 1: (), 2: (), 3: (), 4: ()}, ngan_sach=40)

    assert {"Phụ lục 02, Mục B", "Phụ lục 02, Mục C"} <= set(nc.dieu_khoan)
    assert nc.bo_qua == ("Phụ lục 02, Mục A",)
    assert nc.so_token == dem_tu(nc.van_ban) <= 40


def test_dieu_khoan_lon_hon_nua_ngan_sach_xep_sau_cung_trong_nhom_chu_de():
    # Mục 3 TOSS: bảng kỹ thuật được gắn nhiều Chủ đề, chiếm chỗ của các khoản liên quan trực tiếp
    chu_de = {0: (), 1: ("doi-tuong-pham-vi",), 2: (), 3: (), 4: ("doi-tuong-pham-vi",)}
    # Bảng (khoảng 213 token) vừa ngân sách khi đứng một mình nhưng không vừa cùng 1.1; bảng được xếp hạng cao hơn
    nc = chon_lon(chu_de, ngan_sach=220, tim_kiem=[TimGiaLon([1, 4])])

    assert "1.1" in nc.dieu_khoan
    assert nc.bo_qua == ("Phụ lục 02, Mục A",)


def test_dung_bo_dem_token_duoc_truyen_vao():
    nc = chon_lon({0: ("doi-tuong-pham-vi",), 1: (), 2: (), 3: (), 4: ()}, ngan_sach=1000)

    assert nc.so_token == dem_tu(nc.van_ban)


class TimGiaLon:
    def __init__(self, thu_tu):
        self.thu_tu = thu_tu

    def tim(self, cau_truy_van):
        return self.thu_tu + [d.ma for d in PHU_LUC_LON.dieu_khoan if d.ma not in self.thu_tu]


def test_do_phu_trich_dan_chuan_trong_ngu_canh():
    trich_dan_chuan = {
        "7.D1": ("Mức phạt không vượt quá 8% … bị vi phạm",),  # có trong ngữ cảnh Mục 7, có "…"
        "7.D2": ("Bên A được đơn phương chấm dứt hợp đồng.",),  # có trong Hợp đồng nhưng ngữ cảnh không có
        "7.L1": ("Câu không có trong Hợp đồng.",),  # bộ chuẩn chép sai: không tính vào độ phủ
        "7.V1": ("ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG",),  # dòng tiêu đề của Điều khoản cha: model vẫn đọc được
        "4.D1": ("Bên B xử lý dữ liệu cá nhân theo Nghị định 13.",),  # Mục khác
    }

    kq = do_phu_ngu_canh(trich_dan_chuan, CHECKLIST, VAN_BAN, lambda m: chon_dieu_khoan(m, VAN_BAN, CHU_DE, [], 16000))

    theo_ma = {d.ma: d.trang_thai for d in kq}
    assert theo_ma == {"7.D1": "co", "7.D2": "thieu", "7.L1": "khong_co_trong_van_ban", "7.V1": "co", "4.D1": "co"}
    assert {d.ma: d.so_muc for d in kq}["4.D1"] == 4
