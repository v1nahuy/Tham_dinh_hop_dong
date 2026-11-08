import os
import re
from pathlib import Path

import jsonschema
import pytest

from thamdinh.checklist import load_checklist
from thamdinh.llm import LLMKetNoiError, LLMResponseError
from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.truy_xuat import BoTimBM25, chuan_bi_truy_xuat, gan_chu_de

CHECKLIST = load_checklist(Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml")
DAI = "Bên B cung cấp dịch vụ vận hành hệ thống theo yêu cầu kỹ thuật. " * 120  # khoảng 3k token


def dk(ma, so_hieu, noi_dung, cha=None, loai="khoan"):
    return DieuKhoan(ma, so_hieu, loai, None, cha, 1, 1, noi_dung)


VAN_BAN = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        dk(0, "Điều 10", "ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG", loai="dieu"),
        dk(1, "10.1", "Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm.", cha=0),
        dk(2, "10.2", "Bên vi phạm bồi thường toàn bộ thiệt hại thực tế.", cha=0),
        dk(3, "Phụ lục 02, Mục A", DAI, loai="muc_phu_luc"),
        dk(4, "Phụ lục 02, Mục B", DAI, loai="muc_phu_luc"),
        dk(5, "4.1", "Thanh toán trong vòng 30 ngày kể từ ngày nghiệm thu.", loai="khoan"),
        dk(6, "4.1", "Bên A tạm ứng 10% giá trị hợp đồng.", loai="khoan"),  # số hiệu trùng như TOSS
    ],
    canh_bao=[],
)

TU_KHOA = {"phạt": "phat-vi-pham", "bồi thường": "boi-thuong", "thanh toán": "thanh-toan", "tạm ứng": "thanh-toan"}


class ModelGia:
    def __init__(self, loi_khi_co=None):
        self.goi: list[tuple[str, dict]] = []
        self.loi_khi_co = loi_khi_co  # chuỗi: nhóm nào chứa chuỗi này thì trả JSON sai

    def complete_json(self, prompt, schema):
        self.goi.append((prompt, schema))
        if self.loi_khi_co and self.loi_khi_co in prompt:
            raise LLMResponseError("JSON sai")
        tra_loi = {}
        for khoa in schema["properties"]:
            noi_dung = prompt.split(f"[{khoa}]", 1)[1].split("\n### ", 1)[0].lower()
            tra_loi[khoa] = [cd for tu, cd in TU_KHOA.items() if tu in noi_dung] * 2  # lặp để thử bỏ trùng
        return tra_loi


def test_gan_chu_de_cho_tung_dieu_khoan():
    kq = gan_chu_de(VAN_BAN, CHECKLIST, ModelGia())

    assert kq.chu_de[1] == ("phat-vi-pham",)
    assert kq.chu_de[2] == ("boi-thuong",)
    assert kq.chu_de[5] == ("thanh-toan",) and kq.chu_de[6] == ("thanh-toan",)  # số hiệu trùng vẫn tách đúng
    assert kq.chu_de[3] == ()
    assert set(kq.chu_de) == {d.ma for d in VAN_BAN.dieu_khoan}


def test_chia_nhom_dieu_khoan_lien_nhau_khong_vuot_4k_token():
    model = ModelGia()

    gan_chu_de(VAN_BAN, CHECKLIST, model)

    nhom = [[int(k[2:]) for k in s["properties"]] for _, s in model.goi]
    assert sorted(ma for n in nhom for ma in n) == list(range(7))  # mỗi Điều khoản đúng một lần
    assert all(n == list(range(n[0], n[-1] + 1)) for n in nhom)  # liền nhau
    assert not any(3 in n and 4 in n for n in nhom)  # hai Điều khoản khoảng 3k token không chung nhóm


def test_dieu_khoan_lon_hon_gioi_han_nhom_duoc_gui_rieng():
    model = ModelGia()

    gan_chu_de(VAN_BAN, CHECKLIST, model, toi_da_token_nhom=1000)

    assert [[3], [4]] == [[int(k[2:]) for k in s["properties"]] for _, s in model.goi if "dk3" in s["properties"] or "dk4" in s["properties"]]


def test_schema_chi_nhan_ma_chu_de_cua_checklist():
    model = ModelGia()
    gan_chu_de(VAN_BAN, CHECKLIST, model)
    _, schema = model.goi[0]
    khoa = next(iter(schema["properties"]))

    jsonschema.validate({k: ["thanh-toan"] for k in schema["properties"]}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**{k: [] for k in schema["properties"]}, khoa: ["chu-de-la"]}, schema)


