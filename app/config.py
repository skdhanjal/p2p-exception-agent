"""Configuration. Environment variables win. Fails fast when deployed."""

import os

ENV_NAME = os.environ.get("APP_ENV", "local")  # local, dev, or prod
GIT_SHA = os.environ.get("GIT_SHA", "unknown")
REGISTRY_LOCATION = os.environ.get("REGISTRY_LOCATION", "asia-south1")
ERP_SERVER_ID = os.environ.get("ERP_SERVER_ID", "REPLACE_ME")
VENDOR_SERVER_ID = os.environ.get("VENDOR_SERVER_ID", "REPLACE_ME")
PAYMENTS_AGENT_URL = os.environ.get("A2A_PAYMENTS_AGENT_URL", "REPLACE_ME")
# Stay in dry run until you deliberately change it.
PAYMENTS_DRY_RUN = os.environ.get("PAYMENTS_DRY_RUN", "true").lower() != "false"


def validate() -> None:
    """Stop at startup, not at the first invoice."""
    if ENV_NAME == "local":
        return
    required = {
        "ERP_SERVER_ID": ERP_SERVER_ID,
        "VENDOR_SERVER_ID": VENDOR_SERVER_ID,
        "A2A_PAYMENTS_AGENT_URL": PAYMENTS_AGENT_URL,
    }
    missing = [k for k, v in required.items() if v.startswith("REPLACE")]
    if missing:
        raise RuntimeError(f"Missing configuration: {missing}")
    if ENV_NAME == "prod" and not PAYMENTS_DRY_RUN:
        raise RuntimeError("Live payments are not allowed in this phase")
