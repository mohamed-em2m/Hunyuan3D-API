"""
tests/test_config.py
~~~~~~~~~~~~~~~~~~~~
Verify that dynaconf settings load correctly and expose the expected keys.
These tests run without any ML dependencies (no torch, no hy3dgen).
"""

from hunyuan3d_api.config import settings


def test_settings_has_app_section():
    assert hasattr(settings, "app")
    assert settings.app.name == "Hunyuan3D API"


def test_settings_has_server_section():
    assert hasattr(settings, "server")
    assert isinstance(settings.server.port, int)
    assert isinstance(settings.server.host, str)


def test_settings_has_model_section():
    assert hasattr(settings, "model")
    assert settings.model.pretrained_id == "tencent/Hunyuan3D-2"
    assert settings.model.device in ("auto", "cpu", "cuda")


def test_settings_has_storage_section():
    assert hasattr(settings, "storage")
    assert settings.storage.max_file_size_mb > 0
    assert len(settings.storage.supported_formats) > 0


def test_settings_has_ngrok_section():
    assert hasattr(settings, "ngrok")
    assert isinstance(settings.ngrok.enabled, bool)
