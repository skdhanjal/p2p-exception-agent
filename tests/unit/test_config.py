import importlib

import pytest


def load(monkeypatch, **env):
    for key in (
        "APP_ENV",
        "ERP_SERVER_ID",
        "VENDOR_SERVER_ID",
        "A2A_PAYMENTS_AGENT_URL",
        "PAYMENTS_DRY_RUN",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from app import config

    return importlib.reload(config)


FULL = {
    "ERP_SERVER_ID": "a",
    "VENDOR_SERVER_ID": "b",
    "A2A_PAYMENTS_AGENT_URL": "https://x",
}


def test_local_runs_without_configuration(monkeypatch):
    load(monkeypatch).validate()


def test_deployed_agent_refuses_placeholders(monkeypatch):
    config = load(monkeypatch, APP_ENV="dev")
    with pytest.raises(RuntimeError):
        config.validate()


def test_a_fully_configured_dev_agent_starts(monkeypatch):
    load(monkeypatch, APP_ENV="dev", **FULL).validate()


def test_prod_cannot_start_with_live_payments(monkeypatch):
    config = load(monkeypatch, APP_ENV="prod", PAYMENTS_DRY_RUN="false", **FULL)
    with pytest.raises(RuntimeError):
        config.validate()
    load(monkeypatch, APP_ENV="local", PAYMENTS_DRY_RUN="true", **FULL)
