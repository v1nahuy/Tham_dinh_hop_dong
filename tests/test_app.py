from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


@pytest.fixture(autouse=True)
def kho_rong(tmp_path, monkeypatch):
    # Không đọc data/ thật: trang Kết quả dựng báo cáo của Lượt mới nhất trong kho, chậm dần khi kho lớn lên
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))


def test_app_khoi_dong_o_buoc_so_hoa():
    at = AppTest.from_file(APP, default_timeout=30).run()

    assert not at.exception
    assert at.title[0].value == "Số hóa"


@pytest.mark.parametrize(
    "page, title",
    [("ui/so_hoa.py", "Số hóa"), ("ui/tham_dinh.py", "Thẩm định"), ("ui/ket_qua.py", "Kết quả")],
)
def test_moi_buoc_deu_mo_duoc(page, title):
    at = AppTest.from_file(APP, default_timeout=30).run()

    at.switch_page(page).run()

    assert not at.exception
    assert at.title[0].value == title
