"""Data contracts for invoice intake."""

import re
from datetime import date

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

TOLERANCE = 0.02  # allow two cents of rounding in money checks


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float

    @field_validator("quantity", "unit_price", "line_total")
    @classmethod
    def not_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("must not be negative")
        return value

    @model_validator(mode="after")
    def line_math_is_consistent(self) -> "LineItem":
        expected = round(self.quantity * self.unit_price, 2)
        if abs(expected - self.line_total) > TOLERANCE:
            raise ValueError(
                f"line_total {self.line_total} does not equal quantity "
                f"x unit_price ({expected}) for '{self.description}'"
            )
        return self


class InvoiceExtraction(BaseModel):
    invoice_number: str
    vendor_name: str
    po_number: str | None = None
    invoice_date: str = Field(description="ISO date, YYYY-MM-DD")
    currency: str = Field(description="3-letter code, for example USD")
    line_items: list[LineItem]
    subtotal: float
    tax_amount: float = 0.0
    total_amount: float
    bank_account_last4: str | None = None
    extraction_notes: list[str] = Field(default_factory=list)

    @field_validator("invoice_date")
    @classmethod
    def valid_iso_date(cls, value: str) -> str:
        date.fromisoformat(value)  # raises ValueError if malformed
        return value

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise ValueError("must be a 3-letter uppercase code")
        return value

    @field_validator("bank_account_last4")
    @classmethod
    def last_four_digits(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"\d{4}", value):
            raise ValueError("must be exactly four digits, or null")
        return value

    @field_validator("line_items")
    @classmethod
    def at_least_one_line(cls, value: list) -> list:
        if not value:
            raise ValueError("at least one line item is required")
        return value

    @model_validator(mode="after")
    def totals_are_consistent(self) -> "InvoiceExtraction":
        lines_sum = round(sum(i.line_total for i in self.line_items), 2)
        if abs(lines_sum - self.subtotal) > TOLERANCE:
            raise ValueError(
                f"subtotal {self.subtotal} does not equal the sum of "
                f"line totals ({lines_sum})"
            )
        expected = round(self.subtotal + self.tax_amount, 2)
        if abs(expected - self.total_amount) > TOLERANCE:
            raise ValueError(
                f"total_amount {self.total_amount} does not equal "
                f"subtotal plus tax_amount ({expected})"
            )
        return self


def validate_invoice(
    data: dict,
) -> tuple[InvoiceExtraction | None, list[str]]:
    """Validate extracted data. Returns (invoice, errors)."""
    try:
        return InvoiceExtraction.model_validate(data), []
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            where = ".".join(str(p) for p in err["loc"]) or "invoice"
            errors.append(f"{where}: {err['msg']}")
        return None, errors
