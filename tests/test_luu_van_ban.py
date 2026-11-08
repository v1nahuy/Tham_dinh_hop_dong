from dataclasses import replace
from pathlib import Path

from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc, hash_pdf, so_hoa
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.so_hoa.van_ban import duong_dan_pdf, hash_noi_dung, luu_van_ban, nap_van_ban

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))

MAU = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ mẫu.pdf",
    trang=[TrangSoHoa(1, "lop_text", True, ("có redline (1 đoạn đã gắn nhãn)",))],
    dieu_khoan=[
        DieuKhoan(0, "Điều 1", "dieu", "ĐỐI TƯỢNG", None, 1, 1, "ĐIỀU 1: ĐỐI TƯỢNG", ((1, 70.0, 700.0, 400.0, 712.0),)),
        DieuKhoan(1, "1.1", "khoan", None, 0, 1, 2, "1.1. Giá [thêm: 294.000.000] [xóa: 1.918.900.000]"),
    ],
    canh_bao=["Số hiệu '4.1' xuất hiện nhiều lần (2 lần, trang 3)"],
)


def test_luu_roi_nap_lai_nguyen_ven(tmp_path):
    luu_van_ban(MAU, tmp_path)

    assert nap_van_ban("abc123", tmp_path) == MAU


def test_chua_luu_thi_khong_co(tmp_path):
    assert nap_van_ban("khong-co", tmp_path) is None


def test_so_hoa_dung_lai_ban_da_luu_ke_ca_ban_sua_tay(tmp_path):
    da_sua = replace(MAU, hash_pdf=hash_pdf(TOSS), dieu_khoan=[replace(MAU.dieu_khoan[0], noi_dung="đã sửa tay")])
    luu_van_ban(da_sua, tmp_path)

    assert so_hoa(TOSS, thu_muc_luu=tmp_path) == da_sua


def test_so_hoa_lan_dau_luu_lai_theo_hash(tmp_path):
    van_ban = so_hoa(TOSS, thu_muc_luu=tmp_path)

    assert nap_van_ban(hash_pdf(TOSS), tmp_path) == van_ban


def test_ban_sua_tay_khong_xoa_ban_cu_nap_lai_theo_hash_noi_dung(tmp_path):
    # Lượt chạy trước khi sửa tay phải mở lại được đúng văn bản lúc chạy
    luu_van_ban(MAU, tmp_path)
    da_sua = replace(MAU, dieu_khoan=[replace(MAU.dieu_khoan[0], noi_dung="đã sửa tay")])
    luu_van_ban(da_sua, tmp_path)

    assert nap_van_ban("abc123", tmp_path) == da_sua  # bản mới nhất
    assert nap_van_ban("abc123", tmp_path, hash_noi_dung(MAU)) == MAU
    assert nap_van_ban("abc123", tmp_path, hash_noi_dung(da_sua)) == da_sua
    assert hash_noi_dung(MAU) != hash_noi_dung(da_sua)


def test_hash_noi_dung_on_dinh_va_khong_phu_thuoc_ten_file():
    assert hash_noi_dung(MAU) == hash_noi_dung(replace(MAU))
    assert hash_noi_dung(MAU) == hash_noi_dung(replace(MAU, ten_file="đổi tên.pdf"))


def test_so_hoa_chep_file_pdf_vao_thu_muc_du_lieu(tmp_path):
    so_hoa(TOSS, thu_muc_luu=tmp_path)

    ban_chep = tmp_path / "pdf" / f"{hash_pdf(TOSS)}.pdf"
    assert ban_chep.read_bytes() == TOSS.read_bytes()
    assert duong_dan_pdf(hash_pdf(TOSS), tmp_path) == ban_chep
