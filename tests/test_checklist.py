import textwrap
from pathlib import Path

import pytest

from thamdinh.checklist import ChecklistError, load_checklist

HOP_LE = """
ma: dau-ra
phien_ban: "1.1"
ten: Checklist thử
dua_tren: V1
chu_de:
  - {ma: phat-vi-pham, ten: Phạt vi phạm}
danh_muc_tham_chieu:
  nganh-nghe-dang-ky: danh-muc/nganh.yaml
muc:
  - so: 7
    cau_hoi: Điều khoản phạt có bảo vệ Công ty không?
    chu_de: [phat-vi-pham]
    tieu_chi:
      dat:
        - ma: "7.D1"
          mo_ta: Mức phạt không vượt 8%
          loai: dinh_luong
          truong: muc_phat_phan_tram
          phep_so_sanh: "<="
          nguong: 8
      luu_y:
        - {ma: "7.L1", mo_ta: Phạt một chiều, loai: dinh_tinh}
      vi_pham:
        - {ma: "7.V1", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh}
"""


def viet_checklist(tmp_path, noi_dung):
    (tmp_path / "danh-muc").mkdir(exist_ok=True)
    (tmp_path / "danh-muc" / "nganh.yaml").write_text("trang_thai: da-soan\n", encoding="utf-8")
    path = tmp_path / "checklist.yaml"
    path.write_text(textwrap.dedent(noi_dung), encoding="utf-8")
    return path


def test_nap_checklist_hop_le(tmp_path):
    checklist = load_checklist(viet_checklist(tmp_path, HOP_LE))

    assert checklist.phien_ban == "1.1"
    muc = checklist.muc[0]
    assert muc.so == 7
    assert muc.chu_de == ["phat-vi-pham"]
    dinh_luong = muc.tieu_chi["dat"][0]
    assert (dinh_luong.ma, dinh_luong.phep_so_sanh, dinh_luong.nguong) == ("7.D1", "<=", 8)
    assert [t.ma for t in muc.tieu_chi["vi_pham"]] == ["7.V1"]


@pytest.mark.parametrize(
    "cu, moi, thong_bao",
    [
        # Mục thiếu tiêu chí Đạt
        (
            """      dat:
        - ma: "7.D1"
          mo_ta: Mức phạt không vượt 8%
          loai: dinh_luong
          truong: muc_phat_phan_tram
          phep_so_sanh: "<="
          nguong: 8
""",
            "      dat: []\n",
            "Mục 7: thiếu tiêu chí Đạt",
        ),
        # Mã tiêu chí trùng
        ('{ma: "7.V1", mo_ta: Mức phạt vượt 8%', '{ma: "7.L1", mo_ta: Mức phạt vượt 8%', "Mục 7, tiêu chí 7.L1: mã bị trùng"),
        # Tiêu chí định lượng thiếu ngưỡng
        ("          nguong: 8\n", "", "Mục 7, tiêu chí 7.D1: tiêu chí định lượng thiếu nguong"),
        # Phép so sánh không hỗ trợ
        ('phep_so_sanh: "<="', 'phep_so_sanh: "~"', "Mục 7, tiêu chí 7.D1: phep_so_sanh '~' không hợp lệ"),
        # Loại tiêu chí sai
        ("loai: dinh_tinh}\n      vi_pham", "loai: cam_tinh}\n      vi_pham", "Mục 7, tiêu chí 7.L1: loai 'cam_tinh' không hợp lệ"),
        # Chủ đề không được khai báo
        ("chu_de: [phat-vi-pham]", "chu_de: [phat-vi-pham, thanh-toan]", "Mục 7: Chủ đề 'thanh-toan' chưa được khai báo"),
        # Danh mục tham chiếu không tồn tại
        ("danh-muc/nganh.yaml", "danh-muc/khong-co.yaml", "Danh mục tham chiếu 'nganh-nghe-dang-ky': không tìm thấy file"),
        # Số mục trùng
        ("muc:\n", "muc:\n  - {so: 7, cau_hoi: Trùng, chu_de: [], tieu_chi: {dat: [{ma: X1, mo_ta: x, loai: dinh_tinh}], vi_pham: [{ma: X2, mo_ta: x, loai: dinh_tinh}]}}\n", "Mục 7: số mục bị trùng"),
    ],
)
def test_bao_loi_chi_ro_vi_tri(tmp_path, cu, moi, thong_bao):
    noi_dung = textwrap.dedent(HOP_LE)
    assert cu in noi_dung
    path = viet_checklist(tmp_path, noi_dung.replace(cu, moi, 1))

    with pytest.raises(ChecklistError) as loi:
        load_checklist(path)

    assert thong_bao in str(loi.value)


