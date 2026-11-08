import json

import httpx
import pytest

from thamdinh.llm import LLMKetNoiError
from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.truy_xuat import BoTimBM25, BoTimNhung, LocalEmbeddingClient, tach_tu, tao_bo_tim_kiem


def dk(ma, so_hieu, noi_dung):
    return DieuKhoan(ma, so_hieu, "khoan", None, None, 1, 1, noi_dung)


VAN_BAN = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ.pdf",
    trang=[TrangSoHoa(1, "lop_text", False, ())],
    dieu_khoan=[
        dk(0, "4.1", "Bên A thanh toán cho Bên B trong vòng 30 ngày kể từ ngày nghiệm thu."),
        dk(1, "10.1", "Mức phạt vi phạm hợp đồng không vượt quá 8% giá trị phần nghĩa vụ bị vi phạm."),
        dk(2, "10.2", "Bên vi phạm phải bồi thường toàn bộ thiệt hại thực tế phát sinh."),
        dk(3, "7.3", "Bên B đồng ý hỗ trợ kỹ thuật cho hợp phần đào tạo; các bên ký biên bản."),
        dk(4, "12.1", "Bên A được đơn phương chấm dứt [xóa: phạt vi phạm ]khi Bên B vi phạm nghiêm trọng."),
    ],
    canh_bao=[],
)


def test_tach_tu_theo_am_tiet_va_cap_am_tiet():
    assert tach_tu("Mức PHẠT, vi phạm.") == ["mức", "phạt", "vi", "phạm", "mức phạt", "phạt vi", "vi phạm"]


def test_bm25_xep_dieu_khoan_lien_quan_len_dau():
    tim = BoTimBM25(VAN_BAN)

    assert tim.tim("Mức phạt vi phạm cao nhất")[0] == 1
    assert tim.tim("bồi thường thiệt hại")[0] == 2
    assert sorted(tim.tim("thanh toán")) == [0, 1, 2, 3, 4]  # luôn trả mọi Điều khoản


def test_bm25_cap_am_tiet_phan_biet_hop_dong_voi_hop_phan_dong_y():
    # 7.3 có "hợp" và "đồng" rời nhau ("hợp phần", "đồng ý"); 10.1 có cụm "hợp đồng"
    assert BoTimBM25(VAN_BAN).tim("hợp đồng")[0] == 1


def test_bm25_bo_chu_da_xoa():
    # "bảo lãnh" chỉ có trong [xóa: …] của 12.1: không Điều khoản nào khớp, giữ thứ tự Hợp đồng
    van_ban = VanBanHieuLuc(**{**VAN_BAN.__dict__, "dieu_khoan": [
        *VAN_BAN.dieu_khoan[:4], dk(4, "12.1", "Bên A được chấm dứt [xóa: và tịch thu bảo lãnh ]khi Bên B vi phạm.")]})

    assert BoTimBM25(van_ban).tim("bảo lãnh")[0] == 0


class NhungGia:
    """Embedding giả: vector đếm vài từ khóa."""

    TU = ["thanh toán", "phạt", "bồi thường", "chấm dứt"]

    def __init__(self):
        self.goi = []

    def nhung(self, van_ban):
        self.goi.append(list(van_ban))
        return [[float(t.lower().count(tu)) + 0.01 for tu in self.TU] for t in van_ban]


def test_bo_tim_nhung_xep_theo_do_tuong_dong_cosine():
    nhung = NhungGia()
    tim = BoTimNhung(VAN_BAN, nhung)

    assert tim.tim("bồi thường")[0] == 2
    assert tim.tim("chấm dứt hợp đồng")[0] == 4
    assert len(nhung.goi) == 3  # Điều khoản chỉ nhúng một lần


def test_dieu_khoan_dai_duoc_chia_doan_khi_nhung():
    dai = VanBanHieuLuc(**{**VAN_BAN.__dict__, "dieu_khoan": [
        dk(0, "PL02", "Yêu cầu kỹ thuật chung. " * 2000 + "Bồi thường khi vi phạm SLA."), *VAN_BAN.dieu_khoan[1:]]})
    nhung = NhungGia()

    tim = BoTimNhung(dai, nhung, toi_da_token_doan=1000)

    doan = nhung.goi[0]
    assert len(doan) > len(dai.dieu_khoan) and max(len(d) for d in doan) <= 1000 * 2.5
    assert tim.tim("bồi thường")[0] in (0, 2)  # điểm của Điều khoản dài = đoạn giống nhất


def may_chu(xu_ly):
    return httpx.Client(transport=httpx.MockTransport(xu_ly))


def test_local_embedding_client_goi_api_chuan_openai():
    ghi_lai = []

    def xu_ly(request):
        ghi_lai.append(request)
        n = len(json.loads(request.content)["input"])
        return httpx.Response(200, json={"data": [{"index": i, "embedding": [i, 1.0]} for i in reversed(range(n))]})

    kq = LocalEmbeddingClient("http://127.0.0.1:8081/v1", "bge-m3", http=may_chu(xu_ly)).nhung(["a", "b"])

    body = json.loads(ghi_lai[0].content)
    assert str(ghi_lai[0].url) == "http://127.0.0.1:8081/v1/embeddings"
    assert body == {"model": "bge-m3", "input": ["a", "b"]}
    assert kq == [[0, 1.0], [1, 1.0]]  # xếp lại theo index


def test_chua_chay_may_chu_embedding_thi_chi_dung_bm25_va_canh_bao():
    def xu_ly(request):
        raise httpx.ConnectError("refused")

    nhung = LocalEmbeddingClient("http://127.0.0.1:8081/v1", "bge-m3", http=may_chu(xu_ly))
    with pytest.raises(LLMKetNoiError):
        nhung.nhung(["a"])

    bo, canh_bao = tao_bo_tim_kiem(VAN_BAN, nhung)

    assert [type(b) for b in bo] == [BoTimBM25]
    assert any("chỉ dùng BM25" in c for c in canh_bao)


def test_co_may_chu_embedding_thi_dung_ca_hai():
    bo, canh_bao = tao_bo_tim_kiem(VAN_BAN, NhungGia())

    assert [type(b) for b in bo] == [BoTimBM25, BoTimNhung] and canh_bao == []
