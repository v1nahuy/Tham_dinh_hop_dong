from pathlib import Path

import pytest
import yaml

from thamdinh.bo_chuan import BoChuanError, doc_trich_dan_chuan, nap_bo_chuan, tao_mau_bo_chuan
from thamdinh.checklist import load_checklist

GOC = Path(__file__).parent.parent
CHECKLIST = GOC / "checklists" / "dau-ra-v1.1.yaml"
TOSS = next((GOC / "Sample").glob("*TOSS*.pdf"))


@pytest.fixture(scope="module")
def checklist():
    return load_checklist(CHECKLIST)


@pytest.fixture(scope="module")
def mau():
    return tao_mau_bo_chuan(CHECKLIST, TOSS)


def dien_du(mau: str) -> dict:
    """Điền mọi ô bắt buộc của file mẫu như người dùng sẽ làm."""
    d = yaml.safe_load(mau)
    for m in d["muc"]:
        m["ket_qua"] = "luu_y"
        for t in m["tieu_chi"]:
            t["danh_gia"] = "thoa"
            if "gia_tri" in t:
                t["gia_tri"] = 39820000000
            t["trich_dan"] = "Trong vòng 15 ngày kể từ ngày ký kết hợp đồng."
            t["vi_tri"] = "4.3.1, trang 3"
    return d


def viet(tmp_path, d) -> Path:
    file = tmp_path / "toss.yaml"
    file.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return file


def loi_khi_nap(file, checklist, **kw) -> list[str]:
    with pytest.raises(BoChuanError) as e:
        nap_bo_chuan(file, checklist, **kw)
    return e.value.loi


def test_nap_mot_phan_chi_lay_tieu_chi_da_dien(tmp_path, mau, checklist):
    d = yaml.safe_load(mau)
    d["muc"][0]["tieu_chi"][0]["danh_gia"] = "thoa"
    d["muc"][0]["ket_qua"] = "dat"

    bo = nap_bo_chuan(viet(tmp_path, d), checklist, mot_phan=True)

    assert set(bo.danh_gia) == {"1.D1"}
    assert bo.ket_qua_muc[1] == "dat"


def test_nap_mot_phan_van_bao_gia_tri_dien_sai(tmp_path, mau, checklist):
    d = yaml.safe_load(mau)
    t = next(t for t in d["muc"][0]["tieu_chi"] if t["ma"] == "1.V2")
    t["danh_gia"], t["gia_tri"] = "khong_thoa", "39.820.000.000"

    with pytest.raises(BoChuanError, match="39820000000"):
        nap_bo_chuan(viet(tmp_path, d), checklist, mot_phan=True)


def test_file_mau_co_du_tieu_chi_va_doc_duoc(mau, checklist):
    d = yaml.safe_load(mau)
    ma = [t["ma"] for m in d["muc"] for t in m["tieu_chi"]]
    assert ma == [tc.ma for m in checklist.muc for ds in m.tieu_chi.values() for tc in ds]
    co_gia_tri = {t["ma"] for m in d["muc"] for t in m["tieu_chi"] if "gia_tri" in t}
    assert {"1.V2", "7.D1", "10.L1"} <= co_gia_tri


def test_nap_bo_chuan_da_dien_du(tmp_path, mau, checklist):
    d = dien_du(mau)
    d["muc"][0]["tieu_chi"][0]["trich_dan"] = ["Câu một.", "Câu hai."]

    bo = nap_bo_chuan(viet(tmp_path, d), checklist, pdf=TOSS)

    assert len(bo.danh_gia) == 122
    assert bo.danh_gia["1.V2"].gia_tri == 39820000000
    assert bo.danh_gia["1.D1"].trich_dan == ("Câu một.", "Câu hai.")
    assert bo.danh_gia["7.D2"].trich_dan == ("Trong vòng 15 ngày kể từ ngày ký kết hợp đồng.",)
    assert bo.ket_qua_muc[7] == "luu_y"


def test_file_mau_chua_dien_bao_tung_tieu_chi(tmp_path, mau, checklist):
    file = tmp_path / "toss.yaml"
    file.write_text(mau, encoding="utf-8")

    loi = loi_khi_nap(file, checklist)

    assert "Mục 1, tiêu chí 1.D1: chưa điền danh_gia" in loi
    assert sum("chưa điền danh_gia" in l for l in loi) == 122
    # ket_qua của Mục không bắt buộc
    assert not any("ket_qua" in l for l in loi)


