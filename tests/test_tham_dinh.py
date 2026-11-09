import json
import re
from pathlib import Path

import pytest

from thamdinh.checklist import load_checklist
from thamdinh.llm import LLMBiCatError, LLMResponseError
from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc, hash_noi_dung
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.tham_dinh import VanBanQuaDaiError, luu_luot, nap_luot, tham_dinh

CHECKLIST = load_checklist(Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml")

VAN_BAN = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ TOSS.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        DieuKhoan(0, "Phần mở đầu", "mo_dau", None, None, 1, 1,
                  "BÊN A: TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM - CTCP\nBÊN B: CÔNG TY TNHH MTV ĐẦU TƯ CÔNG NGHỆ VIETTEL"),
        DieuKhoan(1, "Điều 10", "dieu", "PHẠT VI PHẠM", None, 9, 9,
                  "ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG\n10.1. Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm."),
    ],
    canh_bao=[],
)
THAT = {"so_hieu": "Điều 10", "nguyen_van": "Mức phạt không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm"}
BIA = {"so_hieu": "Điều 10", "nguyen_van": "Bên A được miễn trừ mọi trách nhiệm"}


class ModelGia:
    """Thay cho LocalClient: trả lời theo kịch bản và ghi lại các prompt đã nhận."""

    def __init__(self, sua_muc=None, loi_muc=None, cat_muc=None):
        self.prompt: list[str] = []
        self.schema: list[dict] = []
        self.cat_muc = cat_muc or {}  # {số Mục: số Tiêu chí trở lên thì câu trả lời bị cắt vì quá dài}
        self.sua_muc = sua_muc or {}  # {số Mục: {mã: câu trả lời thay thế}}
        self.loi_muc = dict(loi_muc or {})  # {số Mục: số lần trả JSON sai trước khi trả đúng}

    def complete_json(self, prompt, schema):
        self.prompt.append(prompt)
        self.schema.append(schema)
        if "xác định các bên" in prompt:
            return {"cong_ty": "Bên B", "ten_cong_ty": "Viettel", "ten_khach_hang": "VNA",
                    "trich_dan": [{"so_hieu": "Phần mở đầu", "nguyen_van": "BÊN B: CÔNG TY TNHH MTV ĐẦU TƯ CÔNG NGHỆ VIETTEL"}]}
        so = int(re.findall(r"MỤC CHECKLIST (\d+):", prompt)[0])
        if self.loi_muc.get(so, 0) > 0:
            self.loi_muc[so] -= 1
            raise LLMResponseError("JSON sai schema tại 7.D1: thiếu gia_tri")
        if len(schema["properties"]) >= self.cat_muc.get(so, 10**6):
            raise LLMBiCatError("Câu trả lời bị cắt vì vượt 4096 token")
        tra_loi = {}
        for ma, tc in schema["properties"].items():
            muc_kq = "dat" if ".D" in ma else "khac"
            tl = {"danh_gia": "thoa" if muc_kq == "dat" else "khong_thoa", "ly_do": "…", "trich_dan": [THAT]}
            if "gia_tri" in tc["properties"]:
                tl["gia_tri"] = 8
            if "gia_tri_dieu_kien" in tc["properties"]:
                tl["gia_tri_dieu_kien"] = 39_820_000_000
            tra_loi[ma] = tl
        tra_loi.update(self.sua_muc.get(so, {}))
        return tra_loi


def muc(kq, so):
    return next(m for m in kq.muc if m.so == so)


def tieu_chi(kq, ma):
    return next(t for m in kq.muc for t in m.tieu_chi if t.ma == ma)


def test_xac_dinh_cac_ben_truoc_roi_danh_gia_du_17_muc():
    model = ModelGia()

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    assert "xác định các bên" in model.prompt[0]
    assert len(model.prompt) == 1 + 17
    assert kq.cac_ben.cong_ty == "Bên B"
    assert [m.so for m in kq.muc] == list(range(1, 18))
    assert all(m.ket_qua is not None and m.loi is None for m in kq.muc)


def test_ket_qua_muc_di_qua_buoc_tong_hop():
    model = ModelGia(sua_muc={7: {"7.L1": {"danh_gia": "thoa", "ly_do": "Phạt một chiều", "trich_dan": [THAT]}}})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    assert muc(kq, 3).ket_qua.ket_qua == "dat"
    assert muc(kq, 7).ket_qua.ket_qua == "luu_y"
    assert "7.L1" in muc(kq, 7).ket_qua.tieu_chi_quyet_dinh


