"""Test với model thật: cần llama-server đang chạy (docs/chay-model-local.md).

Chạy: .venv/Scripts/python -m pytest -m llm      (Lượt thẩm định đủ 17 Mục TOSS mất khoảng 5–6 giờ trên CPU)
"""

from dataclasses import replace
from pathlib import Path

import pytest

from thamdinh.checklist import load_checklist
from thamdinh.llm import LocalClient
from thamdinh.settings import load_settings
from thamdinh.so_hoa import so_hoa
from thamdinh.kho_luot import KhoLuot
from thamdinh.tham_dinh import xay_prompt_cac_ben, tham_dinh
from thamdinh.truy_xuat import LocalEmbeddingClient, chuan_bi_truy_xuat

pytestmark = pytest.mark.llm

GOC = Path(__file__).parent.parent
TOSS = next((GOC / "Sample").glob("*TOSS*.pdf"))


@pytest.fixture(scope="module")
def settings():
    return load_settings()


@pytest.fixture(scope="module")
def llm(settings):
    return LocalClient(settings.local_url, settings.model, suy_luan=settings.suy_luan)


@pytest.fixture(scope="module")
def van_ban(settings):
    return so_hoa(TOSS, thu_muc_luu=settings.data_dir)


def test_model_xac_dinh_dung_cac_ben_toss(llm, van_ban):
    d = llm.complete_json(*xay_prompt_cac_ben(van_ban))

    assert d["cong_ty"] == "Bên B"
    assert "VIETTEL" in d["ten_cong_ty"].upper()


def test_tieu_chi_mo_ta_van_de_xau_khong_bi_hieu_nguoc(llm, van_ban, settings):
    """TOSS có phạt vi phạm (Điều 10.4) và bất khả kháng (Điều 11), nên hai vấn đề của 7.V2 và 16.V2 không xảy ra."""
    checklist = load_checklist(GOC / "checklists" / "dau-ra-v1.1.yaml")
    tx = chuan_bi_truy_xuat(
        van_ban, checklist, llm, LocalEmbeddingClient(settings.embedding_url, settings.embedding_model),
        settings.ngan_sach_truy_xuat, model=settings.model, thu_muc_luu=settings.data_dir, dem_token=llm.dem_token,
    )
    hai_muc = replace(checklist, muc=[m for m in checklist.muc if m.so in (7, 16)])

    kq = tham_dinh(van_ban, hai_muc, llm, model=settings.model, tien_trinh=print, truy_xuat=tx)

    danh_gia = {t.ma: t for m in kq.muc for t in m.tieu_chi}
    for ma in ("7.V2", "16.V2"):
        assert danh_gia[ma].danh_gia == "khong_thoa", danh_gia[ma].ly_do


def test_luot_tham_dinh_toss_du_17_muc(llm, van_ban, settings):
    kq = tham_dinh(van_ban, load_checklist(GOC / "checklists" / "dau-ra-v1.1.yaml"), llm,
                   ngu_canh=settings.ngu_canh, model=settings.model, tien_trinh=print,
                   sau_moi_buoc=KhoLuot(settings.data_dir).luu)  # lưu sau mỗi Mục: một Lượt mất nhiều giờ
    print(f"Đã lưu Lượt {kq.ma}; Mục lỗi chạy lại bằng scripts/chay_tham_dinh.py --tiep-tuc {kq.ma}")

    chua_duoc = [(m.so, m.loi) for m in kq.muc if m.ket_qua is None]
    assert not chua_duoc, f"Mục chưa đánh giá được: {chua_duoc}"
    trich_dan = [td for m in kq.muc for t in m.tieu_chi for td in t.trich_dan]
    assert trich_dan and all(td.trang_thai for td in trich_dan)