@pytest.mark.parametrize(
    "sua, thong_bao",
    [
        (lambda d: d["muc"][6]["tieu_chi"][0].update(danh_gia="dat"),
         "Mục 7, tiêu chí 7.D1: danh_gia 'dat' không hợp lệ, phải là thoa | khong_thoa | khong_ro"),
        (lambda d: d["muc"][6]["tieu_chi"][0].update(gia_tri="8%"),
         "Mục 7, tiêu chí 7.D1: gia_tri '8%' phải là số"),
        (lambda d: d["muc"][6].update(ket_qua="dạt"),
         "Mục 7: ket_qua 'dạt' không hợp lệ, phải là dat | luu_y | vi_pham"),
        (lambda d: d["muc"][6]["tieu_chi"].pop(1),
         "Mục 7: thiếu tiêu chí 7.D2"),
        (lambda d: d["muc"][6]["tieu_chi"].append({"ma": "7.X9", "danh_gia": "thoa"}),
         "Mục 7: tiêu chí 7.X9 không có trong checklist"),
        (lambda d: d["muc"].pop(),
         "Thiếu Mục 17"),
        (lambda d: d.update(checklist="dau-ra 1.0"),
         "File điền cho checklist 'dau-ra 1.0', nhưng đang kiểm tra với 'dau-ra 1.1'"),
    ],
)
def test_bao_loi_chi_ro_vi_tri(tmp_path, mau, checklist, sua, thong_bao):
    d = dien_du(mau)
    sua(d)

    assert thong_bao in loi_khi_nap(viet(tmp_path, d), checklist)


def test_bao_loi_khi_hash_pdf_khong_khop(tmp_path, mau, checklist):
    d = dien_du(mau)
    d["hash_pdf"] = "abc"

    loi = loi_khi_nap(viet(tmp_path, d), checklist, pdf=TOSS)

    assert any("hash_pdf không khớp" in l for l in loi)


def test_loi_cu_phap_yaml_bao_dong_cot_thay_vi_crash(tmp_path, mau, checklist):
    # Người điền tay hay gõ phím Tab ở cuối dòng (eval/chuan/toss.yaml dòng 45)
    file = viet(tmp_path, dien_du(mau))
    dong = file.read_text(encoding="utf-8").splitlines()
    dong[5] += "\t"
    file.write_text("\n".join(dong), encoding="utf-8")
    dong[5] = dong[5].rstrip("\t") + ": :"  # lỗi cú pháp khác
    file2 = tmp_path / "toss2.yaml"
    file2.write_text("\n".join(dong), encoding="utf-8")

    loi = loi_khi_nap(file, checklist)

    assert len(loi) == 1 and "dòng 6" in loi[0] and "Tab" in loi[0]
    assert "dòng 6" in loi_khi_nap(file2, checklist)[0]


def test_gia_tri_co_dau_cham_phan_cach_thi_huong_dan_cach_ghi(tmp_path, mau, checklist):
    d = dien_du(mau)
    tc = next(t for m in d["muc"] for t in m["tieu_chi"] if "gia_tri" in t)
    tc["gia_tri"] = "39.820.000.000"

    loi = loi_khi_nap(viet(tmp_path, d), checklist)

    assert any("39820000000" in l and "dấu chấm" in l for l in loi)


def test_doc_trich_dan_chuan_khi_bo_chuan_chua_dien_xong(tmp_path, mau):
    d = yaml.safe_load(mau)  # chưa điền danh_gia: nap_bo_chuan sẽ báo lỗi, nhưng trích dẫn vẫn đọc được
    tc = [t for m in d["muc"] for t in m["tieu_chi"]]
    tc[0]["trich_dan"] = "Trong vòng 15 ngày kể từ ngày ký kết hợp đồng."
    tc[1]["trich_dan"] = ["Câu thứ nhất.", "", "Câu thứ hai."]

    kq = doc_trich_dan_chuan(viet(tmp_path, d))

    assert kq == {tc[0]["ma"]: ("Trong vòng 15 ngày kể từ ngày ký kết hợp đồng.",), tc[1]["ma"]: ("Câu thứ nhất.", "Câu thứ hai.")}


def test_doc_trich_dan_chuan_bao_loi_cu_phap(tmp_path, mau):
    file = viet(tmp_path, yaml.safe_load(mau))
    file.write_text(file.read_text(encoding="utf-8").replace("muc:", "muc:\t", 1), encoding="utf-8")

    with pytest.raises(BoChuanError, match="cú pháp YAML"):
        doc_trich_dan_chuan(file)
