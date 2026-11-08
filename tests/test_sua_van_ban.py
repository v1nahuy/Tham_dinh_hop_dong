"""Sửa tay nội dung Điều khoản của Văn bản hiệu lực (issue 06)."""

import os
from dataclasses import replace
from pathlib import Path

import pytest

from thamdinh.so_hoa import so_hoa
from thamdinh.so_hoa.van_ban import (
    danh_sach_van_ban,
    dieu_khoan_da_sua,
    dieu_khoan_tren_trang,
    luu_van_ban,
    nap_van_ban_goc,
    sua_dieu_khoan,
)
from test_luu_van_ban import MAU

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))


def test_sua_noi_dung_mot_dieu_khoan():
    da_sua = sua_dieu_khoan(MAU, 1, "1.1. Giá 294.000.000 đồng")

    assert da_sua.dieu_khoan[1] == replace(MAU.dieu_khoan[1], noi_dung="1.1. Giá 294.000.000 đồng")
    assert da_sua.dieu_khoan[0] == MAU.dieu_khoan[0]
    assert MAU.dieu_khoan[1].noi_dung.startswith("1.1. Giá [thêm:")  # bản cũ giữ nguyên


def test_giu_nhan_redline_hop_le():
    da_sua = sua_dieu_khoan(MAU, 1, "1.1. Giá [thêm: 294.000.000] [xóa: 1.918.900.000] [sửa: đồng]")
    assert "[xóa: 1.918.900.000]" in da_sua.dieu_khoan[1].noi_dung


def test_ngoac_vuong_thuong_trong_hop_dong_van_hop_le():
    da_sua = sua_dieu_khoan(MAU, 1, "1.1. Giá: [●] đồng")
    assert da_sua.dieu_khoan[1].noi_dung == "1.1. Giá: [●] đồng"


@pytest.mark.parametrize(
    "noi_dung, loi",
    [
        ("   ", "rỗng"),
        ("1.1. Giá [xóa: 1.918.900.000", "thiếu dấu ]"),
        ("1.1. Giá 1.918.900.000]", "thừa dấu ]"),
        ("1.1. Giá [xóa: 1 [thêm: 2]]", "lồng nhau"),
        ("1.1. Giá [chèn: 294.000.000]", "nhãn 'chèn'"),
    ],
)
def test_noi_dung_sai_bi_tu_choi(noi_dung, loi):
    with pytest.raises(ValueError, match=loi):
        sua_dieu_khoan(MAU, 1, noi_dung)


def test_dieu_khoan_khong_ton_tai():
    with pytest.raises(KeyError):
        sua_dieu_khoan(MAU, 99, "abc")


def test_sua_dieu_khoan_toss_tai_lai_van_thay_ban_da_sua(tmp_path):
    goc = so_hoa(TOSS, thu_muc_luu=tmp_path)
    khoan = next(dk for dk in goc.dieu_khoan if dk.so_hieu == "4.3.2")
    luu_van_ban(sua_dieu_khoan(goc, khoan.ma, "4.3.2. Hình thức bảo đảm: Thư bảo lãnh."), tmp_path)

    tai_lai = so_hoa(TOSS, thu_muc_luu=tmp_path)

    assert tai_lai.dieu_khoan[khoan.ma].noi_dung == "4.3.2. Hình thức bảo đảm: Thư bảo lãnh."
    assert nap_van_ban_goc(goc.hash_pdf, tmp_path) == goc  # bản số hóa gốc để biết Điều khoản nào đã sửa tay


def test_so_hoa_lai_tu_dau_bo_ban_da_sua(tmp_path):
    goc = so_hoa(TOSS, thu_muc_luu=tmp_path)
    luu_van_ban(sua_dieu_khoan(goc, 1, "đã sửa tay"), tmp_path)

    assert so_hoa(TOSS, thu_muc_luu=tmp_path, lam_lai=True) == goc
    assert so_hoa(TOSS, thu_muc_luu=tmp_path) == goc


def test_dieu_khoan_tren_trang_gom_ca_dieu_khoan_trai_qua_nhieu_trang():
    # Điều 1 nằm ở trang 1, khoản 1.1 từ trang 1 sang trang 2
    assert [dk.so_hieu for dk in dieu_khoan_tren_trang(MAU, 1)] == ["Điều 1", "1.1"]
    assert [dk.so_hieu for dk in dieu_khoan_tren_trang(MAU, 2)] == ["1.1"]
    assert dieu_khoan_tren_trang(MAU, 3) == []


def test_dieu_khoan_da_sua_so_voi_ban_goc():
    da_sua = sua_dieu_khoan(MAU, 1, "1.1. Giá 294.000.000 đồng")
    assert dieu_khoan_da_sua(da_sua, MAU) == {1}
    assert dieu_khoan_da_sua(MAU, MAU) == set()
    assert dieu_khoan_da_sua(da_sua, None) == set()  # văn bản số hóa trước khi có bản gốc


def test_danh_sach_van_ban_da_so_hoa(tmp_path):
    assert danh_sach_van_ban(tmp_path) == []
    luu_van_ban(MAU, tmp_path, ban_goc=True)
    luu_van_ban(sua_dieu_khoan(MAU, 1, "đã sửa"), tmp_path)  # thêm bản theo nội dung, vẫn là một văn bản
    khac = replace(MAU, hash_pdf="def456", ten_file="HĐ khác.pdf")
    file_khac = luu_van_ban(khac, tmp_path, ban_goc=True)
    moi_hon = (tmp_path / "van-ban-hieu-luc" / "abc123.json").stat().st_mtime + 10
    os.utime(file_khac, (moi_hon, moi_hon))  # đồng hồ file của Windows thô, hai lần ghi liền nhau có thể trùng giờ

    ds = danh_sach_van_ban(tmp_path)

    assert [(v.hash_pdf, v.ten_file) for v in ds] == [("def456", "HĐ khác.pdf"), ("abc123", "HĐ mẫu.pdf")]
    assert (ds[1].so_trang, ds[1].so_trang_tin_cay_thap, ds[1].so_dieu_khoan) == (1, 1, 2)
