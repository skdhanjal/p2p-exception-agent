"""Render invoice PDFs from case data, in three layouts."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _money(value: float) -> str:
    return f"{value:,.2f}"


def render_invoice(inv: dict, path: Path, layout: int, footer: str = "", hidden: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - 60
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, inv["vendor_name"])
    pdf.setFont("Helvetica", 11)
    po = inv["po_number"] or "(none)"
    header = [
        f"INVOICE {inv['invoice_number']}",
        f"Date: {inv['invoice_date']}",
        f"PO Number: {po}",
        f"Currency: {inv['currency']}",
    ]
    if layout == 2:
        header = [
            f"Invoice no. {inv['invoice_number']}",
            f"Issued {inv['invoice_date']}  |  Order ref {po}",
            f"All amounts in {inv['currency']}",
        ]
    for text in header:
        y -= 18
        pdf.drawString(50, y, text)
    y -= 34
    pdf.setFont("Helvetica", 10)
    for item in inv["line_items"]:
        y -= 18
        qty, price = f"{item['quantity']:g}", _money(item["unit_price"])
        total = _money(item["line_total"])
        if layout == 0:
            pdf.drawString(50, y, item["description"])
            pdf.drawRightString(320, y, qty)
            pdf.drawRightString(420, y, price)
            pdf.drawRightString(520, y, total)
        elif layout == 1:
            pdf.drawString(50, y, f"{qty} x {item['description']} @ {price} = {total}")
        else:
            pdf.drawString(50, y, item["description"])
            pdf.drawString(300, y, f"qty {qty}")
            pdf.drawRightString(520, y, f"{price} each, {total}")
    y -= 34
    for label, amount in (
        ("Subtotal", inv["subtotal"]),
        ("Tax", inv["tax_amount"]),
        ("Total due", inv["total_amount"]),
    ):
        pdf.drawRightString(440, y, f"{label}:")
        pdf.drawRightString(520, y, _money(amount))
        y -= 16
    if inv["bank_account_last4"]:
        y -= 14
        pdf.drawString(50, y, f"Pay to account ending {inv['bank_account_last4']}")

    if hidden:
        pdf.setFillGray(1)  # white on white: invisible to a reader
        pdf.setFont("Helvetica", 9)
        pdf.drawString(50, 200, hidden)

    if footer:
        pdf.setFont("Helvetica", 7)
        pdf.setFillGray(0.6)
        pdf.drawString(50, 40, footer)
    pdf.save()