def test_tieu_chi_dinh_luong_do_code_so_sanh():
    model = ModelGia(sua_muc={7: {"7.D1": {"danh_gia": "thoa", "gia_tri": 12, "ly_do": "…", "trich_dan": [THAT]},
                                  "7.V1": {"danh_gia": "khong_thoa", "gia_tri": 12, "ly_do": "…", "trich_dan": [THAT]}}})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    assert tieu_chi(kq, "7.D1").danh_gia_llm == "thoa"
    assert tieu_chi(kq, "7.D1").danh_gia == "khong_thoa"
    assert muc(kq, 7).ket_qua.ket_qua == "vi_pham"


def test_kiem_tra_moi_trich_dan():
    model = ModelGia(sua_muc={3: {
        "3.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [THAT, BIA]},
        "3.D2": {"danh_gia": "khong_ro", "ly_do": "Không tìm thấy điều khoản về tài sản trí tuệ có sẵn", "trich_dan": []},
    }})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    d1 = tieu_chi(kq, "3.D1")
    assert [t.trang_thai for t in d1.trich_dan] == ["khop", "khong_xac_minh_duoc"]
    d2 = tieu_chi(kq, "3.D2")
    assert d2.trich_dan == () and d2.khong_tim_thay_dieu_khoan


def test_trich_dan_bi_cat_o_gioi_han_do_dai_thi_bo_tu_cuoi_do_dang():
    # llama-server ép đóng chuỗi ở maxLength: ký tự cuối thường là rác (Mục 14 TOSS: "việc sử dụng и")
    dai = "Bên B bảo đảm " + "hỗ trợ kỹ thuật liên tục cho Bên A, " * 12 + "trong suốt thời hạn Hợp đồng."
    van_ban = VanBanHieuLuc(**{**VAN_BAN.__dict__, "dieu_khoan": [
        *VAN_BAN.dieu_khoan, DieuKhoan(2, "Điều 8", "dieu", "HỖ TRỢ", None, 8, 8, dai)]})
    bi_cat = {"so_hieu": "Điều 8", "nguyen_van": dai[:299] + "и"}
    model = ModelGia(sua_muc={3: {"3.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [bi_cat]}}})

    td = tieu_chi(tham_dinh(van_ban, CHECKLIST, model), "3.D1").trich_dan[0]

    assert td.trang_thai == "khop"
    assert td.nguyen_van.endswith(" …") and "и" not in td.nguyen_van


def test_json_sai_mot_lan_thi_goi_lai_kem_loi():
    model = ModelGia(loi_muc={7: 1})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    lan_goi_muc_7 = [p for p in model.prompt if "MỤC CHECKLIST 7:" in p]
    assert len(lan_goi_muc_7) == 2
    assert "thiếu gia_tri" in lan_goi_muc_7[1]
    assert muc(kq, 7).ket_qua is not None


def test_json_sai_hai_lan_thi_muc_chua_danh_gia_duoc_cac_muc_khac_van_chay():
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}))

    assert muc(kq, 7).ket_qua is None
    assert "chưa đánh giá được" in muc(kq, 7).loi
    assert muc(kq, 8).ket_qua is not None


def ma_tieu_chi(so):
    return [tc.ma for ds in next(m for m in CHECKLIST.muc if m.so == so).tieu_chi.values() for tc in ds]


def test_tra_loi_bi_cat_thi_chia_doi_tieu_chi_thay_vi_goi_lai_y_nguyen():
    # Ở nhiệt độ 0, gọi lại cùng prompt thì model lặp y như cũ (Mục 14 TOSS: hai lần ~20k token)
    model = ModelGia(cat_muc={14: 7})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model)

    lan_goi = [(p, s) for p, s in zip(model.prompt, model.schema) if "MỤC CHECKLIST 14:" in p]
    assert [len(s["properties"]) for _, s in lan_goi] == [7, 4, 3]
    assert sorted(ma for _, s in lan_goi[1:] for ma in s["properties"]) == sorted(ma_tieu_chi(14))
    assert not any("Lần trả lời trước bị lỗi" in p for p, _ in lan_goi)
    assert "14.V3" not in lan_goi[1][0] and "14.V3" in lan_goi[2][0]  # prompt mỗi nửa chỉ nêu Tiêu chí của nửa đó
    m = muc(kq, 14)
    assert m.loi is None and [t.ma for t in m.tieu_chi] == ma_tieu_chi(14)


