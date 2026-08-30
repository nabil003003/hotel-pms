"""Génération des 6 rapports PDF (spec ligne 625-632, D12) — `reportlab`
(pur Python, aucune dépendance système supplémentaire dans l'image Docker,
contrairement à weasyprint/wkhtmltopdf)."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def render_report(title: str, subtitle: str, rows: list[tuple[str, ...]]) -> bytes:
    """`rows[0]` est l'en-tête de colonnes ; les suivantes, les données —
    mise en page volontairement simple (texte tabulaire), pas de charte
    graphique (hors-scope Sprint 5)."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 20 * mm, title)
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 27 * mm, subtitle)

    y = height - 40 * mm
    col_x = [20 * mm + i * 40 * mm for i in range(len(rows[0]))] if rows else [20 * mm]

    for row_index, row in enumerate(rows):
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm
        c.setFont("Helvetica-Bold" if row_index == 0 else "Helvetica", 9)
        for x, cell in zip(col_x, row):
            c.drawString(x, y, str(cell))
        y -= 6 * mm

    c.save()
    return buffer.getvalue()


def render_ca_detail(establishment_id: str, business_date: str, data: dict) -> bytes:
    rows = [("Poste", "HT", "TVA", "TTC")]
    rows += [(l["poste_comptable"], f"{l['montant_ht']:.2f}", f"{l['tva_amount']:.2f}", f"{l['montant_ttc']:.2f}") for l in data["lines"]]
    return render_report("CA détaillé du jour", f"{establishment_id} — {business_date}", rows)


def render_encashments(establishment_id: str, business_date: str, data: dict) -> bytes:
    rows = [("Mode de règlement", "Total")]
    rows += [(l["mode"], f"{l['total']:.2f}") for l in data["lines"]]
    return render_report("Encaissements du jour", f"{establishment_id} — {business_date}", rows)


def render_debtors(establishment_id: str, business_date: str, data: list[dict]) -> bytes:
    rows = [("Folio", "Réservation", "Solde")]
    rows += [(d["folio_id"], d["booking_id"], f"{d['balance']:.2f}") for d in data]
    return render_report("Soldes débiteurs (Folio B)", f"{establishment_id} — {business_date}", rows)


def render_departures(establishment_id: str, business_date: str, data: dict) -> bytes:
    rows = [("Folio", "Réservation", "Solde")]
    rows += [(d["folio_id"], d["booking_id"], f"{d['balance']:.2f}") for d in data["departures"]]
    return render_report("Départs attendus J+1", f"{establishment_id} — {business_date}", rows)


def render_arrivals(establishment_id: str, business_date: str, bookings: list[dict]) -> bytes:
    rows = [("Réservation", "Client", "Chambre", "Statut")]
    rows += [(b["id"], str(b["customer_id"]), str(b["room_id"]), b["status"]) for b in bookings]
    return render_report("Arrivées prévues J+1", f"{establishment_id} — {business_date}", rows)


def render_occupancy_forecast(establishment_id: str, business_date: str, forecast: dict) -> bytes:
    rows = [
        ("Indicateur", "Valeur"),
        ("Arrivées prévues", str(forecast["arrivals_count"])),
        ("TO prévisionnel (%)", f"{forecast['projected_occupancy_rate']:.2f}"),
        ("ADR proxy", f"{forecast['adr_proxy']:.2f}"),
        ("RevPAR proxy", f"{forecast['revpar_proxy']:.2f}"),
    ]
    return render_report("Prévision d'occupation J+1", f"{establishment_id} — {business_date}", rows)
