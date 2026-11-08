import os
from pathlib import Path

import jsonschema
import pytest

from thamdinh.checklist import load_checklist
from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.tham_dinh import CacBen, xay_prompt_cac_ben, xay_prompt_muc

CHECKLIST = load_checklist(Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml")
MUC = {m.so: m for m in CHECKLIST.muc}

VAN_BAN = VanBanHieuLuc(
    hash_pdf="x",
    ten_file="HĐ TOSS.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        DieuKhoan(0, "Phần mở đầu", "mo_dau", None, None, 1, 1,
                  "BÊN A: TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM - CTCP\nBÊN B: CÔNG TY TNHH MTV ĐẦU TƯ CÔNG NGHỆ VIETTEL"),
        DieuKhoan(1, "Điều 10", "dieu", "PHẠT VI PHẠM", None, 9, 9,
                  "ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG\n10.1. Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm."),
        DieuKhoan(2, "4.3.2", "khoan", None, None, 3, 3, "Giá trị bảo đảm: 294.000.000 [xóa: 1.918.900.000]"),
    ],
    canh_bao=[],
)
CAC_BEN = CacBen("Bên B", "CÔNG TY TNHH MTV ĐẦU TƯ CÔNG NGHỆ VIETTEL", "TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM - CTCP", ())


def prompt(so: int) -> str:
    return xay_prompt_muc(MUC[so], CHECKLIST, VAN_BAN, CAC_BEN)[0]


def schema(so: int) -> dict:
    return xay_prompt_muc(MUC[so], CHECKLIST, VAN_BAN, CAC_BEN)[1]


def test_cac_muc_co_chung_phan_dau_chua_toan_van():
    chung = os.path.commonprefix([prompt(1), prompt(7), prompt(11)])

    for dk in VAN_BAN.dieu_khoan:
        assert dk.noi_dung in chung
    # Kết quả bước xác định các bên đứng sau toàn văn
    assert prompt(7).index("Công ty là Bên B") > prompt(7).index(VAN_BAN.dieu_khoan[-1].noi_dung)


def test_prompt_neu_quy_uoc_va_cac_ben():
    p = prompt(7)

    assert "Nếu" in p and "điều kiện không xảy ra" in p
    assert "[xóa: …]" in p
    assert "Công ty là Bên B" in p


def test_prompt_co_du_tieu_chi_cua_muc():
    p = prompt(7)

    for ds in MUC[7].tieu_chi.values():
        for tc in ds:
            assert tc.ma in p and tc.mo_ta in p
    assert MUC[7].cau_hoi in p


def test_tieu_chi_dinh_luong_va_co_dieu_kien_neu_truong_va_don_vi():
    p7, p1 = prompt(7), prompt(1)

    assert "muc_phat_cao_nhat_phan_tram" in p7 and "%" in p7
    assert "gia_tri_dieu_kien" in p1 and "gia_tri_hop_dong_vnd" in p1 and "đồng" in p1


def test_danh_muc_chi_dua_vao_muc_khai_bao():
    assert "6219" in prompt(2)  # ngành nghề đã đăng ký
    assert "Kinh doanh dịch vụ viễn thông" in prompt(2)  # ngành nghề có điều kiện
    assert "Category 5 Part 2" in prompt(6)  # dấu hiệu EAR
    assert "6219" not in prompt(7)


def tra_loi_muc_7(**sua):
    tl = {
        tc.ma: {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [{"so_hieu": "10.1", "nguyen_van": "Mức phạt"}]}
        for ds in MUC[7].tieu_chi.values()
        for tc in ds
    }
    for tc in (t for ds in MUC[7].tieu_chi.values() for t in ds if t.loai == "dinh_luong"):
        tl[tc.ma]["gia_tri"] = 8
    tl.update(sua)
    return tl


def test_schema_nhan_cau_tra_loi_dung():
    jsonschema.validate(tra_loi_muc_7(), schema(7))


@pytest.mark.parametrize(
    "sua_doi",
    [
        lambda tl: tl.pop("7.D1"),  # thiếu mã
        lambda tl: tl.update({"7.X9": tl["7.L1"]}),  # thừa mã
        lambda tl: tl["7.D1"].pop("gia_tri"),  # định lượng thiếu giá trị
        lambda tl: tl["7.L1"].update(danh_gia="dat"),  # đánh giá sai giá trị
    ],
)
def test_schema_tu_choi_cau_tra_loi_sai(sua_doi):
    tl = tra_loi_muc_7()
    sua_doi(tl)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(tl, schema(7))


def test_schema_tieu_chi_co_dieu_kien_bat_buoc_gia_tri_dieu_kien():
    item = schema(1)["properties"]["1.V2"]

    assert "gia_tri_dieu_kien" in item["required"]


@pytest.mark.parametrize("so", [1, 7])
def test_schema_dat_danh_gia_truoc_ly_do(so):
    """Model sinh JSON theo thứ tự thuộc tính. Đã thử đặt ly_do trước (issue 17, Q127): model viết lý do thành nhận xét
    "Hợp đồng tốt/xấu" rồi ghi "tốt" thành `thoa`, hiểu ngược nghĩa ở Tiêu chí Vi phạm/Lưu ý (79→83/122, 12 đúng→sai)."""
    for ma, item in schema(so)["properties"].items():
        thu_tu = list(item["properties"])
        assert thu_tu.index("danh_gia") < thu_tu.index("ly_do"), ma
    p = prompt(so)
    assert p.index("danh_gia", p.index("Trả lời bằng JSON")) < p.index("ly_do", p.index("Trả lời bằng JSON"))


def test_prompt_cac_ben_chi_dung_phan_mo_dau():
    p, s = xay_prompt_cac_ben(VAN_BAN)

    assert "BÊN B: CÔNG TY TNHH MTV ĐẦU TƯ CÔNG NGHỆ VIETTEL" in p
    assert "Mức phạt không vượt quá 8%" not in p
    jsonschema.validate({"cong_ty": "Bên B", "ten_cong_ty": "Viettel", "ten_khach_hang": "VNA", "trich_dan": []}, s)


def test_cau_hoi_va_quy_uoc_duoc_nhac_lai_sau_van_ban():
    # Model nhỏ bám theo phần cuối prompt: hướng dẫn chỉ nằm trước ~28k token văn bản thì bị quên
    p_cac_ben, _ = xay_prompt_cac_ben(VAN_BAN)
    het_van_ban = p_cac_ben.index("=== HẾT ===")
    assert p_cac_ben.index("dòng \"BÊN A:\" hay dòng \"BÊN B:\"", het_van_ban) > het_van_ban

    p = prompt(7)
    sau_van_ban = p[p.index("=== HẾT VĂN BẢN HỢP ĐỒNG ===") :]
    for nhac_lai in ("khong_ro", "Nếu …", "NGUYÊN VĂN", "###", "[xóa: …]"):
        assert nhac_lai in sau_van_ban


@pytest.mark.parametrize(
    "trich_dan",
    [
        [{"so_hieu": "10.1", "nguyen_van": "Mức phạt"}] * 4,  # quá nhiều trích dẫn
        [{"so_hieu": "10.1", "nguyen_van": "x" * 301}],  # trích dẫn quá dài
    ],
)
def test_schema_gioi_han_trich_dan(trich_dan):
    tl = tra_loi_muc_7()
    tl["7.L1"]["trich_dan"] = trich_dan

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(tl, schema(7))
