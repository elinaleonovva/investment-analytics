from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def build_portfolio_pdf_report(portfolio, analytics_payload, currency="USD"):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 20 * mm

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(20 * mm, y, f"Portfolio Report: {portfolio.name}")
    y -= 8 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, y, f"Currency: {currency}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"Current value: {analytics_payload['totalCurrentValue']:.2f}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"Invested value: {analytics_payload['totalInvestedValue']:.2f}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"PnL: {analytics_payload['totalPnL']:.2f}")
    y -= 6 * mm
    pdf.drawString(20 * mm, y, f"PnL %: {analytics_payload['totalPnLPercent']:.2f}")
    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20 * mm, y, "Positions")
    y -= 8 * mm
    pdf.setFont("Helvetica", 9)
    for row in analytics_payload["positions"]:
        stock = row["stock"]
        line = (
            f"{stock.indexISIN:10} qty={row['quantity']:.4f} "
            f"invested={row['invested']:.2f} current={row['current_value']:.2f} "
            f"PnL={row['pnl']:.2f} ({row['pnl_percent']:.2f}%)"
        )
        pdf.drawString(20 * mm, y, line[:110])
        y -= 5 * mm
        if y < 20 * mm:
            pdf.showPage()
            y = height - 20 * mm
            pdf.setFont("Helvetica", 9)

    pdf.save()
    buffer.seek(0)
    return buffer
