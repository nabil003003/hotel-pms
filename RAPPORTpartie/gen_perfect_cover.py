import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur Haute Précision de la Page de Garde EMSI officielle
- En-tête : "PROJET" et "DE FIN D'ANNÉE" ultra-nets, rendus directement en haute définition
- Logo Entreprise : "ALIDENTEC" uniquement (suppression des sous-titres sous le logo)
- "THÈME" préservé avec sa ligne décorative
- Titre : "PLATEFORME PMS HÔTELIÈRE MULTI-ÉTABLISSEMENTS"
- 3ème étudiant : Mohamed Hamza IBNTALIB
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
PREV_DIR = os.path.join(BASE_DIR, 'pdf_previews')
TEMPLATE_IMG = os.path.join(PREV_DIR, 'extracted_img_132.png')
OUT_COVER_IMG = os.path.join(FIG_DIR, 'official_cover_page.png')
OUT_COVER_PDF = os.path.join(FIG_DIR, 'official_cover_page.pdf')

def build_perfect_cover():
    bg = Image.open(TEMPLATE_IMG).convert('RGBA')
    bg = bg.resize((2480, 3508), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(bg)

    font_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_reg = "C:/Windows/Fonts/arial.ttf"
    font_italic = "C:/Windows/Fonts/ariali.ttf"
    if not os.path.exists(font_bold):
        font_bold = "arial.ttf"
        font_reg = "arial.ttf"
        font_italic = "arial.ttf"

    # Tailles de polices haute résolution (300 DPI)
    f_pfa = ImageFont.truetype(font_bold, 138)
    f_company = ImageFont.truetype(font_bold, 64)
    f_badge = ImageFont.truetype(font_bold, 60)
    f_filiere = ImageFont.truetype(font_bold, 54)
    f_filiere_sub = ImageFont.truetype(font_italic, 36)
    f_year = ImageFont.truetype(font_bold, 46)
    f_title = ImageFont.truetype(font_bold, 54)
    f_names = ImageFont.truetype(font_bold, 38)
    f_roles = ImageFont.truetype(font_reg, 32)
    f_date = ImageFont.truetype(font_bold, 36)

    C_BLUE = (41, 171, 226, 255)       # Bleu template EMSI
    C_EMSI_GREEN = (44, 114, 76, 255)  # Vert officiel EMSI (#2C724C)
    C_DARK = (35, 35, 35, 255)         # Noir texte
    C_GRAY = (90, 90, 90, 255)         # Gris
    C_PRIMARY_NAVY = (10, 59, 114, 255)# Bleu marine

    # 1. LOGO DE L'ENTREPRISE -> "ALIDENTEC" uniquement (sans aucune écriture en-dessous)
    # Zone masquée : x: 320 à 1150, y: 140 à 480
    draw.rectangle([320, 140, 1150, 480], fill=(255, 255, 255, 255))
    draw.text((735, 290), "ALIDENTEC", fill=C_PRIMARY_NAVY, font=f_company, anchor="mm")

    # 2. BADGE IAII -> IIR
    draw.rectangle([115, 640, 312, 860], fill=C_BLUE)
    draw.text((213, 750), "IIR", fill=(255, 255, 255, 255), font=f_badge, anchor="mm")

    # 3. FILIERE : "INGÉNIERIE INFORMATIQUE & RÉSEAUX"
    draw.rectangle([500, 680, 2200, 980], fill=(255, 255, 255, 255))
    draw.text((560, 740), "INGÉNIERIE INFORMATIQUE & RÉSEAUX", fill=C_BLUE, font=f_filiere, anchor="lm")
    draw.text((560, 830), "Option : Génie Logiciel & Systèmes d'Information", fill=C_GRAY, font=f_filiere_sub, anchor="lm")

    # 4. ANNÉE UNIVERSITAIRE -> 2025-2026
    draw.rectangle([1380, 1200, 2150, 1330], fill=(255, 255, 255, 255))
    draw.text((1765, 1260), "2025 – 2026", fill=C_DARK, font=f_year, anchor="mm")

    # 5. RENDU NET ET ULTRA-CLAIR DE "PROJET DE FIN D'ANNÉE"
    # Effacement complet de l'ancienne zone floue (y: 1280 à 1740)
    draw.rectangle([115, 1280, 1950, 1740], fill=(255, 255, 255, 255))
    # Rendu vectoriel net des deux lignes
    draw.text((140, 1420), "PROJET", fill=C_EMSI_GREEN, font=f_pfa, anchor="lm")
    draw.text((140, 1590), "DE FIN D'ANNÉE", fill=C_EMSI_GREEN, font=f_pfa, anchor="lm")

    # 6. THÈME DU PROJET : Uniquement "PLATEFORME PMS HÔTELIÈRE MULTI-ÉTABLISSEMENTS"
    # Effacement uniquement des pointillés sous la ligne de THÈME : y: 1960 à 2450
    draw.rectangle([140, 1960, 2180, 2450], fill=(255, 255, 255, 255))
    draw.text((1160, 2120), "PLATEFORME", fill=C_EMSI_GREEN, font=f_title, anchor="mm")
    draw.text((1160, 2220), "PMS HÔTELIÈRE MULTI-ÉTABLISSEMENTS", fill=C_EMSI_GREEN, font=f_title, anchor="mm")

    # 7. RÉALISÉ PAR (Élèves-Ingénieurs : Mohamed Hamza IBNTALIB)
    draw.rectangle([960, 2600, 2180, 2870], fill=(255, 255, 255, 255))
    draw.text((980, 2650), "Nabil BOUDARINE", fill=C_DARK, font=f_names)
    draw.text((980, 2720), "Youssef OUIZZA", fill=C_DARK, font=f_names)
    draw.text((980, 2790), "Mohamed Hamza IBNTALIB", fill=C_DARK, font=f_names)

    # 8. ENCADRÉ PAR
    draw.rectangle([960, 2940, 2180, 3230], fill=(255, 255, 255, 255))
    draw.text((980, 2980), "Lead Architect", fill=C_DARK, font=f_names)
    draw.text((980, 3035), "(Encadrant Professionnel — Alidentec)", fill=C_GRAY, font=f_roles)
    draw.text((980, 3100), "Professeur Habilité", fill=C_DARK, font=f_names)
    draw.text((980, 3155), "(Encadrant Pédagogique — EMSI Marrakech)", fill=C_GRAY, font=f_roles)

    # 9. SOUTENU LE
    draw.rectangle([960, 3280, 2180, 3430], fill=(255, 255, 255, 255))
    draw.text((980, 3350), "Session de Septembre 2026  •  Marrakech, Maroc", fill=C_DARK, font=f_date, anchor="lm")

    # Sauvegarder
    bg_rgb = bg.convert('RGB')
    bg_rgb.save(OUT_COVER_IMG, quality=100)
    bg_rgb.save(OUT_COVER_PDF, "PDF", resolution=300.0)
    print(f"[SUCCÈS] Page de garde officielle générée : {OUT_COVER_IMG}")

if __name__ == '__main__':
    build_perfect_cover()
