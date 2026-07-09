import pytest

from mini_nucleiq.settings import Settings

_ENV_VARS = (
    "SAMPLES_API_BASE_URL",
    "SAMPLES_API_TIMEOUT_SECONDS",
    "SAMPLES_API_MAX_RETRIES",
    "SAMPLES_API_BACKOFF_SECONDS",
)


def test_defaults_are_sensible(tmp_path, monkeypatch: pytest.MonkeyPatch):
    # Run from a directory with no .env so the defaults are truly the source's own.
    monkeypatch.chdir(tmp_path)
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    settings = Settings()

    assert "cellsia/mini-nucleiq-code-challenge" in settings.samples_api_base_url
    assert settings.samples_api_timeout_seconds == 5.0
    assert settings.samples_api_max_retries == 2


def test_environment_overrides_defaults(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SAMPLES_API_BASE_URL", "https://example.test")
    monkeypatch.setenv("SAMPLES_API_MAX_RETRIES", "5")
    monkeypatch.setenv("SAMPLES_API_TIMEOUT_SECONDS", "2.5")

    settings = Settings()

    assert settings.samples_api_base_url == "https://example.test"
    assert settings.samples_api_max_retries == 5
    assert settings.samples_api_timeout_seconds == 2.5  # env strings coerce to float