def test_cac_nhom_chung_phan_dau_prompt_chua_danh_sach_chu_de():
    model = ModelGia()
    gan_chu_de(VAN_BAN, CHECKLIST, model)

    chung = os.path.commonprefix([p for p, _ in model.goi])

    assert all(f"{ma}: {ten}" in chung for ma, ten in CHECKLIST.chu_de.items())
    # Câu hỏi được nhắc lại sau văn bản (model nhỏ bám theo phần cuối prompt)
    p = model.goi[0][0]
    assert p.index("Với mỗi mã") > p.index("=== HẾT ===")


def test_nhom_loi_thi_cac_dieu_khoan_do_khong_co_chu_de_va_co_canh_bao():
    kq = gan_chu_de(VAN_BAN, CHECKLIST, ModelGia(loi_khi_co="Mức phạt"))

    assert kq.chu_de[1] == ()
    assert kq.chu_de[5] == ("thanh-toan",)
    assert any("10.1" in c for c in kq.canh_bao)


def test_luu_va_dung_lai_ket_qua(tmp_path):
    gan_chu_de(VAN_BAN, CHECKLIST, ModelGia(), model="qwen3.5", thu_muc_luu=tmp_path)
    model = ModelGia()

    kq = gan_chu_de(VAN_BAN, CHECKLIST, model, model="qwen3.5", thu_muc_luu=tmp_path)

    assert model.goi == []
    assert kq.chu_de[1] == ("phat-vi-pham",)


def test_van_ban_sua_tay_hoac_doi_model_thi_gan_lai(tmp_path):
    gan_chu_de(VAN_BAN, CHECKLIST, ModelGia(), model="qwen3.5", thu_muc_luu=tmp_path)
    sua = VanBanHieuLuc(**{**VAN_BAN.__dict__, "dieu_khoan": [
        *VAN_BAN.dieu_khoan[:1], dk(1, "10.1", "Mức phạt không vượt quá 12% giá trị.", cha=0), *VAN_BAN.dieu_khoan[2:]]})

    model_sua, model_khac = ModelGia(), ModelGia()
    gan_chu_de(sua, CHECKLIST, model_sua, model="qwen3.5", thu_muc_luu=tmp_path)
    gan_chu_de(VAN_BAN, CHECKLIST, model_khac, model="qwen3.5-4b", thu_muc_luu=tmp_path)

    assert model_sua.goi and model_khac.goi


def test_nhom_loi_khong_duoc_luu_de_lan_sau_gan_lai(tmp_path):
    gan_chu_de(VAN_BAN, CHECKLIST, ModelGia(loi_khi_co="Mức phạt"), thu_muc_luu=tmp_path)
    model = ModelGia()

    kq = gan_chu_de(VAN_BAN, CHECKLIST, model, thu_muc_luu=tmp_path)

    assert model.goi and kq.chu_de[1] == ("phat-vi-pham",) and not kq.canh_bao


def test_chuan_bi_truy_xuat_gan_chu_de_roi_chon_dieu_khoan_cho_tung_muc():
    muc_7 = next(m for m in CHECKLIST.muc if m.so == 7)

    tx = chuan_bi_truy_xuat(VAN_BAN, CHECKLIST, ModelGia(loi_khi_co="Phụ lục 02, Mục B"), nhung=None, ngan_sach=16000)

    assert [type(b) for b in tx.tim_kiem] == [BoTimBM25]
    assert any("Phụ lục 02, Mục B" in c for c in tx.canh_bao)  # gắn Chủ đề lỗi
    assert any("chỉ dùng BM25" in c for c in tx.canh_bao)
    nc = tx.ngu_canh(muc_7)
    assert {"10.1", "10.2"} <= set(nc.dieu_khoan)


def test_chuan_bi_truy_xuat_dem_token_chinh_xac_khi_co_may_chu():
    muc_7 = next(m for m in CHECKLIST.muc if m.so == 7)

    tx = chuan_bi_truy_xuat(VAN_BAN, CHECKLIST, ModelGia(), nhung=None, ngan_sach=16000, dem_token=lambda t: 7)

    assert tx.ngu_canh(muc_7).so_token == 7
    assert not any("ước tính" in c for c in tx.canh_bao)


def test_chuan_bi_truy_xuat_khong_dem_duoc_token_thi_uoc_tinh_va_canh_bao():
    def dem_loi(_):
        raise LLMKetNoiError("Chưa chạy máy chủ model")

    tx = chuan_bi_truy_xuat(VAN_BAN, CHECKLIST, ModelGia(), nhung=None, ngan_sach=16000, dem_token=dem_loi)

    assert any("ước tính" in c for c in tx.canh_bao)
    assert tx.ngu_canh(next(m for m in CHECKLIST.muc if m.so == 7)).so_token > 0
