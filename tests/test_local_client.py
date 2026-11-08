import json

import httpx
import pytest

from thamdinh.llm import LLMBiCatError, LLMKetNoiError, LLMResponseError, LocalClient

SCHEMA = {
    "type": "object",
    "properties": {"ket_qua": {"enum": ["thoa", "khong_thoa"]}},
    "required": ["ket_qua"],
    "additionalProperties": False,
}


def may_chu_gia(noi_dung: str, ghi_lai: list):
    """Thay cho llama-server: trả về `noi_dung` như model trả lời, và ghi lại request."""

    def xu_ly(request: httpx.Request) -> httpx.Response:
        ghi_lai.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": noi_dung}}]})

    return httpx.Client(transport=httpx.MockTransport(xu_ly))


def client(noi_dung: str, ghi_lai: list | None = None, **kw) -> LocalClient:
    ghi_lai = [] if ghi_lai is None else ghi_lai
    return LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=may_chu_gia(noi_dung, ghi_lai), **kw)


def test_tra_ve_json_hop_le():
    assert client('{"ket_qua": "thoa"}').complete_json("Hỏi?", SCHEMA) == {"ket_qua": "thoa"}


def test_gui_prompt_va_ep_json_schema_tat_suy_luan():
    ghi_lai = []
    client('{"ket_qua": "thoa"}', ghi_lai).complete_json("Hỏi?", SCHEMA)

    request = ghi_lai[0]
    body = json.loads(request.content)
    assert str(request.url) == "http://127.0.0.1:8080/v1/chat/completions"
    assert body["model"] == "qwen3.5"
    assert body["messages"] == [{"role": "user", "content": "Hỏi?"}]
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["schema"] == SCHEMA
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_bat_suy_luan_theo_cau_hinh():
    ghi_lai = []
    client('{"ket_qua": "thoa"}', ghi_lai, suy_luan=True).complete_json("Hỏi?", SCHEMA)

    assert json.loads(ghi_lai[0].content)["chat_template_kwargs"] == {"enable_thinking": True}


def test_bo_khoi_suy_luan_neu_model_van_tra_ve():
    noi_dung = '<think>\nĐiều 10 quy định phạt 8%...\n</think>\n\n{"ket_qua": "khong_thoa"}'

    assert client(noi_dung).complete_json("Hỏi?", SCHEMA) == {"ket_qua": "khong_thoa"}


@pytest.mark.parametrize(
    "noi_dung, thong_bao",
    [
        ("Tôi nghĩ là thỏa.", "không phải JSON"),
        ('{"ket_qua": "co_le"}', "sai schema"),
    ],
)
def test_json_sai_bao_loi(noi_dung, thong_bao):
    with pytest.raises(LLMResponseError, match=thong_bao):
        client(noi_dung).complete_json("Hỏi?", SCHEMA)


def test_chua_chay_may_chu_model_bao_loi_de_hieu():
    def tu_choi(request):
        raise httpx.ConnectError("connection refused", request=request)

    c = LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=httpx.Client(transport=httpx.MockTransport(tu_choi)))

    with pytest.raises(LLMKetNoiError, match="Chưa chạy máy chủ model tại http://127.0.0.1:8080/v1"):
        c.complete_json("Hỏi?", SCHEMA)


def test_gioi_han_do_dai_cau_tra_loi():
    # Model nhỏ có lúc sinh lặp không dừng đến hết ngữ cảnh (Mục 14 TOSS: ~20k token, ~3 giờ trên CPU)
    ghi_lai = []
    client('{"ket_qua": "thoa"}', ghi_lai, toi_da_token=4096).complete_json("Hỏi?", SCHEMA)

    assert json.loads(ghi_lai[0].content)["max_tokens"] == 4096


def test_cau_tra_loi_bi_cat_bao_loi_ro_rang():
    def xu_ly(request):
        return httpx.Response(200, json={"choices": [{"finish_reason": "length", "message": {"content": '{"ket_qua": "th'}}]})

    c = LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=httpx.Client(transport=httpx.MockTransport(xu_ly)))

    with pytest.raises(LLMBiCatError, match="bị cắt") as loi:
        c.complete_json("Hỏi?", SCHEMA)
    assert isinstance(loi.value, LLMResponseError)


def test_dem_token_bang_tokenize_cua_llama_server():
    ghi_lai = []

    def xu_ly(request):
        ghi_lai.append(request)
        return httpx.Response(200, json={"tokens": [1, 2, 3, 4]})

    c = LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=httpx.Client(transport=httpx.MockTransport(xu_ly)))

    assert c.dem_token("Điều 10") == 4
    assert str(ghi_lai[0].url) == "http://127.0.0.1:8080/tokenize"  # không nằm dưới /v1
    assert json.loads(ghi_lai[0].content) == {"content": "Điều 10"}


def test_dem_token_khi_chua_chay_may_chu():
    def xu_ly(request):
        raise httpx.ConnectError("refused")

    c = LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=httpx.Client(transport=httpx.MockTransport(xu_ly)))

    with pytest.raises(LLMKetNoiError):
        c.dem_token("Điều 10")


@pytest.mark.parametrize(
    "tra_loi, san_sang",
    [
        (lambda r: httpx.Response(200, json={"status": "ok"}), True),
        (lambda r: httpx.Response(503, json={"error": {"message": "Loading model"}}), False),  # đang nạp model
        (lambda r: (_ for _ in ()).throw(httpx.ConnectError("refused")), False),  # chưa chạy
    ],
)
def test_kiem_tra_may_chu_san_sang_truoc_khi_chay(tra_loi, san_sang):
    ghi_lai = []

    def xu_ly(request):
        ghi_lai.append(request)
        return tra_loi(request)

    c = LocalClient("http://127.0.0.1:8080/v1", "qwen3.5", http=httpx.Client(transport=httpx.MockTransport(xu_ly)))

    assert c.san_sang() is san_sang
    assert str(ghi_lai[0].url) == "http://127.0.0.1:8080/health"


def test_kiem_tra_may_chu_embedding_san_sang():
    from thamdinh.truy_xuat import LocalEmbeddingClient

    ghi_lai = []

    def xu_ly(request):
        ghi_lai.append(request)
        return httpx.Response(200, json={"status": "ok"})

    c = LocalEmbeddingClient("http://127.0.0.1:8081/v1", "bge-m3", http=httpx.Client(transport=httpx.MockTransport(xu_ly)))

    assert c.san_sang()
    assert str(ghi_lai[0].url) == "http://127.0.0.1:8081/health"
