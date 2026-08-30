import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur Haute Définition du Diagramme de Classes UML (Version Impeccable)
Domaine Métier et Architecture de Données du PMS Alidentec Hospitality
Positionnement spatial parfait, aucune superposition, tracés orthogonaux précis.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)
OUT_PATH = os.path.join(FIG_DIR, 'class_diagram_pms.png')

# Palette de couleurs UML
C_PRIMARY = '#0A3B72'       # Bleu Nuit EMSI
C_HEADER_BG = '#0F4C81'     # Fond d'en-tête de classe
C_BOX_BG = '#FFFFFF'        # Fond de compartiment
C_BORDER = '#0A3B72'        # Bordure de classe
C_PKG_BG = '#F4F7FA'        # Fond de package
C_PKG_BORDER = '#B0BEC5'    # Bordure de package
C_LINE = '#263238'          # Lignes de relations
C_TEXT_LIGHT = '#FFFFFF'    # Texte clair
C_ATTR = '#1F2937'          # Attributs
C_METHOD = '#0369A1'        # Méthodes
C_CARD = '#B91C1C'          # Cardinalités

def draw_uml_class_diagram():
    fig, ax = plt.subplots(figsize=(22, 15), dpi=220)
    ax.set_xlim(-0.5, 21.5)
    ax.set_ylim(-0.5, 15.0)
    ax.axis('off')

    # Titre Global du Diagramme
    ax.text(10.5, 14.5, "DIAGRAMME DE CLASSES UML — DOMAINE MÉTIER PMS ALIDENTEC",
            ha='center', va='center', fontsize=16, fontweight='bold', color=C_PRIMARY)
    ax.text(10.5, 14.15, "Modèle Conceptuel de Données & Entités DDD des Microservices (Norme OMG UML 2.5)",
            ha='center', va='center', fontsize=10, fontstyle='italic', color='#555555')
    ax.plot([0.8, 20.2], [13.9, 13.9], color=C_PRIMARY, lw=1.8)

    # ── Dessin des Packages Thématiques de Fond ──────────────────────────────
    def draw_package(x, y, w, h, name):
        tab_w = min(w * 0.45, 3.6)
        tab_h = 0.45
        tab = FancyBboxPatch((x, y + h), tab_w, tab_h, boxstyle="round,pad=0,rounding_size=0.08",
                             facecolor=C_PKG_BG, edgecolor=C_PKG_BORDER, lw=1.0, zorder=1)
        ax.add_patch(tab)
        ax.text(x + 0.15, y + h + 0.22, name, fontsize=8.5, fontweight='bold', color='#37474F', zorder=2)
        body = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                              facecolor=C_PKG_BG, edgecolor=C_PKG_BORDER, lw=1.0, linestyle='--', zorder=1)
        ax.add_patch(body)

    # 4 Bounded Contexts avec dimensions généreuses
    draw_package(0.2, 7.8, 6.2, 5.8, "Package Multi-Tenancy & IAM")
    draw_package(6.8, 7.2, 6.8, 6.4, "Package Inventaire & Chambres")
    draw_package(0.2, 0.2, 13.4, 7.2, "Package Réservations, CRM & Folios")
    draw_package(14.0, 0.2, 7.0, 13.4, "Package Clôture & Rapports")

    # ── Dessin d'une Classe UML Normée ──────────────────────────────────────
    def draw_class(x, y, w, name, attrs, methods, stereotype="<<Entity>>"):
        lh = 0.23
        pad_top = 0.52 if stereotype else 0.38
        h_attrs = len(attrs) * lh + 0.15
        h_methods = len(methods) * lh + 0.15
        total_h = pad_top + h_attrs + h_methods

        # Fond global de la classe
        box = FancyBboxPatch((x, y), w, total_h, boxstyle="square,pad=0",
                             facecolor=C_BOX_BG, edgecolor=C_BORDER, lw=1.2, zorder=3)
        ax.add_patch(box)

        # En-tête (Header)
        header = FancyBboxPatch((x, y + total_h - pad_top), w, pad_top, boxstyle="square,pad=0",
                                facecolor=C_HEADER_BG, edgecolor=C_BORDER, lw=1.2, zorder=4)
        ax.add_patch(header)

        # Texte Header
        if stereotype:
            ax.text(x + w/2.0, y + total_h - 0.16, stereotype, ha='center', va='center',
                    fontsize=7.5, fontstyle='italic', color='#E0E0E0', zorder=5)
            ax.text(x + w/2.0, y + total_h - 0.36, name, ha='center', va='center',
                    fontsize=9.5, fontweight='bold', color=C_TEXT_LIGHT, zorder=5)
        else:
            ax.text(x + w/2.0, y + total_h - pad_top/2.0, name, ha='center', va='center',
                    fontsize=9.5, fontweight='bold', color=C_TEXT_LIGHT, zorder=5)

        # Ligne séparatrice Header / Attributs
        y_cursor = y + total_h - pad_top
        ax.plot([x, x + w], [y_cursor, y_cursor], color=C_BORDER, lw=1.0, zorder=5)

        # Attributs
        y_attr_start = y_cursor - 0.12
        for i, attr in enumerate(attrs):
            ax.text(x + 0.12, y_attr_start - i*lh, attr, ha='left', va='top',
                    fontsize=7.3, color=C_ATTR, fontfamily='monospace', zorder=5)

        # Ligne séparatrice Attributs / Méthodes
        y_cursor -= h_attrs
        ax.plot([x, x + w], [y_cursor, y_cursor], color=C_BORDER, lw=0.8, zorder=5)

        # Méthodes
        y_method_start = y_cursor - 0.12
        for i, method in enumerate(methods):
            ax.text(x + 0.12, y_method_start - i*lh, method, ha='left', va='top',
                    fontsize=7.3, color=C_METHOD, fontfamily='monospace', zorder=5)

        return {
            'x': x, 'y': y, 'w': w, 'h': total_h,
            'top': (x + w/2.0, y + total_h),
            'bottom': (x + w/2.0, y),
            'left': (x, y + total_h/2.0),
            'right': (x + w, y + total_h/2.0)
        }

    # ── Instanciation des Classes ────────────────────────────────────────────
    c = {}

    # 1. Establishment
    c['Establishment'] = draw_class(
        0.5, 8.2, 2.7, "Establishment",
        ["+ id: UUID", "+ name: String", "+ code: String", "+ vat_rate: Decimal = 0.10",
         "+ city_tax_ts: Decimal = 25.0", "+ tpt_tax: Decimal = 12.0", "+ business_date: Date"],
        ["+ get_taxes(): TaxConfig", "+ advance_date(): Date", "+ is_open(): Boolean"]
    )

    # 2. UserAccount & WebAuthn
    c['UserAccount'] = draw_class(
        3.5, 10.8, 2.6, "UserAccount",
        ["+ id: UUID", "+ username: String", "+ email: String", "+ role: UserRole", "+ is_active: Boolean"],
        ["+ has_permission(p): Bool", "+ verify_token(jwt): Bool"]
    )

    c['WebAuthnCredential'] = draw_class(
        3.5, 8.2, 2.6, "WebAuthnCredential",
        ["+ id: UUID", "+ credential_id: Bytes", "+ public_key: Bytes", "+ sign_count: Int", "+ device_name: String"],
        ["+ verify_signature(ch): Bool", "+ update_counter(cnt)"]
    )

    # 3. RoomType
    c['RoomType'] = draw_class(
        7.1, 10.4, 2.8, "RoomType",
        ["+ id: UUID", "+ code: String", "+ name: String", "+ max_occupancy: Int",
         "+ base_rate_ht: Decimal", "+ surface_sqm: Float"],
        ["+ get_rate_for_date(d): Dec", "+ check_capacity(nb): Bool"]
    )

    # 4. Room
    c['Room'] = draw_class(
        10.4, 10.4, 2.9, "Room",
        ["+ id: UUID", "+ number: String", "+ floor: Int", "+ status: HygieneStatus",
         "+ is_occupied: Boolean", "+ is_locked: Boolean"],
        ["+ mark_clean()", "+ mark_dirty()", "+ mark_inspected()", "+ acquire_lock(ttl): Bool"]
    )

    # 5. HousekeepingTask (Bien séparé sous Room)
    c['HousekeepingTask'] = draw_class(
        10.4, 7.6, 2.9, "HousekeepingTask",
        ["+ id: UUID", "+ task_type: TaskType", "+ status: TaskStatus",
         "+ assigned_at: DateTime", "+ completed_at: DateTime"],
        ["+ start_cleaning()", "+ complete_cleaning()", "+ report_issue(desc)"]
    )

    # 6. GuestProfile
    c['GuestProfile'] = draw_class(
        0.5, 3.8, 2.8, "GuestProfile",
        ["+ id: UUID", "+ first_name: String", "+ last_name: String", "+ email: String",
         "+ phone: String", "+ nationality: String", "+ passport_cin: String", "+ is_vip: Boolean"],
        ["+ get_full_name(): String", "+ get_stay_history(): List", "+ flag_vip()"]
    )

    # 7. Reservation
    c['Reservation'] = draw_class(
        3.8, 3.2, 3.4, "Reservation",
        ["+ id: UUID", "+ confirmation_code: String", "+ check_in: Date", "+ check_out: Date",
         "+ adults_count: Int", "+ children_count: Int", "+ status: ResvStatus",
         "+ total_ht: Decimal", "+ total_taxes: Decimal", "+ total_ttc: Decimal"],
        ["+ calculate_pricing(): Quote", "+ confirm_booking()", "+ check_in_guest()",
         "+ check_out_guest()", "+ cancel_booking()"]
    )

    # 8. StayRecord
    c['StayRecord'] = draw_class(
        0.5, 0.6, 2.8, "StayRecord",
        ["+ id: UUID", "+ arrival_date: Date", "+ departure_date: Date",
         "+ rating: Int", "+ guest_notes: String"],
        ["+ archive_stay()", "+ add_feedback(note)"]
    )

    # 9. Folio
    c['Folio'] = draw_class(
        7.8, 3.2, 3.2, "Folio",
        ["+ id: UUID", "+ folio_number: String", "+ status: FolioStatus",
         "+ total_debit: Decimal", "+ total_credit: Decimal", "+ balance: Decimal"],
        ["+ post_charge(item)", "+ post_payment(pay)", "+ calculate_balance(): Dec",
         "+ can_checkout(): Boolean", "+ close_folio()"]
    )

    # 10. FolioCharge
    c['FolioCharge'] = draw_class(
        7.8, 0.5, 2.7, "FolioCharge",
        ["+ id: UUID", "+ date: Date", "+ description: String",
         "+ charge_type: ChargeType", "+ amount_ht: Decimal",
         "+ vat_amount: Decimal", "+ amount_ttc: Decimal"],
        ["+ compute_tax(vat_rate)", "+ is_room_charge(): Bool"]
    )

    # 11. FolioPayment
    c['FolioPayment'] = draw_class(
        10.9, 0.5, 2.5, "FolioPayment",
        ["+ id: UUID", "+ payment_date: DateTime", "+ method: PaymentMethod",
         "+ amount: Decimal", "+ transaction_ref: String"],
        ["+ validate_payment(): Bool", "+ issue_receipt(): Receipt"]
    )

    # 12. NightAuditSession
    c['NightAuditSession'] = draw_class(
        14.4, 8.4, 3.2, "NightAuditSession",
        ["+ id: UUID", "+ business_date: Date", "+ executed_at: DateTime",
         "+ total_rooms_audited: Int", "+ total_revenue_ht: Decimal",
         "+ total_taxes_collected: Decimal", "+ status: AuditStatus"],
        ["+ execute_night_audit()", "+ roll_business_date()", "+ generate_consolidated_report()"]
    )

    # 13. FinancialReport
    c['FinancialReport'] = draw_class(
        17.9, 8.4, 2.8, "FinancialReport",
        ["+ id: UUID", "+ report_type: ReportType", "+ report_date: Date",
         "+ s3_storage_url: String", "+ checksum_sha256: String"],
        ["+ upload_to_minio()", "+ verify_integrity(): Bool", "+ download_pdf(): Bytes"]
    )

    # 14. PoliceReport
    c['PoliceReport'] = draw_class(
        14.4, 4.4, 2.9, "PoliceReport",
        ["+ id: UUID", "+ generation_date: Date", "+ total_guests: Int",
         "+ dgsn_compliance_code: String"],
        ["+ compile_guest_manifest()", "+ export_dgsn_pdf()"]
    )

    # ── Dessin des Relations UML Orthogonales ─────────────────────────────────
    def draw_orthogonal_rel(start_pt, end_pt, rel_type='assoc', label='', card1='', card2='', waypoints=None, diamond_side='start'):
        pts = [start_pt]
        if waypoints:
            pts.extend(waypoints)
        pts.append(end_pt)

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        # Draw lines
        ax.plot(xs, ys, color=C_LINE, lw=1.2, zorder=4)

        # Draw Diamond
        if rel_type == 'comp':
            d_size = 0.16
            p_base = pts[0] if diamond_side == 'start' else pts[-1]
            p_next = pts[1] if diamond_side == 'start' else pts[-2]
            # Direction
            dx = p_next[0] - p_base[0]
            dy = p_next[1] - p_base[1]
            if abs(dx) > abs(dy): # Horizontal
                sign = 1 if dx > 0 else -1
                poly = Polygon([
                    (p_base[0], p_base[1]),
                    (p_base[0] + sign*d_size, p_base[1] + d_size*0.7),
                    (p_base[0] + sign*2*d_size, p_base[1]),
                    (p_base[0] + sign*d_size, p_base[1] - d_size*0.7)
                ], closed=True, facecolor=C_LINE, edgecolor=C_LINE, lw=1, zorder=6)
            else: # Vertical
                sign = 1 if dy > 0 else -1
                poly = Polygon([
                    (p_base[0], p_base[1]),
                    (p_base[0] + d_size*0.7, p_base[1] + sign*d_size),
                    (p_base[0], p_base[1] + sign*2*d_size),
                    (p_base[0] - d_size*0.7, p_base[1] + sign*d_size)
                ], closed=True, facecolor=C_LINE, edgecolor=C_LINE, lw=1, zorder=6)
            ax.add_patch(poly)

        # Textes Labels & Cardinalités
        if label:
            if waypoints:
                mid_idx = len(pts) // 2
                mid_x = (pts[mid_idx-1][0] + pts[mid_idx][0]) / 2.0
                mid_y = (pts[mid_idx-1][1] + pts[mid_idx][1]) / 2.0 + 0.12
            else:
                mid_x = (pts[0][0] + pts[-1][0]) / 2.0
                mid_y = (pts[0][1] + pts[-1][1]) / 2.0 + 0.12
            ax.text(mid_x, mid_y, label, ha='center', va='bottom', fontsize=7.5,
                    fontstyle='italic', color='#37474F', zorder=6)

        if card1:
            ax.text(pts[0][0] + 0.10, pts[0][1] + 0.08, card1, fontsize=8,
                    fontweight='bold', color=C_CARD, zorder=6)
        if card2:
            ax.text(pts[-1][0] - 0.15, pts[-1][1] + 0.08, card2, fontsize=8,
                    fontweight='bold', color=C_CARD, zorder=6)

    # 1. Establishment -> RoomType (1 to 1..*)
    draw_orthogonal_rel(c['Establishment']['right'], c['RoomType']['left'],
                        rel_type='comp', label='contient', card1='1', card2='1..*')

    # 2. RoomType -> Room (1 to 1..*)
    draw_orthogonal_rel(c['RoomType']['right'], c['Room']['left'],
                        rel_type='comp', label='décline en', card1='1', card2='1..*')

    # 3. UserAccount -> WebAuthnCredential (1 to 0..*)
    draw_orthogonal_rel(c['UserAccount']['bottom'], c['WebAuthnCredential']['top'],
                        rel_type='comp', label='possède', card1='1', card2='0..*')

    # 4. Room -> HousekeepingTask (1 to 0..*)
    draw_orthogonal_rel(c['Room']['bottom'], c['HousekeepingTask']['top'],
                        rel_type='comp', label='fait l\'objet de', card1='1', card2='0..*')

    # 5. GuestProfile -> Reservation (1 to 0..*)
    draw_orthogonal_rel(c['GuestProfile']['right'], c['Reservation']['left'],
                        rel_type='assoc', label='effectue', card1='1', card2='0..*')

    # 6. GuestProfile -> StayRecord (1 to 0..*)
    draw_orthogonal_rel(c['GuestProfile']['bottom'], c['StayRecord']['top'],
                        rel_type='comp', label='historise', card1='1', card2='0..*')

    # 7. Reservation -> Folio (1 to 1)
    draw_orthogonal_rel(c['Reservation']['right'], c['Folio']['left'],
                        rel_type='comp', label='rattache', card1='1', card2='1')

    # 8. Folio -> FolioCharge (1 to 0..*)
    draw_orthogonal_rel((c['Folio']['x'] + 0.8, c['Folio']['y']),
                        (c['FolioCharge']['x'] + 0.8, c['FolioCharge']['y'] + c['FolioCharge']['h']),
                        rel_type='comp', label='comprend', card1='1', card2='0..*')

    # 9. Folio -> FolioPayment (1 to 0..*)
    draw_orthogonal_rel((c['Folio']['x'] + 2.4, c['Folio']['y']),
                        (c['FolioPayment']['x'] + 0.8, c['FolioPayment']['y'] + c['FolioPayment']['h']),
                        rel_type='comp', label='règle par', card1='1', card2='0..*')

    # 10. NightAuditSession -> FinancialReport (1 to 1..*)
    draw_orthogonal_rel(c['NightAuditSession']['right'], c['FinancialReport']['left'],
                        rel_type='comp', label='produit', card1='1', card2='1..*')

    # 11. Reservation -> Room (0..* to 1) via Waypoint propre
    draw_orthogonal_rel(c['Reservation']['top'], (c['Room']['x'] + 0.6, c['Room']['y']),
                        rel_type='assoc', label='assigne', card1='0..*', card2='1',
                        waypoints=[(c['Reservation']['x'] + 1.7, 7.3), (c['Room']['x'] + 0.6, 7.3)])

    # 12. NightAuditSession -> Folio (clôture) via Waypoint propre
    draw_orthogonal_rel(c['NightAuditSession']['left'], (c['Folio']['x'] + c['Folio']['w'], c['Folio']['y'] + 1.4),
                        rel_type='assoc', label='clôture & audite', card1='1', card2='1..*',
                        waypoints=[(13.8, 4.6), (11.0, 4.6)])

    # 13. Reservation -> PoliceReport (1 to 1)
    draw_orthogonal_rel((c['Reservation']['right'][0], c['Reservation']['y'] + 2.0),
                        c['PoliceReport']['left'],
                        rel_type='assoc', label='génère fiche DGSN', card1='1', card2='1',
                        waypoints=[(7.5, 5.2), (14.4, 5.2)])

    # ── Légende UML en Bas à Droite ──────────────────────────────────────────
    leg_x = 14.4
    leg_y = 0.5
    leg_w = 6.4
    leg_h = 3.4
    leg_box = FancyBboxPatch((leg_x, leg_y), leg_w, leg_h, boxstyle="round,pad=0,rounding_size=0.1",
                             facecolor='#FFFFFF', edgecolor='#B0BEC5', lw=1.0, zorder=3)
    ax.add_patch(leg_box)
    ax.text(leg_x + 0.2, leg_y + leg_h - 0.28, "LÉGENDE DES RELATIONS UML :",
            fontsize=8.5, fontweight='bold', color=C_PRIMARY, zorder=4)

    items = [
        ("♦  Composition forte (Cycle de vie dépendant / Cascade)", 'comp'),
        ("—  Association simple avec cardinalités (1..*, 0..*, 1)", 'assoc'),
        ("Toutes les entités respectent le typage strict Decimal & UUID", 'note'),
        ("Séparation en 4 Bounded Contexts conformes au DDD", 'note2')
    ]
    for idx, (txt, k) in enumerate(items):
        item_y = leg_y + leg_h - 0.75 - idx*0.62
        if k == 'comp':
            poly = Polygon([(leg_x + 0.3, item_y), (leg_x + 0.45, item_y + 0.09), (leg_x + 0.6, item_y), (leg_x + 0.45, item_y - 0.09)],
                           closed=True, facecolor=C_LINE, edgecolor=C_LINE, lw=1)
            ax.add_patch(poly)
            ax.plot([leg_x + 0.6, leg_x + 1.0], [item_y, item_y], color=C_LINE, lw=1.2)
        elif k == 'assoc':
            ax.plot([leg_x + 0.3, leg_x + 1.0], [item_y, item_y], color=C_LINE, lw=1.2)
            ax.text(leg_x + 0.35, item_y + 0.05, "1", fontsize=7, color=C_CARD, fontweight='bold')
            ax.text(leg_x + 0.85, item_y + 0.05, "*", fontsize=7, color=C_CARD, fontweight='bold')

        ax.text(leg_x + 1.15, item_y, txt, ha='left', va='center', fontsize=7.5, color='#333333', zorder=4)

    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=220, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[SUCCÈS] Nouveau Diagramme de Classes généré : {OUT_PATH}")

if __name__ == '__main__':
    draw_uml_class_diagram()
