"""Model Armor checks for text that crosses a trust boundary."""

import os

from google.cloud import modelarmor_v1

LOCATION = os.environ.get("MODEL_ARMOR_LOCATION", "asia-south1")
TEMPLATE = os.environ.get("MODEL_ARMOR_TEMPLATE", "")
MAX_CHARS = 4000


def enabled() -> bool:
    return bool(TEMPLATE)


def collect_text(invoice: dict) -> str:
    """The attacker-controlled free text of an invoice, bounded."""
    pieces = [invoice.get("vendor_name", "")]
    pieces += [i.get("description", "") for i in invoice.get("line_items", [])]
    pieces += invoice.get("extraction_notes", [])
    return "\n".join(pieces)[:MAX_CHARS]


def prompt_flagged(text: str) -> bool:
    """True if Model Armor matches a filter. Raises on API failure."""
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    client = modelarmor_v1.ModelArmorClient(
        transport="rest",
        client_options={"api_endpoint": f"modelarmor.{LOCATION}.rep.googleapis.com"},
    )
    name = f"projects/{project}/locations/{LOCATION}/templates/{TEMPLATE}"
    request = modelarmor_v1.SanitizeUserPromptRequest(
        name=name, user_prompt_data=modelarmor_v1.DataItem(text=text)
    )
    result = client.sanitize_user_prompt(request=request)
    state = result.sanitization_result.filter_match_state
    return state == modelarmor_v1.FilterMatchState.MATCH_FOUND
