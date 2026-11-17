"""Approvals service: records human decisions under a verified identity."""

import os
import secrets

import uvicorn
from common.approvals_logic import validate_decision
from common.bq import run_query
from common.logs import log
from fastapi import FastAPI, Header, HTTPException
from google.auth.transport import requests as grequests
from google.oauth2 import id_token
from pydantic import BaseModel

app = FastAPI()
APPROVERS = {
    e.strip().lower()
    for e in os.environ.get("APPROVER_EMAILS", "").split(",")
    if e.strip()
}


class Decision(BaseModel):
    invoice_number: str
    vendor_id: str
    amount: float
    currency: str
    decision: str
    comment: str = ""


def caller_email(authorization: str | None) -> str:
    """Verify the signature and expiry of the caller's ID token.

    Cloud Run already enforced the invoker role and the audience. User
    tokens carry a client audience, so audience is not re-checked here.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    try:
        claims = id_token.verify_oauth2_token(
            authorization[7:], grequests.Request(), audience=None
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    if not claims.get("email_verified"):
        raise HTTPException(status_code=403, detail="unverified email")
    return claims["email"].lower()


@app.post("/decisions")
def decide(body: Decision, authorization: str | None = Header(None)):
    email = caller_email(authorization)
    try:
        validate_decision(
            email=email,
            approvers=APPROVERS,
            comment=body.comment,
            **body.model_dump(exclude={"comment"}),
        ) # type: ignore
    except PermissionError as exc:
        log("WARNING", "approval_denied", reason="not_an_approver")
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    approval_id = f"APR-{secrets.randbelow(900000) + 100000}"
    run_query(
        """
        INSERT INTO `__DATASET__.approvals`
          (approval_id, invoice_number, vendor_id, amount, currency,
           decision, approver_email, comment, decided_at)
        VALUES (@id, @invoice, @vendor, @amount, @currency,
                @decision, @email, @comment, CURRENT_TIMESTAMP())
        """,
        {
            "id": approval_id,
            "invoice": body.invoice_number,
            "vendor": body.vendor_id,
            "amount": float(body.amount),
            "currency": body.currency,
            "decision": body.decision,
            "email": email,
            "comment": body.comment,
        },
    )
    log("INFO", "approval_recorded", decision=body.decision)
    return {"approval_id": approval_id, "decision": body.decision, "approver": email}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ["PORT"]))
