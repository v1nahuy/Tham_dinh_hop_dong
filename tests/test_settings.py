from pathlib import Path

from thamdinh.settings import load_settings


def test_mac_dinh_khi_khong_co_bien_moi_truong():
    settings = load_settings(env={})

    assert settings.model == "qwen3.5"
    assert settings.local_url == "http://127.0.0.1:8080/v1"
    assert settings.ngu_canh == 65536
    assert settings.suy_luan is False
    assert settings.data_dir == Path("data")
    assert settings.ngan_sach_truy_xuat == 16000
    assert settings.toi_da_token == 4096
    assert settings.moi_tieu_chi_mot_lan is False
    assert settings.embedding_url == "http://127.0.0.1:8081/v1"
    assert settings.embedding_model == "bge-m3"
    assert settings.ocr_model == "vgg_transformer"
    assert settings.thu_muc_model_ocr == Path("models/vietocr")
    assert settings.nguoi_duyet == ""


def test_bien_moi_truong_ghi_de_mac_dinh():
    settings = load_settings(
        env={
            "THAMDINH_MODEL": "qwen3.5-4b",
            "THAMDINH_LOCAL_URL": "http://127.0.0.1:9000/v1",
            "THAMDINH_NGU_CANH": "32768",
            "THAMDINH_SUY_LUAN": "true",
            "THAMDINH_DATA_DIR": "D:/thamdinh",
            "THAMDINH_NGAN_SACH_TRUY_XUAT": "24000",
            "THAMDINH_TOI_DA_TOKEN": "16384",
            "THAMDINH_MOI_TIEU_CHI_MOT_LAN": "true",
            "THAMDINH_EMBEDDING_URL": "http://127.0.0.1:9001/v1",
            "THAMDINH_EMBEDDING_MODEL": "bge-m3-q8",
            "THAMDINH_OCR_MODEL": "vgg_seq2seq",
            "THAMDINH_OCR_MODEL_DIR": "D:/models/vietocr",
            "THAMDINH_NGUOI_DUYET": "Nguyễn Văn A",
        }
    )

    assert settings.model == "qwen3.5-4b"
    assert settings.local_url == "http://127.0.0.1:9000/v1"
    assert settings.ngu_canh == 32768
    assert settings.suy_luan is True
    assert settings.data_dir == Path("D:/thamdinh")
    assert settings.ngan_sach_truy_xuat == 24000
    assert settings.toi_da_token == 16384
    assert settings.moi_tieu_chi_mot_lan is True
    assert settings.embedding_url == "http://127.0.0.1:9001/v1"
    assert settings.embedding_model == "bge-m3-q8"
    assert settings.ocr_model == "vgg_seq2seq"
    assert settings.thu_muc_model_ocr == Path("D:/models/vietocr")
    assert settings.nguoi_duyet == "Nguyễn Văn A"
