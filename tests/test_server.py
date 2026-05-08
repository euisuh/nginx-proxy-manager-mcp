import pytest
import os


def test_validate_env_fails_on_missing_vars(monkeypatch):
    monkeypatch.delenv("NPM_URL", raising=False)
    monkeypatch.delenv("NPM_EMAIL", raising=False)
    monkeypatch.delenv("NPM_PASSWORD", raising=False)
    from server import validate_env
    with pytest.raises(SystemExit) as exc:
        validate_env()
    assert exc.value.code == 1


def test_validate_env_passes_with_all_vars(monkeypatch):
    monkeypatch.setenv("NPM_URL", "http://npm.test")
    monkeypatch.setenv("NPM_EMAIL", "admin@test.com")
    monkeypatch.setenv("NPM_PASSWORD", "testpass")
    from server import validate_env
    validate_env()  # should not raise
