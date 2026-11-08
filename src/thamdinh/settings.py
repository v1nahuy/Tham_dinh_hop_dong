import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_MODEL = "qwen3.5"
DEFAULT_LOCAL_URL = "http://127.0.0.1:8080/v1"
DEFAULT_NGU_CANH = 65536
DEFAULT_DATA_DIR = "data"
DEFAULT_NGAN_SACH_TRUY_XUAT = 16000
DEFAULT_EMBEDDING_URL = "http://127.0.0.1:8081/v1"
DEFAULT_EMBEDDING_MODEL = "bge-m3"
DEFAULT_OCR_MODEL = "vgg_transformer"
DEFAULT_OCR_MODEL_DIR = "models/vietocr"


@dataclass(frozen=True)
class Settings:
    model: str  # tên model gửi tới máy chủ llama.cpp
    local_url: str  # API chuẩn OpenAI của llama-server, chỉ nghe trên máy
    ngu_canh: int  # số token ngữ cảnh tối đa, phải khớp tham số -c của llama-server
    suy_luan: bool  # bật chế độ suy luận (thinking) của Qwen3.5
    data_dir: Path
    ngan_sach_truy_xuat: int = DEFAULT_NGAN_SACH_TRUY_XUAT  # token văn bản mỗi Mục ở chế độ truy xuất
    embedding_url: str = DEFAULT_EMBEDDING_URL  # llama-server --embedding chạy bge-m3
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    ocr_model: str = DEFAULT_OCR_MODEL  # VietOCR: vgg_transformer (chính xác hơn) | vgg_seq2seq (nhanh hơn khoảng 4 lần)
    thu_muc_model_ocr: Path = Path(DEFAULT_OCR_MODEL_DIR)  # chứa base.yml, <model>.yml và <model>.pth
    nguoi_duyet: str = ""  # tên ghi vào Kết quả đã duyệt; trống thì nhập trên trang Kết quả


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Đọc cấu hình từ biến môi trường; mặc định nạp `.env` rồi dùng `os.environ`."""
    if env is None:
        load_dotenv()
        env = os.environ
    return Settings(
        model=env.get("THAMDINH_MODEL") or DEFAULT_MODEL,
        local_url=env.get("THAMDINH_LOCAL_URL") or DEFAULT_LOCAL_URL,
        ngu_canh=int(env.get("THAMDINH_NGU_CANH") or DEFAULT_NGU_CANH),
        suy_luan=(env.get("THAMDINH_SUY_LUAN") or "").strip().lower() in ("1", "true", "yes", "co"),
        data_dir=Path(env.get("THAMDINH_DATA_DIR") or DEFAULT_DATA_DIR),
        ngan_sach_truy_xuat=int(env.get("THAMDINH_NGAN_SACH_TRUY_XUAT") or DEFAULT_NGAN_SACH_TRUY_XUAT),
        embedding_url=env.get("THAMDINH_EMBEDDING_URL") or DEFAULT_EMBEDDING_URL,
        embedding_model=env.get("THAMDINH_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL,
        ocr_model=env.get("THAMDINH_OCR_MODEL") or DEFAULT_OCR_MODEL,
        thu_muc_model_ocr=Path(env.get("THAMDINH_OCR_MODEL_DIR") or DEFAULT_OCR_MODEL_DIR),
        nguoi_duyet=(env.get("THAMDINH_NGUOI_DUYET") or "").strip(),
    )
