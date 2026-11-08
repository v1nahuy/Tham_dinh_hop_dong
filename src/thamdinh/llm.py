"""Lớp trung gian gọi mô hình ngôn ngữ (ADR 0001).

Luồng thẩm định chỉ phụ thuộc vào `LLMClient`; `LocalClient` gọi model chạy trên máy (Qwen3.5 qua
llama.cpp), nên dữ liệu Hợp đồng không rời khỏi máy.
"""

import json
import re
from typing import Any, Protocol

import httpx
import jsonschema


class LLMResponseError(Exception):
    """Phản hồi của mô hình không phải JSON hợp lệ theo schema yêu cầu."""


class LLMBiCatError(LLMResponseError):
    """Câu trả lời bị cắt vì chạm giới hạn token (model nhỏ có lúc sinh lặp không dừng)."""


class LLMKetNoiError(Exception):
    """Không gọi được máy chủ model (chưa chạy llama-server, sai địa chỉ...)."""


class LLMClient(Protocol):
    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


class LocalClient:
    """Gọi model chạy trên máy qua API chuẩn OpenAI của llama.cpp `llama-server`.

    JSON schema được gửi trong `response_format` để llama-server ép model sinh đúng schema.
    Prompt chỉ gồm một tin nhắn `user`; người gọi giữ phần đầu prompt cố định để llama-server
    dùng lại bộ nhớ đệm của phần đã đọc (văn bản Hợp đồng) giữa các lần gọi.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        suy_luan: bool = False,
        toi_da_token: int = 4096,
        http: httpx.Client | None = None,
        timeout: float = 4 * 3600,
    ):
        self._url = base_url.rstrip("/")
        self._model = model
        self._suy_luan = suy_luan
        self._toi_da_token = toi_da_token
        self._http = http or httpx.Client(timeout=httpx.Timeout(timeout, connect=10.0))

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": self._toi_da_token,
            "response_format": {"type": "json_schema", "json_schema": {"name": "ket_qua", "schema": schema}},
            "chat_template_kwargs": {"enable_thinking": self._suy_luan},
            "cache_prompt": True,
        }
        try:
            response = self._http.post(f"{self._url}/chat/completions", json=body)
        except httpx.ConnectError as e:
            raise LLMKetNoiError(
                f"Chưa chạy máy chủ model tại {self._url}. Hãy khởi động llama-server (xem docs/chay-model-local.md) rồi chạy lại."
            ) from e
        response.raise_for_status()
        lua_chon = response.json()["choices"][0]
        text = lua_chon["message"]["content"] or ""
        if lua_chon.get("finish_reason") == "length":
            raise LLMBiCatError(
                f"Câu trả lời bị cắt vì vượt {self._toi_da_token} token (model có thể đã sinh lặp)\n---\n{text[-300:]}"
            )
        return _parse_json(_SUY_LUAN.sub("", text), schema)

    def san_sang(self) -> bool:
        """Máy chủ model đã chạy và nạp xong model chưa."""
        return may_chu_san_sang(self._url, self._http)

    def dem_token(self, van_ban: str) -> int:
        """Số token theo tokenizer của model (`/tokenize` của llama-server, nằm ngoài `/v1`)."""
        goc = self._url.removesuffix("/v1")
        try:
            response = self._http.post(f"{goc}/tokenize", json={"content": van_ban})
        except httpx.ConnectError as e:
            raise LLMKetNoiError(f"Chưa chạy máy chủ model tại {goc}, không đếm được token.") from e
        response.raise_for_status()
        return len(response.json()["tokens"])


_SUY_LUAN = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCED_JSON = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _parse_json(text: str, schema: dict[str, Any]) -> dict[str, Any]:
    fenced = _FENCED_JSON.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMResponseError(f"Phản hồi không phải JSON: {e}\n---\n{text[:500]}") from e
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        path = "/".join(str(p) for p in e.absolute_path) or "(gốc)"
        raise LLMResponseError(f"JSON sai schema tại {path}: {e.message}") from e
    return data


def may_chu_san_sang(base_url: str, http: httpx.Client) -> bool:
    """`GET /health` của llama-server: 200 khi sẵn sàng, 503 khi đang nạp model; không kết nối được là chưa chạy."""
    try:
        return http.get(f"{base_url.rstrip('/').removesuffix('/v1')}/health", timeout=5).status_code == 200
    except httpx.HTTPError:
        return False
