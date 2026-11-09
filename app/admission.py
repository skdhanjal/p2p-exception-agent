"""Admission control for uploaded documents. Runs before any model."""

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}
MAX_BYTES = 5 * 1024 * 1024
MAX_TEXT = 2000
MAGIC = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
}


def check_parts(parts: list) -> list[str]:
    """Return reasons to refuse the message. Empty means admit."""
    problems: list[str] = []
    documents = [p for p in parts if p.inline_data or p.file_data]
    if len(documents) != 1:
        problems.append("send exactly one document")
    for part in documents:
        if part.file_data:
            problems.append("referenced files are not accepted")
            continue
        blob = part.inline_data
        data = blob.data or b""
        kind = str(blob.mime_type)[:40]
        if blob.mime_type not in ALLOWED_TYPES:
            problems.append(f"file type {kind} is not accepted")
        elif not data.startswith(MAGIC[blob.mime_type]):
            problems.append("file content does not match its type")
        if len(data) > MAX_BYTES:
            problems.append("file is too large")
    if sum(len(p.text or "") for p in parts) > MAX_TEXT:
        problems.append("message text is too long")
    return problems