def test_bao_loi_khi_thieu_truong_bat_buoc(tmp_path):
    path = viet_checklist(tmp_path, textwrap.dedent(HOP_LE).replace("    cau_hoi: Điều khoản phạt có bảo vệ Công ty không?\n", ""))

    with pytest.raises(ChecklistError, match="Mục 7: thiếu trường 'cau_hoi'"):
        load_checklist(path)


def test_muc_khai_bao_danh_muc_tham_chieu_su_dung(tmp_path):
    noi_dung = textwrap.dedent(HOP_LE).replace("    chu_de: [phat-vi-pham]\n", "    chu_de: [phat-vi-pham]\n    danh_muc: [nganh-nghe-dang-ky]\n")

    checklist = load_checklist(viet_checklist(tmp_path, noi_dung))

    assert checklist.muc[0].danh_muc == ["nganh-nghe-dang-ky"]


def test_bao_loi_khi_muc_dung_danh_muc_chua_khai_bao(tmp_path):
    noi_dung = textwrap.dedent(HOP_LE).replace("    chu_de: [phat-vi-pham]\n", "    chu_de: [phat-vi-pham]\n    danh_muc: [dau-hieu-ear]\n")

    with pytest.raises(ChecklistError, match="Mục 7: Danh mục tham chiếu 'dau-hieu-ear' chưa được khai báo"):
        load_checklist(viet_checklist(tmp_path, noi_dung))


DIEU_KIEN = """          dieu_kien: {truong: gia_tri_hop_dong_vnd, phep_so_sanh: ">", nguong: 2000000000}
"""


def test_tieu_chi_co_dieu_kien_dinh_luong(tmp_path):
    noi_dung = textwrap.dedent(HOP_LE).replace(
        '        - {ma: "7.V1", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh}\n',
        '        - ma: "7.V1"\n          mo_ta: Người ký không phải Giám đốc\n          loai: dinh_tinh\n' + DIEU_KIEN,
    )

    tc = load_checklist(viet_checklist(tmp_path, noi_dung)).muc[0].tieu_chi["vi_pham"][0]

    assert (tc.dieu_kien.truong, tc.dieu_kien.phep_so_sanh, tc.dieu_kien.nguong) == ("gia_tri_hop_dong_vnd", ">", 2000000000)
    assert load_checklist(viet_checklist(tmp_path, HOP_LE)).muc[0].tieu_chi["vi_pham"][0].dieu_kien is None


@pytest.mark.parametrize(
    "dieu_kien, thong_bao",
    [
        ('{truong: gia_tri_hop_dong_vnd, phep_so_sanh: ">"}', "Mục 7, tiêu chí 7.V1: dieu_kien thiếu nguong"),
        ('{truong: gia_tri_hop_dong_vnd, phep_so_sanh: "~", nguong: 1}', "Mục 7, tiêu chí 7.V1: dieu_kien có phep_so_sanh '~' không hợp lệ"),
    ],
)
def test_bao_loi_dieu_kien_sai(tmp_path, dieu_kien, thong_bao):
    noi_dung = textwrap.dedent(HOP_LE).replace(
        '{ma: "7.V1", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh}',
        '{ma: "7.V1", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh, dieu_kien: ' + dieu_kien + "}",
    )

    with pytest.raises(ChecklistError) as loi:
        load_checklist(viet_checklist(tmp_path, noi_dung))

    assert thong_bao in str(loi.value)


def test_tieu_chi_danh_dau_can_thong_tin_ngoai_hop_dong(tmp_path):
    noi_dung = textwrap.dedent(HOP_LE).replace(
        "loai: dinh_tinh}\n      vi_pham:\n        - {ma: \"7.V1\", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh}",
        "loai: dinh_tinh}\n      vi_pham:\n        - {ma: \"7.V1\", mo_ta: Mức phạt vượt 8%, loai: dinh_tinh, can_thong_tin_ngoai: true}",
    )

    muc = load_checklist(viet_checklist(tmp_path, noi_dung)).muc[0]

    assert muc.tieu_chi["vi_pham"][0].can_thong_tin_ngoai is True
    assert muc.tieu_chi["luu_y"][0].can_thong_tin_ngoai is False


def test_tim_file_checklist_theo_ma_va_phien_ban_luu_trong_luot():
    from thamdinh.checklist import tim_checklist

    thu_muc = Path(__file__).parent.parent / "checklists"
    assert tim_checklist(thu_muc, "dau-ra 1.1").name == "dau-ra-v1.1.yaml"
    with pytest.raises(FileNotFoundError, match="dau-ra 9.9"):
        tim_checklist(thu_muc, "dau-ra 9.9")
