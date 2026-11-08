"""Xử lý ảnh trang trước khi OCR: cắt khung comment, chỉnh nghiêng, phát hiện redline, ghép dòng (ảnh tổng hợp)."""

import pytest
from PIL import Image, ImageDraw, ImageFont

from thamdinh.so_hoa.anh import cat_khung_comment, chinh_nghieng, ghep_dong, tim_redline

TRANG = (1000, 1400)
XAM = (235, 235, 235)


def ve_dong_chu(ve: ImageDraw.ImageDraw, x0: int, x1: int, y: int, mau=(0, 0, 0)) -> None:
    """Một "dòng chữ" giả: các khối đặc rộng 12–30 px, cao 22 px, cách nhau như chữ và khoảng trắng."""
    x = x0
    while x < x1:
        rong = 12 + (x * 7) % 19
        ve.rectangle((x, y, min(x + rong, x1), y + 22), fill=mau)
        x += rong + (14 if (x // 37) % 4 == 0 else 4)


def trang_co_comment() -> Image.Image:
    anh = Image.new("RGB", TRANG, "white")
    ve = ImageDraw.Draw(anh)
    for y in range(100, 1300, 50):
        ve_dong_chu(ve, 80, 640, y)
    ve.rectangle((680, 0, TRANG[0], TRANG[1]), fill=XAM)
    ve.rectangle((700, 280, 980, 400), fill="white", outline=(230, 140, 30), width=3)
    ve_dong_chu(ve, 710, 960, 300)
    ve.line((640, 310, 700, 310), fill=(230, 140, 30), width=2)  # đường nối từ chữ sang ô comment
    return anh


def test_cat_dai_xam_ben_phai_trang():
    anh, co_khung = cat_khung_comment(trang_co_comment())
    assert co_khung
    assert 675 <= anh.width <= 680
    assert anh.height == TRANG[1]


def test_dai_xam_cach_mep_phai_mot_le_trang_hep():
    # Trang khổ ngang / Letter của TOSS: dải xám không chạm mép phải, không chạy hết chiều cao
    anh = Image.new("RGB", TRANG, "white")
    ve = ImageDraw.Draw(anh)
    for y in range(150, 1200, 50):
        ve_dong_chu(ve, 80, 640, y)
    ve.rectangle((680, 100, TRANG[0] - 15, 1300), fill=(242, 242, 242))
    ve.rectangle((700, 280, 960, 400), fill="white", outline=(230, 140, 30), width=3)
    ve_dong_chu(ve, 710, 940, 300)
    ra, co_khung = cat_khung_comment(anh)
    assert co_khung
    assert 675 <= ra.width <= 680


def test_trang_scan_nghieng_da_chinh_van_cat_duoc_khung():
    # Xoay rồi chỉnh lại: hai góc bên phải thành nêm trắng rộng vài phần trăm bề ngang
    nghieng = trang_co_comment().rotate(-3, resample=Image.Resampling.BICUBIC, fillcolor="white")
    da_chinh, _ = chinh_nghieng(nghieng)
    ra, co_khung = cat_khung_comment(da_chinh)
    assert co_khung
    assert 665 <= ra.width <= 690


def test_ban_scan_co_nhieu_va_nen_jpeg_van_cat_duoc_khung():
    # Nhiễu + JPEG làm nền trắng tối đi (khoảng 248), dễ nhầm với dải xám (242)
    import io

    import numpy as np

    x = np.asarray(trang_co_comment()).astype(np.float32)
    x += np.random.default_rng(1).normal(0, 12, x.shape)
    jpeg = io.BytesIO()
    Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).save(jpeg, "JPEG", quality=75)
    ra, co_khung = cat_khung_comment(Image.open(jpeg))
    assert co_khung
    assert 670 <= ra.width <= 685


def test_bang_lan_sang_dai_xam_khong_bi_cat():
    # Trang 51 của TOSS: cột cuối của bảng tràn vào vùng nền xám của khung comment
    anh = trang_co_comment()
    ve = ImageDraw.Draw(anh)
    ve.rectangle((80, 300, 770, 1150), fill="white", outline="black", width=2)  # bảng cao hơn nửa trang
    ve.line((690, 300, 690, 1150), fill="black", width=2)
    ve_dong_chu(ve, 700, 760, 700)
    ra, co_khung = cat_khung_comment(anh)
    assert co_khung
    assert 771 <= ra.width <= 790


def test_vet_xam_manh_sat_mep_khong_phai_khung():
    # Trang 47 bản scan nghiêng: vệt xám vài điểm sát mép phải, rồi lề trắng, rồi mới đến dải xám thật
    anh = trang_co_comment()
    ve = ImageDraw.Draw(anh)
    ve.rectangle((TRANG[0] - 30, 0, TRANG[0], TRANG[1]), fill="white")
    ve.rectangle((TRANG[0] - 6, 0, TRANG[0], TRANG[1]), fill=XAM)
    ra, co_khung = cat_khung_comment(anh)
    assert co_khung
    assert 675 <= ra.width <= 682


def test_trang_khong_co_comment_giu_nguyen():
    anh = Image.new("RGB", TRANG, "white")
    ve = ImageDraw.Draw(anh)
    for y in range(100, 1300, 50):
        ve_dong_chu(ve, 80, 900, y)
    ra, co_khung = cat_khung_comment(anh)
    assert not co_khung
    assert ra.size == TRANG


def test_o_bang_to_nen_xam_khong_bi_cat():
    anh = Image.new("RGB", TRANG, "white")
    ve = ImageDraw.Draw(anh)
    ve.rectangle((100, 200, TRANG[0], 500), fill=XAM)  # ô bảng tô nền, chạm lề phải nhưng không cao hết trang
    ve_dong_chu(ve, 120, 900, 300)
    ra, co_khung = cat_khung_comment(anh)
    assert not co_khung
    assert ra.size == TRANG


def trang_chu() -> Image.Image:
    anh = Image.new("RGB", TRANG, "white")
    ve = ImageDraw.Draw(anh)
    for y in range(100, 1300, 45):
        ve_dong_chu(ve, 80, 920, y)
    return anh


@pytest.mark.parametrize("goc", [2.0, -2.0, 0.7])
def test_chinh_nghieng_trang_bi_xoay(goc):
    nghieng = trang_chu().rotate(goc, expand=False, fillcolor="white")
    da_chinh, goc_tim_thay = chinh_nghieng(nghieng)
    assert goc_tim_thay == pytest.approx(goc, abs=0.3)
    _, con_lai = chinh_nghieng(da_chinh)
    assert con_lai == pytest.approx(0, abs=0.3)


def test_trang_thang_giu_nguyen():
    anh = trang_chu()
    da_chinh, goc = chinh_nghieng(anh)
    assert goc == 0
    assert da_chinh is anh


def test_ghep_so_hieu_khoan_va_noi_dung_cung_dong():
    so_hieu = (160, 1002, 290, 1050)
    noi_dung = (330, 998, 1640, 1054)  # hộp cao hơn một chút vì có dấu tiếng Việt
    dong_sau = (330, 1060, 1500, 1112)  # dòng kế tiếp, hai hộp chồng nhau vài pixel
    assert ghep_dong([dong_sau, noi_dung, so_hieu]) == [[so_hieu, noi_dung], [dong_sau]]


def test_ghep_dong_theo_thu_tu_tren_xuong_trai_sang_phai():
    hop = [(900, 400, 1200, 440), (100, 100, 400, 140), (500, 402, 850, 438), (100, 400, 450, 441), (450, 98, 800, 142)]
    assert ghep_dong(hop) == [
        [(100, 100, 400, 140), (450, 98, 800, 142)],
        [(100, 400, 450, 441), (500, 402, 850, 438), (900, 400, 1200, 440)],
    ]


def test_khong_co_hop_chu():
    assert ghep_dong([]) == []


# ---- Redline: ảnh một hộp chữ ở 300 dpi (chữ 13pt cao khoảng 54 px) ----
try:
    FONT = ImageFont.truetype("times.ttf", 54)  # font của TOSS, có sẵn trên Windows
except OSError:
    FONT = ImageFont.load_default(size=54)
DEN, CAM, XANH, XANH_NGOC, XAM_CHU = (0, 0, 0), (225, 140, 35), (20, 60, 220), (20, 145, 160), (85, 85, 85)


def ve_hop_chu(*doan, nen="white", to_nen=None):
    """doan: (chữ, màu, nét) với nét None | "ngang" | "chan". Trả về ảnh và khoảng x của từng đoạn."""
    rong = 20 + sum(int(FONT.getlength(c)) for c, _, _ in doan)
    anh = Image.new("RGB", (rong, 80), nen)
    ve = ImageDraw.Draw(anh)
    tren, chan = 8, 8 + FONT.getmetrics()[0]  # đỉnh và đường chân chữ
    cao_x = chan - (tren + FONT.getbbox("x")[1])
    x, khoang = 10, []
    for chu, mau, net in doan:
        x1 = x + FONT.getlength(chu)
        if to_nen:
            ve.rectangle((x, tren + 4, x1, chan + 10), fill=to_nen)
        ve.text((x, tren), chu, fill=mau, font=FONT)
        if net == "ngang":
            ve.line((x, chan - cao_x // 2, x1, chan - cao_x // 2), fill=mau, width=3)
        elif net == "chan":
            ve.line((x, chan + 5, x1, chan + 5), fill=mau, width=3)
        khoang.append((x, x1))
        x = x1
    return anh, khoang


def nhan(anh):
    return [d.nhan for d in tim_redline(anh)]


def test_chu_den_khong_co_redline():
    anh, _ = ve_hop_chu(("Hình thức bảo đảm thực hiện", DEN, None))
    assert nhan(anh) == [None]


def test_doan_redline_phu_kin_be_ngang_hop():
    anh, _ = ve_hop_chu(("Giá trị: ", DEN, None), ("1.918.900", CAM, "ngang"), (" đồng", DEN, None))
    doan = tim_redline(anh)
    assert doan[0].x0 == 0 and doan[-1].x1 == anh.width
    assert all(a.x1 == b.x0 for a, b in zip(doan, doan[1:]))


def test_chu_mau_gach_ngang_la_xoa():
    anh, khoang = ve_hop_chu(("Giá trị: ", DEN, None), ("1.918.900.000", CAM, "ngang"))
    doan = tim_redline(anh)
    assert [d.nhan for d in doan] == [None, "xóa"]
    assert khoang[1][0] - 15 <= doan[1].x0 <= khoang[1][0] + 2  # không cắt mất chữ số đầu


def test_chu_mau_gach_chan_la_them():
    anh, _ = ve_hop_chu(("dịch vụ ", DEN, None), ("triển khai", XANH, "chan"))
    assert nhan(anh) == [None, "thêm"]


def test_chu_xam_khong_gach_la_sua():
    anh, _ = ve_hop_chu(("4.5. Những nội dung thay đổi", XAM_CHU, None))
    assert nhan(anh) == ["sửa"]


def test_so_hieu_cu_gach_ngang_lien_so_hieu_moi_gach_chan():
    anh, _ = ve_hop_chu(("4.3.3.", XANH_NGOC, "ngang"), ("4.3.4.", XANH_NGOC, "chan"))
    assert nhan(anh) == ["xóa", "thêm"]


def test_ban_den_trang_chi_con_net_gach_ngang():
    anh, _ = ve_hop_chu(("trong vòng 06 ", DEN, None), ("23 tháng", DEN, "ngang"))
    assert nhan(anh) == [None, "xóa"]


def test_gach_chan_den_la_dinh_dang_thuong():
    anh, _ = ve_hop_chu(("ĐIỀU 4: ĐƠN GIÁ", DEN, "chan"))
    assert nhan(anh) == [None]


def test_nen_highlight_vang_khong_phai_redline():
    anh, _ = ve_hop_chu(("294.000.000", DEN, None), to_nen=(255, 255, 0))
    assert nhan(anh) == [None]


def test_danh_dau_dau_cach_truoc_doan():
    anh, _ = ve_hop_chu(("dịch vụ ", DEN, None), ("triển khai ", XANH, "chan"), ("của", DEN, None))
    doan = tim_redline(anh)
    assert [d.nhan for d in doan] == [None, "thêm", None]
    assert doan[1].cach_truoc  # nét gạch chân chạy qua khoảng trắng không làm mất dấu cách
    anh, _ = ve_hop_chu(("trong vòng 06", DEN, None), ("23", CAM, "ngang"))
    assert not tim_redline(anh)[1].cach_truoc


def test_gach_ngang_lan_sang_chu_ke_ben_khong_cat_doi_chu():
    anh, khoang = ve_hop_chu(("4.3.3.", XANH_NGOC, None), ("4.3.4.", XANH_NGOC, "chan"))
    ve = ImageDraw.Draw(anh)
    chan = 8 + FONT.getmetrics()[0]
    ve.line((khoang[0][0], chan - 13, khoang[1][0] + 10, chan - 13), fill=XANH_NGOC, width=3)  # lấn 10 px sang "4"
    doan = tim_redline(anh)
    assert [d.nhan for d in doan] == ["xóa", "thêm"]
    assert doan[1].x0 <= khoang[1][0] + 2


def test_duong_noi_comment_va_chu_dong_ben_canh_khong_phai_redline():
    anh, _ = ve_hop_chu(("Giá trị bảo đảm thực hiện", DEN, None))
    ve = ImageDraw.Draw(anh)
    chan = 8 + FONT.getmetrics()[0]
    for x in range(10, anh.width - 10, 12):  # đường nối nét đứt sang khung comment
        ve.line((x, chan - 2, x + 6, chan - 2), fill=(200, 30, 30), width=1)
    ve.text((120, anh.height - 12), "767.560", fill=CAM, font=FONT)  # đỉnh chữ của dòng dưới lọt vào hộp
    assert nhan(anh) == [None]


def test_vach_neo_comment_khong_phai_chu():
    anh, _ = ve_hop_chu(("294.000.000   ", DEN, None))
    ve = ImageDraw.Draw(anh)
    x, chan = anh.width - 30, 8 + FONT.getmetrics()[0]
    ve.rectangle((x, 6, x + 1, chan + 8), fill=(181, 8, 45))  # vạch dọc 2 px của dấu neo comment
    ve.polygon([(x - 5, chan + 8), (x + 6, chan + 8), (x, chan)], fill=(181, 8, 45))
    assert nhan(anh) == [None]


def test_chu_so_khong_co_net_doc_khong_bi_bo():
    anh, _ = ve_hop_chu(("06", DEN, None), ("2357", CAM, "ngang"))
    assert nhan(anh) == [None, "xóa"]
