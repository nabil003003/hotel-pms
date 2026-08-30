#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Intercalaires et Pages de Titre de Chapitres (Thème Vert Prairie)
Chaque chapitre dispose d'une page de titre dédiée, élégamment mise en page
avec le numéro, le titre complet en grand, le sous-titre et l'encadré des objectifs et sommaire en Vert Prairie.
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm

C_VERT_PRAIRIE = HexColor('#2E7D32')       # Vert prairie soutenu (#2E7D32)
C_VERT_PRAIRIE_BG = HexColor('#E8F5E9')    # Fond vert prairie très doux (#E8F5E9)
C_VERT_PRAIRIE_ACCENT = HexColor('#388E3C')# Vert prairie vibrant (#388E3C)
C_DARK = HexColor('#1A2E1C')               # Vert sombre textuel

def make_chapter_cover(chap_num_str, chap_title, chap_theme, sections_list, styles, usable_width):
    story = []
    
    story.append(Spacer(1, 3.2 * cm))
    
    # ── EN-TÊTE NUMÉRO DE CHAPITRE VERT PRAIRIE ─────────────────────────────
    p_num = Paragraph(
        f"<font color='{C_VERT_PRAIRIE.hexval()}' size='18'><b>{chap_num_str.upper()}</b></font>",
        styles['CoverInstitution']
    )
    story.append(p_num)
    story.append(Spacer(1, 10))
    
    # Ligne horizontale décorative Vert Prairie
    story.append(HRFlowable(width="100%", thickness=2.5, color=C_VERT_PRAIRIE, spaceBefore=0, spaceAfter=16))
    
    # ── GRAND TITRE DU CHAPITRE ─────────────────────────────────────────────
    p_title = Paragraph(
        f"<font color='#1B5E20' size='21'><b>{chap_title.upper()}</b></font>",
        styles['CoverTitle']
    )
    story.append(p_title)
    story.append(Spacer(1, 8))
    
    # ── SOUS-TITRE / THÉMATIQUE DU CHAPITRE ──────────────────────────────────
    if chap_theme:
        p_theme = Paragraph(
            f"<font color='{C_VERT_PRAIRIE_ACCENT.hexval()}' size='11.5'><b>{chap_theme}</b></font>",
            styles['CoverSubtitle']
        )
        story.append(p_theme)
        story.append(Spacer(1, 16))
        
    # ── ENCADRÉ OBJECTIFS ET SOMMAIRE EN VERT PRAIRIE DOUX ──────────────────
    summary_content = [
        Paragraph(f"<b><font size='10.5' color='{C_VERT_PRAIRIE.hexval()}'>OBJECTIFS ET SOMMAIRE DU CHAPITRE :</font></b>", styles['Sec3Title']),
        Spacer(1, 6)
    ]
    for sec in sections_list:
        summary_content.append(Paragraph(f"&bull;&nbsp;&nbsp;<b>{sec}</b>", styles['TblCellBold']))
        summary_content.append(Spacer(1, 2.5))
        
    t_summary = Table([[summary_content]], colWidths=[usable_width])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_VERT_PRAIRIE_BG),
        ('BOX', (0,0), (-1,-1), 1.5, C_VERT_PRAIRIE),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 2 * cm))
    
    # Ligne inférieure de finition
    story.append(HRFlowable(width="100%", thickness=1.0, color=C_VERT_PRAIRIE, spaceBefore=8, spaceAfter=0))
    story.append(PageBreak())
    
    return story