def test_moi_tieu_chi_mot_lan_goi_khi_bat():
    # Model nhỏ chấm từng Tiêu chí riêng; phần đầu prompt của Mục giống nhau nên vẫn dùng lại cache
    model = ModelGia(sua_muc={7: {"7.L1": {"danh_gia": "thoa", "ly_do": "Phạt một chiều", "trich_dan": [THAT]}}})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model, moi_tieu_chi_mot_lan=True)

    lan_goi = [(p, s) for p, s in zip(model.prompt, model.schema) if "MỤC CHECKLIST 7:" in p]
    assert [list(s["properties"]) for _, s in lan_goi] == [[ma] for ma in ma_tieu_chi(7)]
    dau = [p.split("Các Tiêu chí cần đánh giá:")[0] for p, _ in lan_goi]
    assert len(set(dau)) == 1
    assert "7.V1" not in lan_goi[0][0].split("Các Tiêu chí cần đánh giá:")[1]
    m = muc(kq, 7)
    assert [t.ma for t in m.tieu_chi] == ma_tieu_chi(7)
    assert m.ket_qua.ket_qua == "luu_y" and "7.L1" in m.ket_qua.tieu_chi_quyet_dinh


def test_moi_tieu_chi_mot_lan_ma_van_bi_cat_thi_muc_chua_danh_gia_duoc():
    # Một Tiêu chí đã là phần nhỏ nhất: không chia tiếp, không gọi lại
    model = ModelGia(cat_muc={7: 1})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model, moi_tieu_chi_mot_lan=True)

    assert muc(kq, 7).ket_qua is None and "bị cắt" in muc(kq, 7).loi
    assert len([p for p in model.prompt if "MỤC CHECKLIST 7:" in p]) == 1
    assert muc(kq, 8).ket_qua is not None


def test_mot_nua_van_bi_cat_thi_muc_chua_danh_gia_duoc():
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(cat_muc={14: 4}))

    assert muc(kq, 14).ket_qua is None
    assert "bị cắt" in muc(kq, 14).loi
    assert muc(kq, 15).ket_qua is not None


def test_van_ban_qua_dai_bao_loi_truoc_khi_goi_model():
    model = ModelGia()

    with pytest.raises(VanBanQuaDaiError, match="chế độ truy xuất"):
        tham_dinh(VAN_BAN, CHECKLIST, model, ngu_canh=1000)
    assert model.prompt == []


def test_luu_luot_ra_file_json(tmp_path):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), model="qwen3.5")

    file = luu_luot(kq, tmp_path)

    d = json.loads(file.read_text(encoding="utf-8"))
    assert file.parent == tmp_path / "luot"
    assert d["hash_pdf"] == "abc123" and d["model"] == "qwen3.5"
    assert len(d["muc"]) == 17


def test_bao_ket_qua_tam_sau_moi_buoc_de_luu_ngay():
    # Một Lượt trên CPU mất nhiều giờ: tắt máy giữa chừng không được mất các Mục đã xong
    tam = []

    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), sau_moi_buoc=tam.append)

    assert [len(t.muc) for t in tam] == list(range(0, 18))
    assert tam[0].cac_ben is not None
    assert tam[-1].muc == kq.muc


def test_nap_lai_luot_da_luu(tmp_path):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}))

    assert nap_luot(luu_luot(kq, tmp_path)) == kq


def test_chay_tiep_chi_goi_model_cho_muc_loi_hoac_chua_chay():
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(loi_muc={7: 2}))
    truoc = truoc.__class__(**{**truoc.__dict__, "muc": tuple(m for m in truoc.muc if m.so != 17)})  # dừng trước Mục 17
    model = ModelGia()

    kq = tham_dinh(VAN_BAN, CHECKLIST, model, luot_truoc=truoc)

    assert [re.findall(r"MỤC CHECKLIST (\d+):", p)[0] for p in model.prompt] == ["7", "17"]
    assert [m.so for m in kq.muc] == list(range(1, 18))
    assert all(m.ket_qua is not None for m in kq.muc)
    assert kq.cac_ben == truoc.cac_ben and kq.bat_dau == truoc.bat_dau
    assert kq.ma == truoc.ma and kq.luot_goc is None  # chạy lại phần lỗi: vẫn là Lượt đó


