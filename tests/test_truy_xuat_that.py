"""Chế độ truy xuất với model thật: cần llama-server đang chạy (docs/chay-model-local.md).

Chạy: .venv/Scripts/python -m pytest -m llm tests/test_truy_xuat_that.py -s
Gắn Chủ đề cho TOSS lần đầu mất khoảng 40 phút trên CPU; kết quả lưu trong data/chu-de/ và dùng lại ở lần sau.
Máy chủ embedding bge-m3 không chạy thì lưới an toàn chỉ dùng BM25.
Độ phủ đo trên các Tiêu chí đã có Trích dẫn trong Bộ chuẩn; Bộ chuẩn chưa có Trích dẫn nào thì bỏ qua.
"""

from pathlib import Path

import pytest

from thamdinh.bo_chuan import BoChuanError, doc_trich_dan_chuan
from thamdinh.checklist import load_checklist
from thamdinh.llm import LocalClient
from thamdinh.settings import load_settings
from thamdinh.so_hoa import so_hoa
from thamdinh.truy_xuat import LocalEmbeddingClient, chuan_bi_truy_xuat, do_phu_ngu_canh

pytestmark = pytest.mark.llm

GOC = Path(__file__).parent.parent
TOSS = next((GOC / "Sample").glob("*TOSS*.pdf"))
CHECKLIST = load_checklist(GOC / "checklists" / "dau-ra-v1.1.yaml")
BO_CHUAN = GOC / "eval" / "chuan" / "toss.yaml"


@pytest.fixture(scope="module")
def settings():
    return load_settings()


@pytest.fixture(scope="module")
def van_ban(settings):
    return so_hoa(TOSS, thu_muc_luu=settings.data_dir)


@pytest.fixture(scope="module")
def truy_xuat(settings, van_ban):
    llm = LocalClient(settings.local_url, settings.model, suy_luan=settings.suy_luan)
    tx = chuan_bi_truy_xuat(
        van_ban, CHECKLIST, llm, LocalEmbeddingClient(settings.embedding_url, settings.embedding_model),
        settings.ngan_sach_truy_xuat, model=settings.model, thu_muc_luu=settings.data_dir, tien_trinh=print,
        dem_token=llm.dem_token,
    )
    for c in tx.canh_bao:
        print("Cảnh báo:", c)
    return tx


def test_bang_ngu_canh_tung_muc_khong_vuot_ngan_sach(truy_xuat, settings):
    print(f"\n{'Mục':>3} {'token':>6} / {settings.ngan_sach_truy_xuat}  {'Điều khoản':>10}  bị bỏ")
    for m in CHECKLIST.muc:
        nc = truy_xuat.ngu_canh(m)
        print(f"{m.so:>3} {nc.so_token:>6}          {len(nc.dieu_khoan):>10}  {', '.join(nc.bo_qua)}")
        assert nc.so_token <= settings.ngan_sach_truy_xuat


def test_moi_trich_dan_bo_chuan_nam_trong_ngu_canh_cua_muc(truy_xuat, van_ban):
    """Model có được đọc những câu người thẩm định dựa vào (eval/chuan/toss.yaml) không. Chung cho mọi Hợp đồng có Bộ chuẩn."""
    try:
        trich_dan_chuan = doc_trich_dan_chuan(BO_CHUAN)
    except BoChuanError as e:
        pytest.fail(f"Chưa đọc được Bộ chuẩn {BO_CHUAN.name}: {e.loi}")
    if not trich_dan_chuan:
        pytest.skip("Bộ chuẩn chưa có Trích dẫn nào")

    do_phu = do_phu_ngu_canh(trich_dan_chuan, CHECKLIST, van_ban, truy_xuat.ngu_canh)

    tinh = [d for d in do_phu if d.trang_thai != "khong_co_trong_van_ban"]
    print(f"\nĐộ phủ: {sum(d.trang_thai == 'co' for d in tinh)}/{len(tinh)} Trích dẫn của Bộ chuẩn nằm trong ngữ cảnh")
    for d in do_phu:
        if d.trang_thai != "co":
            print(f"  {d.ma} ({d.trang_thai}): {d.nguyen_van[:100]}")
    assert all(d.trang_thai == "co" for d in tinh), [d.ma for d in tinh if d.trang_thai != "co"]
