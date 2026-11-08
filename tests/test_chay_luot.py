"""Script chạy Lượt (tiến trình nền của giao diện): chạy lại phần lỗi chỉ gửi Mục lỗi tới model (issue 11)."""

import re
from pathlib import Path

import pytest
from test_tham_dinh import ModelGia

from thamdinh.chay_luot import chay_luot
from thamdinh.kho_luot import KhoLuot
from thamdinh.settings import load_settings

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))
CHECKLIST = str(Path(__file__).parent.parent / "checklists" / "dau-ra-v1.1.yaml")


@pytest.fixture
def settings(tmp_path):
    return load_settings(env={"THAMDINH_DATA_DIR": str(tmp_path)})


def muc_da_gui(model: ModelGia) -> list[int]:
    return [int(m) for p in model.prompt for m in re.findall(r"MỤC CHECKLIST (\d+):", p)]


def test_in_ma_luot_ngay_khi_luu_lan_dau(settings):
    dong = []
    kq = chay_luot(TOSS, checklist=CHECKLIST, settings=settings, llm=ModelGia(), in_ra=dong.append)

    assert dong.count(f"Mã Lượt: {kq.ma}") == 1
    assert dong.index(f"Mã Lượt: {kq.ma}") < next(i for i, d in enumerate(dong) if "Mục 1" in d)


def test_chay_lai_phan_loi_chi_gui_muc_loi_roi_du_17_muc(settings):
    truoc = chay_luot(TOSS, checklist=CHECKLIST, settings=settings, llm=ModelGia(loi_muc={7: 2}), in_ra=lambda _: None)
    assert next(m for m in truoc.muc if m.so == 7).ket_qua is None

    model = ModelGia()
    sau = chay_luot(TOSS, checklist=CHECKLIST, settings=settings, llm=model, tiep_tuc=truoc.ma, in_ra=lambda _: None)

    assert set(muc_da_gui(model)) == {7}
    assert sau.ma == truoc.ma
    assert all(m.ket_qua is not None for m in KhoLuot(settings.data_dir).nap(sau.ma).muc)
    assert len(sau.muc) == 17


def test_chon_them_muc_da_co_ket_qua_thi_tao_luot_moi(settings):
    truoc = chay_luot(TOSS, checklist=CHECKLIST, settings=settings, llm=ModelGia(), in_ra=lambda _: None)

    model = ModelGia()
    sau = chay_luot(TOSS, checklist=CHECKLIST, settings=settings, llm=model, tiep_tuc=truoc.ma, chi_muc={14},
                    in_ra=lambda _: None)

    assert set(muc_da_gui(model)) == {14}
    assert sau.ma != truoc.ma and sau.luot_goc == truoc.ma
