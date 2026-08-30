import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur Vectoriel de la Page de Garde EMSI officielle
À partir de la page 1 de 'template de rapport.pdf', applique les remplacements exacts
pour Alidentec, la filière IIR, le thème du PMS hôtelier et le trinôme d'élèves-ingénieurs.
"""

import os
import fitz  # PyMuPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
PREV_DIR = os.path.join(BASE_DIR, 'pdf_previews')
TEMPLATE_PDF = os.path.join(BASE_DIR, 'template de rapport.pdf')
OUT_COVER_PDF = os.path.join(FIG_DIR, 'official_cover_page.pdf')
OUT_COVER_PNG = os.path.join(PREV_DIR, 'official_cover_page_vector.png')

def generate_vector_cover():
    doc = fitz.open(TEMPLATE_PDF)
    page = doc[0] # Page 1 du template

    # 1. Nettoyer les zones de texte initiales avec des rectangles de masquage blanc
    # A. Logo entreprise (Haut Gauche)
    page.draw_rect(fitz.Rect(50, 40, 280, 110), color=None, fill=(1, 1, 1))

    # B. Badge IAII
    page.draw_rect(fitz.Rect(25, 185, 75, 235), color=None, fill=(0.16, 0.67, 0.89)) # Bleu EMSI

    # C. Filière (Haut Centre)
    page.draw_rect(fitz.Rect(100, 195, 520, 270), color=None, fill=(1, 1, 1))

    # D. Année Universitaire
    page.draw_rect(fitz.Rect(320, 315, 520, 360), color=None, fill=(1, 1, 1))

    # E. Zone Pointillés Thème
    page.draw_rect(fitz.Rect(40, 545, 520, 660), color=None, fill=(1, 1, 1))

    # F. Zone Réalisé Par
    page.draw_rect(fitz.Rect(230, 725, 520, 785), color=None, fill=(1, 1, 1))

    # G. Zone Encadré Par
    page.draw_rect(fitz.Rect(230, 800, 520, 875), color=None, fill=(1, 1, 1))

    # H. Zone Soutenu Le
    page.draw_rect(fitz.Rect(230, 890, 520, 930), color=None, fill=(1, 1, 1))

    # I. Pied de page du template (1 / Rapport PFE)
    page.draw_rect(fitz.Rect(40, 790, 560, 840), color=None, fill=(1, 1, 1))

    # ── 2. Insérer les Textes du Projet PMS Alidentec ────────────────────────
    # A. Cartouche Alidentec
    page.insert_text(fitz.Point(60, 68), "ALIDENTEC", fontsize=14, fontname="helv", fontfile=None, color=(0.04, 0.23, 0.45))
    page.insert_text(fitz.Point(60, 82), "Société de Développement de Solutions Logicielles", fontsize=8.5, fontname="helv", color=(0.3, 0.3, 0.3))
    page.insert_text(fitz.Point(60, 94), "Transformation Digitale & Architectures Cloud-Native", fontsize=8.0, fontname="helv", color=(0.4, 0.4, 0.4))

    # B. Badge IIR
    page.insert_text(fitz.Point(36, 218), "IIR", fontsize=16, fontname="helv", color=(1, 1, 1))

    # C. Filière IIR
    page.insert_text(fitz.Point(105, 215), "INGÉNIERIE INFORMATIQUE & RÉSEAUX", fontsize=14.5, fontname="helv", color=(0.16, 0.67, 0.89))
    page.insert_text(fitz.Point(105, 233), "Option : Génie Logiciel & Systèmes d'Information", fontsize=10, fontname="helv", color=(0.35, 0.35, 0.35))

    # D. Année Universitaire
    page.insert_text(fitz.Point(400, 335), "2025 – 2026", fontsize=12.5, fontname="helv", color=(0.15, 0.15, 0.15))

    # E. Thème du Projet PMS
    p_theme1 = "CONCEPTION ET RÉALISATION D'UNE PLATEFORME"
    p_theme2 = "PMS HÔTELIÈRE MULTI-ÉTABLISSEMENTS"
    p_sub1 = "Architecture Microservices Distribuée • Next.js 14 • FastAPI • WebAuthn FIDO2"
    p_sub2 = "PostgreSQL • Redis Redlock • RabbitMQ • MinIO S3 • Docker"
    
    page.insert_text(fitz.Point(55, 570), p_theme1, fontsize=13, fontname="helv", color=(0.11, 0.37, 0.13))
    page.insert_text(fitz.Point(55, 590), p_theme2, fontsize=13, fontname="helv", color=(0.11, 0.37, 0.13))
    page.insert_text(fitz.Point(55, 615), p_sub1, fontsize=8.5, fontname="helv", color=(0.25, 0.25, 0.25))
    page.insert_text(fitz.Point(55, 630), p_sub2, fontsize=8.5, fontname="helv", color=(0.25, 0.25, 0.25))

    # F. Réalisé par
    page.insert_text(fitz.Point(235, 735), "• Nabil BOUDARINE", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
    page.insert_text(fitz.Point(235, 750), "• Youssef OUIZZA", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
    page.insert_text(fitz.Point(235, 765), "• Hamza IBN TALIB", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))

    # G. Encadré par
    page.insert_text(fitz.Point(235, 815), "• Lead Architect (Encadrant Professionnel — Alidentec)", fontsize=9, fontname="helv", color=(0.15, 0.15, 0.15))
    page.insert_text(fitz.Point(235, 835), "• Professeur Habilité (Encadrant Pédagogique — EMSI Marrakech)", fontsize=9, fontname="helv", color=(0.15, 0.15, 0.15))

    # H. Soutenu le
    page.insert_text(fitz.Point(235, 905), "Session de Juin 2026 • Marrakech, Maroc", fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))

    # Sauvegarder la nouvelle page de garde
    doc_out = fitz.open()
    doc_out.insert_pdf(doc, from_page=0, to_page=0)
    doc_out.save(OUT_COVER_PDF)
    doc_out[0].get_pixmap(dpi=150).save(OUT_COVER_PNG)
    print(f"[SUCCÈS] Page de garde vectorielle officielle enregistrée : {OUT_COVER_PDF}")
    print(f"[PREVIEW] Image générée : {OUT_COVER_PNG}")

if __name__ == '__main__':
    generate_vector_cover()