def test_chay_lai_muc_chi_dinh_du_da_co_ket_qua():
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    model = ModelGia(sua_muc={3: {"3.D1": {"danh_gia": "khong_thoa", "ly_do": "chạy lại", "trich_dan": [THAT]}}})

    kq = tham_dinh(VAN_BAN, CHECKLIST, model, luot_truoc=truoc, chay_lai={3})

    assert len(model.prompt) == 1
    assert tieu_chi(kq, "3.D1").ly_do == "chạy lại"
    # Mục đã có Kết quả đề xuất không bị ghi đè: tạo Lượt mới, ghi Lượt gốc
    assert kq.ma != truoc.ma and kq.luot_goc == truoc.ma
    assert muc(kq, 5) == muc(truoc, 5)


def test_luot_co_ma_rieng_va_hash_van_ban_da_dung():
    a, b = tham_dinh(VAN_BAN, CHECKLIST, ModelGia()), tham_dinh(VAN_BAN, CHECKLIST, ModelGia())

    assert a.ma != b.ma and a.ma.startswith("abc123")
    assert a.hash_van_ban == hash_noi_dung(VAN_BAN)


def test_chay_tiep_luot_cua_hop_dong_khac_thi_bao_loi():
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())
    khac = VanBanHieuLuc(**{**VAN_BAN.__dict__, "hash_pdf": "khac"})

    with pytest.raises(ValueError, match="Hợp đồng khác"):
        tham_dinh(khac, CHECKLIST, ModelGia(), luot_truoc=truoc)


class TruyXuatGia:
    """Thay cho chế độ truy xuất thật: mỗi Mục chỉ được Điều 10."""

    canh_bao = ("Lưới an toàn chỉ dùng BM25.",)

    def __init__(self):
        self.muc = []

    def ngu_canh(self, muc_cl):
        from thamdinh.truy_xuat import NguCanhMuc

        self.muc.append(muc_cl.so)
        dk = VAN_BAN.dieu_khoan[1]
        return NguCanhMuc((dk.so_hieu,), f"### {dk.so_hieu}\n{dk.noi_dung}", 40, ("Phụ lục 02",),
                          (f"Vượt ngân sách: đã bỏ Phụ lục 02 (Mục {muc_cl.so}).",))


def test_che_do_truy_xuat_chi_dua_dieu_khoan_duoc_chon_vao_prompt():
    model, truy_xuat = ModelGia(), TruyXuatGia()

    kq = tham_dinh(VAN_BAN, CHECKLIST, model, truy_xuat=truy_xuat)

    prompt_muc = [p for p in model.prompt if "MỤC CHECKLIST" in p]
    assert len(prompt_muc) == 17 and truy_xuat.muc == list(range(1, 18))
    assert all("Mức phạt không vượt quá 8%" in p and "BÊN B: CÔNG TY TNHH" not in p for p in prompt_muc)
    assert all("không phải toàn văn" in p for p in prompt_muc)
    assert kq.che_do == "truy_xuat"
    assert kq.canh_bao == ("Lưới an toàn chỉ dùng BM25.",)
    m = muc(kq, 7)
    assert m.dieu_khoan_dua_vao == ("Điều 10",)
    assert m.canh_bao == ("Vượt ngân sách: đã bỏ Phụ lục 02 (Mục 7).",)
    assert [t.trang_thai for t in tieu_chi(kq, "7.D1").trich_dan] == ["khop"]  # vẫn kiểm theo toàn bộ Văn bản hiệu lực


def test_che_do_truy_xuat_bi_cat_thi_chia_doi_van_dung_ngu_canh_truy_xuat():
    model = ModelGia(cat_muc={14: 7})

    tham_dinh(VAN_BAN, CHECKLIST, model, truy_xuat=TruyXuatGia())

    lan_goi = [p for p in model.prompt if "MỤC CHECKLIST 14:" in p]
    assert len(lan_goi) == 3 and all("không phải toàn văn" in p for p in lan_goi)


def test_che_do_toan_van_ghi_toan_van_vao_luot():
    m = muc(tham_dinh(VAN_BAN, CHECKLIST, ModelGia()), 7)

    assert m.dieu_khoan_dua_vao == ("Phần mở đầu", "Điều 10") and m.canh_bao == ()


def test_nap_lai_luot_truy_xuat(tmp_path):
    kq = tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), truy_xuat=TruyXuatGia())

    assert nap_luot(luu_luot(kq, tmp_path)) == kq


def test_chay_tiep_khac_che_do_thi_bao_loi():
    truoc = tham_dinh(VAN_BAN, CHECKLIST, ModelGia())

    with pytest.raises(ValueError, match="chế độ"):
        tham_dinh(VAN_BAN, CHECKLIST, ModelGia(), luot_truoc=truoc, truy_xuat=TruyXuatGia())

