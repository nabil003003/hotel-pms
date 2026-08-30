import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de la Page de Garde Officielle EMSI conforme au modèle exact (template de rapport.pdf)
Utilise le cadre graphique officiel avec le logo EMSI, la filière IIR,
le cartouche d'entreprise Alidentec, le thème PFA et les élèves-ingénieurs.
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
PREV_DIR = os.path.join(BASE_DIR, 'pdf_previews')
os.makedirs(FIG_DIR, exist_ok=True)

TEMPLATE_BG = os.path.join(PREV_DIR, 'extracted_img_132.png')
OUT_COVER_IMG = os.path.join(FIG_DIR, 'official_cover_page.png')

def generate_official_cover_image():
    # Charger l'image de fond du template (595x842) et redimensionner en haute résolution (2480x3508 @ 300 DPI)
    bg = Image.open(TEMPLATE_BG).convert('RGBA')
    bg = bg.resize((2480, 3508), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(bg)

    # Polices TrueType
    font_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_reg = "C:/Windows/Fonts/arial.ttf"
    font_italic = "C:/Windows/Fonts/ariali.ttf"
    if not os.path.exists(font_bold):
        font_bold = "arial.ttf"
        font_reg = "arial.ttf"
        font_italic = "arial.ttf"

    f_filiere = ImageFont.truetype(font_bold, 58)
    f_badge = ImageFont.truetype(font_bold, 62)
    f_year = ImageFont.truetype(font_bold, 52)
    f_title = ImageFont.truetype(font_bold, 56)
    f_subtitle = ImageFont.truetype(font_italic, 36)
    f_company = ImageFont.truetype(font_bold, 50)
    f_company_sub = ImageFont.truetype(font_reg, 32)
    f_names = ImageFont.truetype(font_bold, 44)
    f_names_sub = ImageFont.truetype(font_reg, 36)
    f_date = ImageFont.truetype(font_bold, 42)

    C_BLUE = (41, 171, 226, 255)       # Bleu template EMSI
    C_GREEN = (27, 94, 32, 255)        # Vert sombre EMSI
    C_DARK = (30, 30, 30, 255)         # Noir texte
    C_GRAY = (80, 80, 80, 255)         # Gris métadonnées

    # 1. Masquer et Remplacer "LOGO DE L'ENTREPRISE" par le Cartouche Alidentec
    draw.rectangle([340, 160, 1100, 480], fill=(255, 255, 255, 255))
    draw.text((720, 260), "ALIDENTEC", fill=(10, 59, 114, 255), font=f_company, anchor="mm")
    draw.text((720, 330), "Société de Développement de Solutions Logicielles", fill=C_GRAY, font=f_company_sub, anchor="mm")
    draw.text((720, 380), "Transformation Digitale & Cloud-Native", fill=C_GRAY, font=f_company_sub, anchor="mm")

    # 2. Masquer et Remplacer le Badge "IAII" par "IIR"
    draw.rectangle([115, 770, 310, 990], fill=C_BLUE)
    draw.text((212, 880), "IIR", fill=(255, 255, 255, 255), font=f_badge, anchor="mm")

    # 3. Masquer et Remplacer la Filière "INGÉNIERIE DES AUTOMATISMES..." par "INGÉNIERIE INFORMATIQUE ET RÉSEAUX"
    draw.rectangle([380, 800, 2200, 1180], fill=(255, 255, 255, 255))
    draw.text((420, 860), "INGÉNIERIE INFORMATIQUE & RÉSEAUX", fill=C_BLUE, font=f_filiere)
    draw.text((420, 940), "Option : Génie Logiciel & Systèmes d'Information", fill=C_GRAY, font=ImageFont.truetype(font_italic, 40))

    # 4. Année Universitaire 2025-2026
    draw.rectangle([1400, 1340, 2150, 1500], fill=(255, 255, 255, 255))
    draw.text((1770, 1420), "2025 &ndash; 2026".replace('&ndash;', '–'), fill=C_DARK, font=f_year, anchor="mm")

    # 5. Zone THÈME : Effacer les pointillés et insérer le Titre Officiel du Projet PMS
    draw.rectangle([160, 2280, 2150, 2750], fill=(255, 255, 255, 255))
    
    # Titre du Projet
    draw.text((1155, 2350), "CONCEPTION ET RÉALISATION D'UNE PLATEFORME", fill=C_GREEN, font=f_title, anchor="mm")
    draw.text((1155, 2430), "PMS HÔTELIÈRE MULTI-ÉTABLISSEMENTS", fill=C_GREEN, font=f_title, anchor="mm")
    
    # Sous-titre technologique
    draw.text((1155, 2540), "Architecture Microservices Distribuée • Next.js 14 • FastAPI • WebAuthn FIDO2", fill=C_GRAY, font=f_subtitle, anchor="mm")
    draw.text((1155, 2600), "PostgreSQL • Redis Redlock • RabbitMQ • MinIO S3 • Docker", fill=C_GRAY, font=f_subtitle, anchor="mm")

    # 6. Zone RÉALISÉ PAR (Élèves-Ingénieurs)
    draw.rectangle([980, 3050, 2150, 3320], fill=(255, 255, 255, 255))
    draw.text((1000, 3100), "Nabil BOUDARINE", fill=C_DARK, font=f_names)
    draw.text((1000, 3170), "Youssef OUIZZA", fill=C_DARK, font=f_names)
    draw.text((1000, 3240), "Hamza IBN TALIB", fill=C_DARK, font=f_names)

    # 7. Zone ENCADRÉ PAR (Encadrants Professionnel & Pédagogique)
    draw.rectangle([980, 3420, 2150, 3620], fill=(255, 255, 255, 255))
    # Encadrant Professionnel
    draw.text((1000, 3440), "Lead Architect", fill=C_DARK, font=f_names)
    draw.text((1000, 3495), "(Encadrant Professionnel — Alidentec)", fill=C_GRAY, font=f_names_sub)

    # Encadrant Pédagogique
    draw.text((1000, 3555), "Professeur Habilité", fill=C_DARK, font=f_names)
    draw.text((1000, 3610), "(Encadrant Pédagogique — EMSI Marrakech)", fill=C_GRAY, font=f_names_sub)

    # 8. Zone SOUTENU LE
    draw.rectangle([980, 3750, 2150, 3900], fill=(255, 255, 255, 255))
    draw.text((1000, 3760), "Session de Juin 2026  •  Marrakech, Maroc", fill=C_DARK, font=f_date)

    # Sauvegarder l'image finale
    bg.save(OUT_COVER_IMG, quality=100)
    print(f"[SUCCÈS] Page de garde officielle générée : {OUT_COVER_IMG}")

if __name__ == '__main__':
    generate_official_cover_image()
