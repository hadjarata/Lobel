from io import BytesIO
from pathlib import Path

import reportlab
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)


FONT_NAME = "LobelVera"
FONT_BOLD = "LobelVeraBold"


def _register_fonts():
    fonts = Path(reportlab.__file__).resolve().parent / "fonts"
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, fonts / "Vera.ttf"))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, fonts / "VeraBd.ttf"))


def _safe(value):
    return (
        str(value or "").replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_order_receipt_pdf(receipt):
    _register_fonts()
    buffer = BytesIO()
    page_width, page_height = A4
    frame = Frame(18 * mm, 20 * mm, page_width - 36 * mm, page_height - 38 * mm)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT_NAME, 7.5)
        canvas.setFillColor(colors.HexColor("#6B5B55"))
        canvas.drawString(
            18 * mm, 10 * mm,
            "Ce document constitue un justificatif de commande et de paiement.",
        )
        canvas.drawRightString(
            page_width - 18 * mm, 10 * mm, f"Page {doc.page}"
        )
        canvas.restoreState()

    document = BaseDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title=f"Justificatif de commande {receipt.receipt_number}",
        author=settings.STORE_DISPLAY_NAME,
    )
    document.addPageTemplates(PageTemplate(id="receipt", frames=[frame], onPage=footer))
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName=FONT_NAME,
        fontSize=9, leading=13, textColor=colors.HexColor("#3D2D29"),
    )
    heading = ParagraphStyle(
        "Heading", parent=body, fontName=FONT_BOLD, fontSize=18,
        leading=22, spaceAfter=4,
    )
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=11)
    right = ParagraphStyle("Right", parent=body, alignment=TA_RIGHT)
    center = ParagraphStyle("Center", parent=small, alignment=TA_CENTER)
    white_center = ParagraphStyle(
        "WhiteCenter", parent=center, textColor=colors.white,
        fontName=FONT_BOLD, fontSize=11,
    )
    table_header = ParagraphStyle(
        "TableHeader", parent=small, textColor=colors.white,
        fontName=FONT_BOLD,
    )
    snapshot = receipt.snapshot
    currency = _safe(snapshot["currency"])

    story = [
        Table(
            [[
                Paragraph("LS", white_center),
                Paragraph(
                    f"<b>{_safe(settings.STORE_DISPLAY_NAME)}</b><br/>"
                    f"{_safe(settings.STORE_ADDRESS)}<br/>"
                    f"{_safe(settings.STORE_CONTACT_EMAIL)} "
                    f"{_safe(settings.STORE_CONTACT_PHONE)}",
                    small,
                ),
                Paragraph(
                    f"<b>{_safe(snapshot['document_title'])}</b><br/>"
                    f"{_safe(receipt.receipt_number)}<br/>"
                    f"Émis le {_safe(receipt.issued_at.strftime('%d/%m/%Y'))}",
                    right,
                ),
            ]],
            colWidths=[18 * mm, 78 * mm, 76 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#3D2D29")),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#D4AF95")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]),
        ),
        Spacer(1, 9 * mm),
        Paragraph("Justificatif de commande", heading),
        Paragraph(
            f"Commande #{snapshot['order_id']} - Paiement confirmé le "
            f"{_safe(receipt.issued_at.strftime('%d/%m/%Y à %H:%M'))}",
            body,
        ),
        Spacer(1, 5 * mm),
        Table(
            [
                ["Référence paiement", _safe(snapshot["payment_reference"])],
                ["Mode de paiement", _safe(snapshot["payment_method"])],
                ["Statut", _safe(snapshot["payment_status"])],
                ["Devise", currency],
            ],
            colWidths=[52 * mm, 120 * mm],
            style=TableStyle([
                ("FONT", (0, 0), (-1, -1), FONT_NAME, 8.5),
                ("FONT", (0, 0), (0, -1), FONT_BOLD, 8.5),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5E6ED")),
                ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D4AF95")),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]),
        ),
        Spacer(1, 6 * mm),
        Paragraph("Livraison", ParagraphStyle("Sub", parent=body, fontName=FONT_BOLD, fontSize=11)),
        Paragraph(
            "<br/>".join(filter(None, (
                _safe(snapshot["customer"]["name"]),
                _safe(snapshot["customer"]["email"]),
                _safe(snapshot["customer"]["phone"]),
                _safe(snapshot["customer"]["address"]),
            ))),
            body,
        ),
        Spacer(1, 6 * mm),
    ]
    rows = [[
        Paragraph("Article", table_header), Paragraph("Variante", table_header),
        Paragraph("Qté", table_header), Paragraph("Prix unitaire", table_header),
        Paragraph("Total", table_header),
    ]]
    for item in snapshot["items"]:
        rows.append([
            Paragraph(_safe(item["product"]), small),
            Paragraph(_safe(item["variant"]), small),
            str(item["quantity"]),
            f"{item['unit_price']} {currency}",
            f"{item['line_total']} {currency}",
        ])
    story.extend([
        Table(
            rows, repeatRows=1, colWidths=[60 * mm, 38 * mm, 12 * mm, 31 * mm, 31 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3D2D29")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONT", (0, 0), (-1, -1), FONT_NAME, 7.8),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#D4AF95")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 6 * mm),
        Table(
            [
                ["Sous-total", f"{snapshot['totals']['subtotal']} {currency}"],
                ["Remise", f"{snapshot['totals']['discount']} {currency}"],
                ["Livraison", f"{snapshot['totals']['shipping']} {currency}"],
                ["Total payé", f"{snapshot['totals']['total']} {currency}"],
            ],
            colWidths=[45 * mm, 40 * mm], hAlign="RIGHT",
            style=TableStyle([
                ("FONT", (0, 0), (-1, -1), FONT_NAME, 9),
                ("FONT", (0, -1), (-1, -1), FONT_BOLD, 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#3D2D29")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 8 * mm),
        Paragraph(
            "Ce document constitue un justificatif de commande et de paiement. "
            "Il ne constitue pas une facture fiscale certifiée.",
            center,
        ),
    ])
    if receipt.order.status in {
        "refund_required", "refund_pending", "refunded", "refund_failed",
    }:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            "Attention : la commande fait l'objet d'un processus de remboursement. "
            "Ce document reflète le paiement initial.",
            center,
        ))
    document.build(story)
    return buffer.getvalue()
