import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de la capture d'écran Haute Définition du module :
NIGHT AUDIT (Clôture Journalière Nocturne)
Dessin 100% vectoriel pur sans caractères spéciaux/emojis manquants.
Thème sombre AMH Hospitality (#1B1614 / #201915 / Orange #E55A24).
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
PIC_DIR = os.path.join(BASE_DIR, 'pictures of rapport')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(PIC_DIR, exist_ok=True)

OUT_FIG = os.path.join(FIG_DIR, '06_module_cloture_journaliere_night_audit.png')
OUT_PIC = os.path.join(PIC_DIR, '06_cloture_nocturne_night_audit.png')

def generate_night_audit_ui():
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), color='#161311')
    draw = ImageDraw.Draw(img)

    font_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_reg = "C:/Windows/Fonts/arial.ttf"
    font_italic = "C:/Windows/Fonts/ariali.ttf"
    if not os.path.exists(font_bold):
        font_bold = "arial.ttf"
        font_reg = "arial.ttf"
        font_italic = "arial.ttf"

    f_logo = ImageFont.truetype(font_bold, 24)
    f_h1 = ImageFont.truetype(font_bold, 32)
    f_sub = ImageFont.truetype(font_reg, 16)
    f_nav = ImageFont.truetype(font_bold, 16)
    f_nav_sub = ImageFont.truetype(font_reg, 14)
    f_card_title = ImageFont.truetype(font_bold, 20)
    f_card_sub = ImageFont.truetype(font_reg, 15)
    f_btn = ImageFont.truetype(font_bold, 18)
    f_kpi_val = ImageFont.truetype(font_bold, 24)
    f_kpi_lbl = ImageFont.truetype(font_bold, 13)
    f_mono = ImageFont.truetype(font_reg, 14)

    # ── 1. SIDEBAR GAUCHE (x: 0 à 300) ───────────────────────────────────────
    draw.rectangle([0, 0, 300, height], fill='#201915')
    draw.line([300, 0, 300, height], fill='#2E241E', width=1)

    # Logo AMH Hospitality (4 carrés orange)
    draw.rectangle([35, 38, 48, 51], fill='#E55A24')
    draw.rectangle([52, 38, 65, 51], fill='#E55A24')
    draw.rectangle([35, 55, 48, 68], fill='#E55A24')
    draw.rectangle([52, 55, 65, 68], fill='#E55A24')
    draw.text((78, 42), "AMH Hospitality", fill='#F5F5F5', font=f_logo)

    # Menu items
    nav_items = [
        ("Reservations", False),
        ("Front Office", False),
        ("Housekeeping", False),
        ("Analytics", False),
        ("Night Audit", True), # Actif
        ("Notifications", False),
    ]
    y_nav = 130
    for label, is_active in nav_items:
        if is_active:
            draw.rounded_rectangle([20, y_nav - 8, 280, y_nav + 34], radius=8, fill='#E55A24')
            draw.ellipse([38, y_nav + 6, 48, y_nav + 16], fill='#FFFFFF')
            draw.text((58, y_nav), label, fill='#FFFFFF', font=f_nav)
        else:
            draw.ellipse([38, y_nav + 6, 46, y_nav + 14], fill='#8A7D74')
            draw.text((58, y_nav), label, fill='#A89B91', font=f_nav_sub)
        y_nav += 48

    # Section Administration
    draw.text((35, y_nav + 20), "ADMINISTRATION", fill='#6B5B52', font=ImageFont.truetype(font_bold, 12))
    admin_items = ["Etablissements", "Utilisateurs", "Tarification", "Partenaires", "Canaux OTA"]
    y_nav += 50
    for label in admin_items:
        draw.ellipse([38, y_nav + 6, 44, y_nav + 12], fill='#5A4E46')
        draw.text((55, y_nav), label, fill='#8A7D74', font=f_nav_sub)
        y_nav += 42

    # ── 2. TOPBAR (x: 300 à 1920, y: 0 à 80) ─────────────────────────────────
    draw.rectangle([300, 0, width, 80], fill='#1B1614')
    draw.line([300, 80, width, 80], fill='#2E241E', width=1)

    # Sélecteur d'établissement
    draw.rounded_rectangle([340, 20, 560, 60], radius=8, fill='#29211C', outline='#3D322B')
    draw.text((360, 30), "Riad Yasmine", fill='#FFFFFF', font=f_nav)
    # Flèche vers le bas
    draw.polygon([(525, 38), (537, 38), (531, 46)], fill='#A89B91')

    # Indicateur Business Date
    draw.rounded_rectangle([1380, 20, 1720, 60], radius=8, fill='#29211C', outline='#3D322B')
    draw.ellipse([1400, 35, 1412, 47], fill='#F1A27A')
    draw.text((1425, 30), "Date Metier : 06/08/2026", fill='#F1A27A', font=f_nav)

    # Profil utilisateur
    draw.ellipse([1760, 22, 1796, 58], fill='#E55A24')
    draw.text((1768, 30), "NB", fill='#FFFFFF', font=ImageFont.truetype(font_bold, 14))
    draw.text((1810, 30), "Nabil B.", fill='#E0D5CE', font=f_nav_sub)

    # ── 3. CONTENU PRINCIPAL (x: 340 à 1880, y: 110 à 1050) ──────────────────
    # En-tête de page
    draw.text((340, 110), "Cloture Journaliere Nocturne (Night Audit)", fill='#FFFFFF', font=f_h1)
    draw.text((340, 160), "Controle d'integrite comptable, facturation automatique des nuitees et avancement de la Business Date.", fill='#9E8F84', font=f_sub)

    # Bannière d'état
    draw.rounded_rectangle([340, 200, 1860, 280], radius=12, fill='#241B16', outline='#E55A24', width=2)
    draw.ellipse([365, 220, 405, 260], fill='#E55A24')
    draw.ellipse([377, 232, 393, 248], fill='#FFFFFF')
    draw.text((425, 222), "Statut d'Exploitation : Session Nocturne Prete pour Cloture", fill='#FFFFFF', font=f_card_title)
    draw.text((425, 250), "Etablissement : Riad Yasmine  |  Date Metier : 06 Aout 2026  |  Prochaine Date : 07 Aout 2026", fill='#A89B91', font=f_card_sub)
    
    # Badge équilibré
    draw.rounded_rectangle([1630, 220, 1835, 260], radius=8, fill='#1B7E4B')
    draw.ellipse([1645, 235, 1653, 243], fill='#FFFFFF')
    draw.text((1665, 230), "Equilibre (0 MAD)", fill='#FFFFFF', font=f_nav)

    # ── GRILLE 3 CARTES DU WORKFLOW NIGHT AUDIT ──────────────────────────────
    # Carte 1 : Contrôle des Mouvements (x: 340 à 820)
    c1_x1, c1_x2 = 340, 820
    draw.rounded_rectangle([c1_x1, 310, c1_x2, 680], radius=12, fill='#201915', outline='#352B24')
    draw.text((c1_x1 + 25, 335), "1. Controle des Flux Sejours", fill='#FFFFFF', font=f_card_title)
    draw.line([c1_x1 + 25, 375, c1_x2 - 25, 375], fill='#2E241E', width=1)

    checks = [
        ("Arrivees du jour (Check-in)", "8 / 8 Enregistrees", True),
        ("Departs du jour (Check-out)", "6 / 6 Factures & Regles", True),
        ("Arrivees en suspens", "0 en attente", True),
        ("Departs en suspens", "0 en attente", True),
        ("Traitement des No-Shows", "1 Cloture avec frais", True),
        ("Chambres occupees ce soir", "14 Chambres (93.3%)", True),
    ]
    y_chk = 395
    for label, val, is_ok in checks:
        # Puce verte
        draw.ellipse([c1_x1 + 25, y_chk + 3, c1_x1 + 35, y_chk + 13], fill='#1B7E4B')
        draw.text((c1_x1 + 45, y_chk), label, fill='#E0D5CE', font=f_card_sub)
        draw.text((c1_x2 - 180, y_chk), val, fill='#1B7E4B' if is_ok else '#E55A24', font=ImageFont.truetype(font_bold, 14))
        y_chk += 44

    # Carte 2 : Balance Comptable (x: 850 à 1360)
    c2_x1, c2_x2 = 850, 1360
    draw.rounded_rectangle([c2_x1, 310, c2_x2, 680], radius=12, fill='#201915', outline='#352B24')
    draw.text((c2_x1 + 25, 335), "2. Balance Financiere Journaliere", fill='#FFFFFF', font=f_card_title)
    draw.line([c2_x1 + 25, 375, c2_x2 - 25, 375], fill='#2E241E', width=1)

    # Blocs KPI Débits / Crédits
    draw.rounded_rectangle([c2_x1 + 25, 395, c2_x1 + 230, 485], radius=8, fill='#29211C', outline='#3D322B')
    draw.text((c2_x1 + 40, 408), "TOTAL DEBITS", fill='#A89B91', font=f_kpi_lbl)
    draw.text((c2_x1 + 40, 435), "24 650.00 MAD", fill='#FFFFFF', font=f_kpi_val)

    draw.rounded_rectangle([c2_x1 + 255, 395, c2_x2 - 25, 485], radius=8, fill='#29211C', outline='#3D322B')
    draw.text((c2_x1 + 270, 408), "TOTAL CREDITS", fill='#A89B91', font=f_kpi_lbl)
    draw.text((c2_x1 + 270, 435), "24 650.00 MAD", fill='#FFFFFF', font=f_kpi_val)

    # Détails taxes
    draw.text((c2_x1 + 25, 510), "Detail Fiscal Reglementaire Marocain :", fill='#F1A27A', font=ImageFont.truetype(font_bold, 14))
    draw.text((c2_x1 + 25, 540), "- TVA Hebergement (10%) :", fill='#A89B91', font=f_card_sub)
    draw.text((c2_x2 - 130, 540), "2 145.45 MAD", fill='#E0D5CE', font=f_mono)

    draw.text((c2_x1 + 25, 575), "- Taxe de Sejour Communale (TS) :", fill='#A89B91', font=f_card_sub)
    draw.text((c2_x2 - 130, 575), "550.00 MAD", fill='#E0D5CE', font=f_mono)

    draw.text((c2_x1 + 25, 610), "- Taxe Promo Touristique (TPT) :", fill='#A89B91', font=f_card_sub)
    draw.text((c2_x2 - 130, 610), "264.00 MAD", fill='#E0D5CE', font=f_mono)

    draw.text((c2_x1 + 25, 645), "Ecart Debits / Credits :", fill='#1B7E4B', font=ImageFont.truetype(font_bold, 15))
    draw.text((c2_x2 - 130, 645), "0.00 MAD (OK)", fill='#1B7E4B', font=ImageFont.truetype(font_bold, 15))

    # Carte 3 : Action de Clôture & Rapports (x: 1390 à 1860)
    c3_x1, c3_x2 = 1390, 1860
    draw.rounded_rectangle([c3_x1, 310, c3_x2, 680], radius=12, fill='#201915', outline='#352B24')
    draw.text((c3_x1 + 25, 335), "3. Execution de la Cloture", fill='#FFFFFF', font=f_card_title)
    draw.line([c3_x1 + 25, 375, c3_x2 - 25, 375], fill='#2E241E', width=1)

    draw.text((c3_x1 + 25, 395), "Actions transactionnelles declenchees :", fill='#A89B91', font=f_card_sub)
    draw.text((c3_x1 + 25, 425), "1. Facturation en masse des nuitees", fill='#E0D5CE', font=ImageFont.truetype(font_reg, 14))
    draw.text((c3_x1 + 25, 455), "2. Verrouillage des folios de la date 06/08", fill='#E0D5CE', font=ImageFont.truetype(font_reg, 14))
    draw.text((c3_x1 + 25, 485), "3. Generation & Signature PDF S3 MinIO", fill='#E0D5CE', font=ImageFont.truetype(font_reg, 14))
    draw.text((c3_x1 + 25, 515), "4. Incrementation Date Metier -> 07/08/2026", fill='#E0D5CE', font=ImageFont.truetype(font_reg, 14))

    # Bouton de clôture actif
    draw.rounded_rectangle([c3_x1 + 25, 585, c3_x2 - 25, 650], radius=10, fill='#E55A24')
    draw.text(((c3_x1 + c3_x2) // 2, 617), "LANCER LE NIGHT AUDIT", fill='#FFFFFF', font=f_btn, anchor="mm")

    # ── 4. TABLEAU DES RAPPORTS GÉNÉRÉS EN BAS (y: 710 à 1020) ────────────────
    draw.rounded_rectangle([340, 710, 1860, 1020], radius=12, fill='#201915', outline='#352B24')
    draw.text((365, 735), "Historique & Rapports Financiers Journaliers (Stockage MinIO S3)", fill='#FFFFFF', font=f_card_title)
    draw.line([365, 770, 1835, 770], fill='#2E241E', width=1)

    headers = [("Date Metier", 365), ("Total Encaissements", 560), ("RevPAR / ADR", 820), ("Empreinte SHA-256 (Immuable)", 1080), ("Statut", 1520), ("Actions", 1680)]
    for h_txt, h_x in headers:
        draw.text((h_x, 785), h_txt, fill='#8A7D74', font=ImageFont.truetype(font_bold, 13))

    reports = [
        ("05/08/2026", "21 800.00 MAD", "1 180 MAD / 88%", "sha256:7f3a9e...c81b", "Cloture", "Telecharger PDF"),
        ("04/08/2026", "19 450.00 MAD", "1 050 MAD / 80%", "sha256:4b2d1c...99a0", "Cloture", "Telecharger PDF"),
        ("03/08/2026", "23 100.00 MAD", "1 250 MAD / 93%", "sha256:9a8e7f...12dd", "Cloture", "Telecharger PDF"),
        ("02/08/2026", "18 900.00 MAD", "1 020 MAD / 75%", "sha256:1c5d88...63ee", "Cloture", "Telecharger PDF"),
    ]
    y_rep = 825
    for dt, enc, rev, sha, st, act in reports:
        draw.line([365, y_rep - 8, 1835, y_rep - 8], fill='#28201B', width=1)
        draw.text((365, y_rep), dt, fill='#FFFFFF', font=f_mono)
        draw.text((560, y_rep), enc, fill='#E0D5CE', font=f_mono)
        draw.text((820, y_rep), rev, fill='#E0D5CE', font=f_mono)
        draw.text((1080, y_rep), sha, fill='#F1A27A', font=f_mono)
        draw.ellipse([1505, y_rep + 4, 1513, y_rep + 12], fill='#1B7E4B')
        draw.text((1520, y_rep), st, fill='#1B7E4B', font=ImageFont.truetype(font_bold, 13))
        draw.text((1680, y_rep), act, fill='#E55A24', font=ImageFont.truetype(font_bold, 13))
        y_rep += 44

    # Sauvegarde
    img.save(OUT_FIG, quality=95)
    img.save(OUT_PIC, quality=95)
    print(f"[SUCCES] Capture d'ecran Night Audit haute definition generee : {OUT_FIG}")

if __name__ == '__main__':
    generate_night_audit_ui()
