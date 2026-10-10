"""Non-secret configuration. These are identifiers, not credentials."""

import os

REGISTRY_LOCATION = os.environ.get("REGISTRY_LOCATION", "asia-south1")
# Last part of each server's registry resource name (Step 9.1).
ERP_SERVER_ID = os.environ.get(
    "ERP_SERVER_ID", "agentregistry-00000000-0000-0000-08a4-38206d6337da"
)
VENDOR_SERVER_ID = os.environ.get(
    "VENDOR_SERVER_ID", "agentregistry-00000000-0000-0000-794a-abadbcb1af74"
)
