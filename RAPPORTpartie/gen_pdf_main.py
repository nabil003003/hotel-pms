#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapport de Stage — PMS Alidentec
Generateur PDF principal — ReportLab 5
"""
import os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon
from reportlab.graphics import renderPDF
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, NextPageTemplate
from reportlab.platypus.flowables import Flowable

# ── Couleurs ──────────────────────────────────────────────────────────────────
BLUE   = HexColor('#004B87')
GOLD   = HexColor('#B48C00')
LGRAY  = HexColor('#F5F5F5')
DGRAY  = HexColor('#333333')
GREEN  = HexColor('#007850')
LBLUE  = HexColor('#E8F0F8')

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
FIG  = os.path.join(BASE, 'figures')
OUT  = os.path.join(BASE, 'RAPPORT_ALIDENTEC_PMS.pdf')
W, H = A4   # 595.27 x 841.89 pts

# ── Helpers ───────────────────────────────────────────────────────────────────
def fig(name):
    p = os.path.join(FIG, name)
    return p if os.path.exists(p) else None

def img(name, width=14*cm, caption=None):
    """Retourne [Image, Spacer, Caption] ou []"""
    p = fig(name)
    if not p:
        return []
    items = [Spacer(1, 4*mm), Image(p, width=width, kind='proportional')]
    if caption:
        items.append(Paragraph(caption, ST['caption']))
    items.append(Spacer(1, 4*mm))
    return items

def tbl(data, colWidths=None, hdr=True, caption=None):
    """Table formatée"""
    if colWidths is None:
        n = len(data[0])
        colWidths = [14*cm/n]*n
    style = [
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR',  (0,0), (-1,0), white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 9),
        ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
        ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',   (0,1), (-1,-1), 9),
        ('GRID',       (0,0), (-1,-1), 0.5, HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, LGRAY]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]
    items = [Spacer(1,3*mm), Table(data, colWidths=colWidths, style=TableStyle(style),
                                   repeatRows=1, hAlign='LEFT')]
    if caption:
        items.append(Paragraph(caption, ST['caption']))
    items.append(Spacer(1,4*mm))
    return items

def sec(title, lvl=1):
    """Titre de section"""
    key = {1:'h1', 2:'h2', 3:'h3'}.get(lvl,'h1')
    return [Spacer(1, 5*mm), Paragraph(title, ST[key]), Spacer(1,2*mm)]

def p(text, style='body'):
    return Paragraph(text, ST[style])

def sp(h=4):
    return Spacer(1, h*mm)

# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    S = {}
    def add(name, **kw):
        S[name] = ParagraphStyle(name, **kw)

    add('body',    fontName='Helvetica', fontSize=11, leading=17,
                   alignment=TA_JUSTIFY, textColor=DGRAY, spaceAfter=4)
    add('body_b',  fontName='Helvetica-Bold', fontSize=11, leading=17,
                   alignment=TA_JUSTIFY, textColor=DGRAY)
    add('h1',      fontName='Helvetica-Bold', fontSize=14, leading=20,
                   textColor=BLUE, spaceBefore=8, spaceAfter=4,
                   borderPadding=(0,0,3,0))
    add('h2',      fontName='Helvetica-Bold', fontSize=12, leading=18,
                   textColor=BLUE, spaceBefore=6, spaceAfter=3)
    add('h3',      fontName='Helvetica-Bold', fontSize=11, leading=16,
                   textColor=DGRAY, spaceBefore=4, spaceAfter=2)
    add('caption', fontName='Helvetica-Oblique', fontSize=9, leading=12,
                   alignment=TA_CENTER, textColor=BLUE, spaceAfter=2)
    add('toc_ch',  fontName='Helvetica-Bold', fontSize=12, textColor=BLUE,
                   leading=18, spaceBefore=4)
    add('toc_sec', fontName='Helvetica', fontSize=10, textColor=DGRAY,
                   leading=14, leftIndent=1*cm)
    add('bullet',  fontName='Helvetica', fontSize=10.5, leading=16,
                   leftIndent=1*cm, bulletIndent=0.5*cm, textColor=DGRAY,
                   spaceAfter=2, bulletText='•')
    add('cover_t', fontName='Helvetica-Bold', fontSize=22, leading=28,
                   alignment=TA_CENTER, textColor=BLUE)
    add('cover_s', fontName='Helvetica-Bold', fontSize=13, leading=18,
                   alignment=TA_CENTER, textColor=GOLD)
    add('cover_n', fontName='Helvetica', fontSize=12, leading=16,
                   alignment=TA_CENTER, textColor=DGRAY)
    add('chap',    fontName='Helvetica-Bold', fontSize=20, leading=28,
                   textColor=BLUE, spaceBefore=6, spaceAfter=8,
                   alignment=TA_LEFT)
    add('chap_num',fontName='Helvetica-Bold', fontSize=13, leading=18,
                   textColor=GOLD, spaceAfter=2)
    add('footer',  fontName='Helvetica', fontSize=8, textColor=HexColor('#888888'),
                   alignment=TA_CENTER)
    add('abst',    fontName='Helvetica-Oblique', fontSize=10.5, leading=16,
                   alignment=TA_JUSTIFY, textColor=DGRAY, leftIndent=1*cm,
                   rightIndent=1*cm)
    add('kw',      fontName='Helvetica-Bold', fontSize=10, textColor=BLUE)
    return S

ST = make_styles()

# ── Templates de page ─────────────────────────────────────────────────────────
class HeaderFooter:
    def __init__(self, title=''):
        self.title = title

    def __call__(self, canvas, doc):
        canvas.saveState()
        # En-tête
        canvas.setFillColor(BLUE)
        canvas.rect(2*cm, H-1.8*cm, W-4*cm, 0.5*mm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(BLUE)
        canvas.drawString(2*cm, H-1.6*cm, self.title)
        canvas.drawRightString(W-2*cm, H-1.6*cm, 'Alidentec — Rapport de Stage 2025–2026')
        # Pied
        canvas.setFillColor(BLUE)
        canvas.rect(2*cm, 1.5*cm, W-4*cm, 0.5*mm, fill=1, stroke=0)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredString(W/2, 1.2*cm, f'— {doc.page} —')
        canvas.drawString(2*cm, 1.2*cm, 'PMS Hôtelier Multi-Établissements')
        canvas.drawRightString(W-2*cm, 1.2*cm, 'Confidentiel — Usage Pédagogique')
        canvas.restoreState()

def cover_page_tmpl(canvas, doc):
    canvas.saveState()
    # Fond dégradé simulé
    canvas.setFillColor(BLUE)
    canvas.rect(0, H-5*cm, W, 5*cm, fill=1, stroke=0)
    canvas.setFillColor(HexColor('#F8F8F8'))
    canvas.rect(0, 0, W, H-5*cm, fill=1, stroke=0)
    # Barre bas
    canvas.setFillColor(GOLD)
    canvas.rect(0, 0, W, 1.5*cm, fill=1, stroke=0)
    canvas.restoreState()

# ── Chapitre helper ────────────────────────────────────────────────────────────
def chapter_header(num, title):
    d = Drawing(W-4*cm, 2.5*cm)
    d.add(Rect(0, 0, W-4*cm, 2.5*cm, fillColor=LBLUE, strokeColor=BLUE, strokeWidth=1))
    d.add(Rect(0, 0, 0.6*cm, 2.5*cm, fillColor=BLUE, strokeColor=None))
    d.add(String(1*cm*28.35/cm, 1.5*cm*28.35/cm,
                 f'Chapitre {num}', fontName='Helvetica', fontSize=10, fillColor=GOLD))
    d.add(String(1*cm*28.35/cm, 0.6*cm*28.35/cm,
                 title, fontName='Helvetica-Bold', fontSize=16, fillColor=BLUE))
    return d

from chapter1 import build_ch1
from chapter2 import build_ch2
from chapter3 import build_ch3
from chapter4 import build_ch4
from chapter5 import build_ch5
from chapter6 import build_ch6
from prelim  import build_prelim
from concl   import build_concl

# ── Document ──────────────────────────────────────────────────────────────────
def build_pdf():
    doc = BaseDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=3*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        title='Rapport de Stage — PMS Alidentec',
        author='Nabil BOUDARINE, Youssef OUIZZA, Hamza IBN TALIB',
    )
    frame_cover = Frame(0, 0, W, H, id='cover')
    frame_body  = Frame(3*cm, 2.5*cm, W-5.5*cm, H-5*cm, id='body')

    doc.addPageTemplates([
        PageTemplate(id='Cover',  frames=[frame_cover], onPage=cover_page_tmpl),
        PageTemplate(id='Normal', frames=[frame_body],  onPage=HeaderFooter()),
    ])

    story = []
    story += build_prelim()
    story += build_ch1()
    story += build_ch2()
    story += build_ch3()
    story += build_ch4()
    story += build_ch5()
    story += build_ch6()
    story += build_concl()

    doc.build(story)
    print(f'✅ PDF généré : {OUT}')

if __name__ == '__main__':
    build_pdf()
