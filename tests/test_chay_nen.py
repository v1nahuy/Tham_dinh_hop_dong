"""Chạy Lượt thẩm định ở tiến trình nền, mỗi lúc một Lượt (issue 11, Q76)."""

from pathlib import Path

import pytest

from thamdinh.chay_nen import DangChayError, dung, khoi_chay, trang_thai


class TienTrinhGia:
    """Thay cho subprocess.Popen: ghi lại lệnh, viết sẵn nhật ký như script thật."""

    def __init__(self, nhat_ky_viet=""):
        self.lenh = []
        self.nhat_ky_viet = nhat_ky_viet
        self.song = set()

    def popen(self, lenh, stdout, **_):
        self.lenh.append(lenh)
        stdout.write(self.nhat_ky_viet.encode("utf-8"))
        pid = 4000 + len(self.lenh)
        self.song.add(pid)
        return type("P", (), {"pid": pid})()

    def con_song(self, pid):
        return pid in self.song

    def ket_thuc(self, pid):
        self.song.discard(pid)


@pytest.fixture
def tien_trinh():
    return TienTrinhGia("[  0.0 phút] Xác định các bên\nMã Lượt: abc-20261030T101500\n[ 12.5 phút] Mục 1\n")


def test_chua_chay_lan_nao(tmp_path, tien_trinh):
    assert trang_thai(tmp_path, con_song=tien_trinh.con_song) is None


def test_khoi_chay_script_tham_dinh_voi_doi_so(tmp_path, tien_trinh):
    khoi_chay(["data/pdf/abc.pdf", "--che-do", "toan_van"], tmp_path, popen=tien_trinh.popen,
              con_song=tien_trinh.con_song)

    lenh = tien_trinh.lenh[0]
    assert Path(lenh[-4]).name == "chay_tham_dinh.py"
    assert lenh[-3:] == ["data/pdf/abc.pdf", "--che-do", "toan_van"]


def test_trang_thai_dang_chay_kem_ma_luot_va_dong_cuoi_nhat_ky(tmp_path, tien_trinh):
    khoi_chay(["x.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)

    tt = trang_thai(tmp_path, con_song=tien_trinh.con_song)

    assert tt.dang_chay
    assert tt.ma_luot == "abc-20261030T101500"
    assert tt.dong_cuoi[-1] == "[ 12.5 phút] Mục 1"
    assert tt.nhat_ky.parent == tmp_path / "nhat-ky"


def test_moi_luc_chi_mot_luot(tmp_path, tien_trinh):
    khoi_chay(["x.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)

    with pytest.raises(DangChayError):
        khoi_chay(["y.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)
    assert len(tien_trinh.lenh) == 1


def test_luot_truoc_da_xong_thi_chay_duoc_luot_moi(tmp_path, tien_trinh):
    khoi_chay(["x.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)
    tien_trinh.song.clear()  # tiến trình đã thoát

    assert not trang_thai(tmp_path, con_song=tien_trinh.con_song).dang_chay
    khoi_chay(["y.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)
    assert len(tien_trinh.lenh) == 2


def test_dung_luot_dang_chay(tmp_path, tien_trinh):
    khoi_chay(["x.pdf"], tmp_path, popen=tien_trinh.popen, con_song=tien_trinh.con_song)

    dung(tmp_path, con_song=tien_trinh.con_song, ket_thuc=tien_trinh.ket_thuc)

    assert not trang_thai(tmp_path, con_song=tien_trinh.con_song).dang_chay
