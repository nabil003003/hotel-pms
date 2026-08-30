import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur Maître du Rapport de Stage PFA — Alidentec
Page de garde exacte conforme au modèle officiel 'template de rapport.pdf' (EMSI).
Retrait d'alinéa (espace de début de paragraphe) systématique sur tous les paragraphes.
Pages de titre de chapitres en VERT PRAIRIE, 10 captures d'écran strictement en Chapitre 4,
Chiffres Romains MAJUSCULES (II à X) pour les pages préliminaires.
"""

import os
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Import des modules
from gen_cover_and_prelim import build_preliminaries, to_roman_upper
from gen_intro_generale import build_intro_generale
from gen_chapter_dividers import make_chapter_cover, C_VERT_PRAIRIE, C_VERT_PRAIRIE_BG, C_VERT_PRAIRIE_ACCENT
from gen_chap1_alidentec import build_chap1
from gen_chap2_analyse import build_chap2
from gen_chap3_architecture import build_chap3
from gen_chap4_realisation import build_chap4
from gen_chap5_tests import build_chap5
from gen_chap6_bilan import build_chap6
from gen_conclusion_annexes import build_conclusion_annexes
from gen_perfect_cover import build_perfect_cover

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
OUTPUT_PDF = os.path.join(BASE_DIR, 'RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')
TEMP_BODY_PDF = os.path.join(BASE_DIR, 'temp_report_body.pdf')
OFFICIAL_COVER_PDF = os.path.join(FIG_DIR, 'official_cover_page.pdf')

# Couleurs
C_PRIMARY = HexColor('#0A3B72')     # Bleu Nuit EMSI
C_SECONDARY = HexColor('#C29B38')   # Or sobre
C_ACCENT = HexColor('#0080A0')      # Bleu cyan
C_DARK = HexColor('#222222')        # Texte
C_LIGHT_BG = HexColor('#F4F7FA')    # Fond encadrés
C_BORDER = HexColor('#D0D7DE')      # Bordures
C_GREEN = HexColor('#1B7E4B')       # Succès
C_MUTED = HexColor('#666666')       # Notes

# Dimensions A4
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 2.5 * cm
MARGIN_RIGHT = 2.0 * cm
MARGIN_TOP = 2.5 * cm
MARGIN_BOTTOM = 2.5 * cm
USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# ── Styles Typographiques Académiques avec Retrait d'Alinéa ───────────────────
def get_report_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=21, leading=27,
        textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        'CoverSubtitle', fontName='Helvetica-Bold', fontSize=12, leading=17,
        textColor=C_SECONDARY, alignment=TA_CENTER, spaceAfter=18
    ))
    styles.add(ParagraphStyle(
        'CoverInstitution', fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=C_PRIMARY, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'CoverMeta', fontName='Helvetica', fontSize=10, leading=14,
        textColor=C_DARK, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'ChapTitle', fontName='Helvetica-Bold', fontSize=18, leading=23,
        textColor=C_PRIMARY, spaceBefore=14, spaceAfter=14, keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'Sec1Title', fontName='Helvetica-Bold', fontSize=13, leading=18,
        textColor=C_PRIMARY, spaceBefore=14, spaceAfter=7, keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'Sec2Title', fontName='Helvetica-Bold', fontSize=11.5, leading=16,
        textColor=C_ACCENT, spaceBefore=11, spaceAfter=5, keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        'Sec3Title', fontName='Helvetica-Bold', fontSize=10.5, leading=14.5,
        textColor=C_DARK, spaceBefore=8, spaceAfter=4, keepWithNext=True
    ))
    
    # Paragraphe standard avec ESPACE / RETRAIT D'ALINÉA AU DÉBUT & INTERLIGNE 1.5 (fontSize=11, leading=16.5)
    styles.add(ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=11.0, leading=16.5,
        textColor=C_DARK, alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=6,
        firstLineIndent=20
    ))
    styles.add(ParagraphStyle(
        'BodyBold', fontName='Helvetica-Bold', fontSize=11.0, leading=16.5,
        textColor=C_DARK, alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=6,
        firstLineIndent=20
    ))
    styles.add(ParagraphStyle(
        'ReportBullet', fontName='Helvetica', fontSize=11.0, leading=16.5,
        textColor=C_DARK, alignment=TA_JUSTIFY, leftIndent=16, firstLineIndent=-10, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'FigCaption', fontName='Helvetica-Bold', fontSize=9.0, leading=13,
        textColor=C_PRIMARY, alignment=TA_CENTER, spaceBefore=6, spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        'TblCaption', fontName='Helvetica-Bold', fontSize=9.0, leading=13,
        textColor=C_PRIMARY, alignment=TA_CENTER, spaceBefore=8, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        'TblHeader', fontName='Helvetica-Bold', fontSize=8.5, leading=11.5,
        textColor=white, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'TblCell', fontName='Helvetica', fontSize=8.0, leading=11.5,
        textColor=C_DARK, alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'TblCellBold', fontName='Helvetica-Bold', fontSize=8.0, leading=11.5,
        textColor=C_DARK, alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'TblCellCenter', fontName='Helvetica', fontSize=8.0, leading=11.5,
        textColor=C_DARK, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'CalloutText', fontName='Helvetica-Oblique', fontSize=9.5, leading=14.5,
        textColor=C_DARK, alignment=TA_JUSTIFY
    ))
    styles.add(ParagraphStyle(
        'TocItem', fontName='Helvetica', fontSize=9.5, leading=14.0, textColor=C_DARK
    ))
    styles.add(ParagraphStyle(
        'TocChap', fontName='Helvetica-Bold', fontSize=10.0, leading=15.0, textColor=C_PRIMARY
    ))

    return styles

# ── Custom Numbered Canvas pour le Corps du Rapport ───────────────────────────
class NumberedCanvasBody(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvasBody, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_header_footer(self, total_pages):
        page_num = self._pageNumber

        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(C_MUTED)

        # En-tête
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.6)
        self.line(MARGIN_LEFT, PAGE_HEIGHT - 1.8 * cm, PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 1.8 * cm)
        self.drawString(MARGIN_LEFT, PAGE_HEIGHT - 1.6 * cm, "Rapport de Stage PFA — Alidentec | Plateforme PMS Hôtelière Multi-Établissements")
        self.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, PAGE_HEIGHT - 1.6 * cm, "EMSI Marrakech (2025-2026)")

        # Pied de page
        self.line(MARGIN_LEFT, 1.8 * cm, PAGE_WIDTH - MARGIN_RIGHT, 1.8 * cm)
        self.drawString(MARGIN_LEFT, 1.3 * cm, "N. BOUDARINE — Y. OUIZZA — M. H. IBNTALIB")
        self.drawCentredString(PAGE_WIDTH / 2.0, 1.3 * cm, "— Confidentiel / Alidentec —")
        
        # Numérotation : Chiffres Romains MAJUSCULES pour pages préliminaires (1 à 9 -> I à IX)
        if page_num <= 9:
            roman_str = to_roman_upper(page_num)
            page_display = f"Page {roman_str}"
        else:
            main_page_num = page_num - 9
            total_main_pages = total_pages - 9
            page_display = f"Page {main_page_num} / {total_main_pages}"
            
        self.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, 1.3 * cm, page_display)

        self.restoreState()

# Helpers
def get_fig_flowable(filename, max_width=USABLE_WIDTH*0.92, max_height=7.2*cm, caption=None, styles=None):
    path = os.path.join(FIG_DIR, filename)
    if not os.path.exists(path):
        return [Paragraph(f"<b>[Figure manquante : {filename}]</b>", styles['Body'])]
    
    from PIL import Image as PILImage
    try:
        with PILImage.open(path) as img:
            iw, ih = img.size
            aspect = ih / float(iw)
            w = min(max_width, 14.5 * cm)
            h = w * aspect
            if h > max_height:
                h = max_height
                w = h / aspect
                
            elements = [
                Spacer(1, 4),
                RLImage(path, width=w, height=h),
                Spacer(1, 4)
            ]
            if caption:
                elements.append(Paragraph(caption, styles['FigCaption']))
            elements.append(Spacer(1, 6))
            return [KeepTogether(elements)]
    except Exception as e:
        return [Paragraph(f"<b>[Erreur image {filename} : {e}]</b>", styles['Body'])]

def get_two_figs_flowable(f1, c1, f2, c2, max_h=5.4*cm, styles=None):
    p1 = os.path.join(FIG_DIR, f1)
    p2 = os.path.join(FIG_DIR, f2)
    w_each = (USABLE_WIDTH - 14) / 2.0
    
    def load_img(p):
        if not os.path.exists(p):
            return Paragraph("Image introuvable", styles['Body'])
        from PIL import Image as PILImage
        with PILImage.open(p) as img:
            iw, ih = img.size
            aspect = ih / float(iw)
            w = w_each
            h = w * aspect
            if h > max_h:
                h = max_h
                w = h / aspect
            return RLImage(p, width=w, height=h)
            
    img1 = load_img(p1)
    img2 = load_img(p2)
    
    t_data = [
        [img1, img2],
        [Paragraph(c1, styles['FigCaption']), Paragraph(c2, styles['FigCaption'])]
    ]
    t = Table(t_data, colWidths=[w_each, w_each])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    return [KeepTogether([Spacer(1, 4), t, Spacer(1, 6)])]

def make_callout_flowable(text, title="NOTE TECHNIQUE", styles=None):
    content = [
        Paragraph(f"<b><font color='{C_PRIMARY.hexval()}'>[ {title} ]</font></b>", styles['Sec3Title']),
        Spacer(1, 2),
        Paragraph(text, styles['CalloutText'])
    ]
    t = Table([[content]], colWidths=[USABLE_WIDTH])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1.0, C_PRIMARY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return [KeepTogether([Spacer(1, 4), t, Spacer(1, 6)])]

def make_table_flowable(data, col_widths, caption, styles, alignments=None):
    rows = []
    h_row = [Paragraph(f"<b>{col}</b>", styles['TblHeader']) for col in data[0]]
    rows.append(h_row)
    
    for r_idx, r in enumerate(data[1:]):
        row_cells = []
        for c_idx, cell_txt in enumerate(r):
            align = alignments[c_idx] if alignments else 'left'
            st = styles['TblCellCenter'] if align == 'center' else (styles['TblCellBold'] if c_idx == 0 else styles['TblCell'])
            row_cells.append(Paragraph(str(cell_txt), st))
        rows.append(row_cells)
        
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
    ]
    for i in range(1, len(rows)):
        bg = C_LIGHT_BG if i % 2 == 0 else white
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(t_style))
    
    elements = [
        Spacer(1, 6),
        Paragraph(caption, styles['TblCaption']),
        Spacer(1, 2),
        t,
        Spacer(1, 6)
    ]
    return [KeepTogether(elements)]

# ── Construction Globale avec Fusion de la Page de Garde Officielle ───────────
def generate_full_pdf():
    print("=" * 70)
    print("DÉMARRAGE DE LA GÉNÉRATION DU RAPPORT DE STAGE PFA — ALIDENTEC")
    print("=" * 70)
    
    # 1. Générer la page de garde officielle pixel-perfect
    print("1/10 — Génération de la page de garde officielle (template de rapport.pdf)...")
    build_perfect_cover()
    
    styles = get_report_styles()
    
    doc = SimpleDocTemplate(
        TEMP_BODY_PDF,
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM
    )
    
    story = []
    
    print("2/10 — Pages préliminaires (Dédicace, Remerciements, Résumé, Glossaire, TOC, LOF, LOT)...")
    story += build_preliminaries(styles, USABLE_WIDTH, C_PRIMARY, C_LIGHT_BG)
    
    print("3/10 — Introduction Générale...")
    story += build_intro_generale(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT)
    
    print("4/10 — Chapitre 1 (Intercalaire Vert Prairie + Contenu)...")
    story += make_chapter_cover(
        "Chapitre 1",
        "Présentation de l'Entreprise et Cadre du Projet",
        "Immersion Sectorielle, Organisation d'Accueil, Méthodologie Agile Scrum & Planification",
        [
            "1.1 Introduction",
            "1.2 Présentation de l'Organisme d'Accueil (Alidentec)",
            "1.3 Présentation du Cadre Institutionnel (EMSI) et du Stage",
            "1.4 Immersion Métier & Présentation du Projet Hôtelier",
            "1.5 Méthodologie de Conduite de Projet (Agile Scrum)",
            "1.6 Planification Temporelle et Diagramme de Gantt",
            "1.7 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap1(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("5/10 — Chapitre 2 (Intercalaire Vert Prairie + Contenu & Nouveau Diagramme de Classes)...")
    story += make_chapter_cover(
        "Chapitre 2",
        "Analyse des Besoins et Modélisation du Système",
        "Étude Critique, Spécifications Fonctionnelles & Modélisation UML (3 UC, 3 Séquences, Classes, DDD)",
        [
            "2.1 Introduction",
            "2.2 Étude et Critique de l'Existant Hôtelier",
            "2.3 Solution Proposée et Objectifs Stratégiques",
            "2.4 Identification et Rôles des Acteurs (Matrice RACI)",
            "2.5 Spécification Détaillée des Besoins Fonctionnels",
            "2.6 Spécification des Besoins Non-Fonctionnels",
            "2.7 Modélisation UML des Cas d'Utilisation (3 Diagrammes UC)",
            "2.8 Modélisation UML Dynamique (3 Diagrammes de Séquence)",
            "2.9 Modélisation UML Structurelle (Diagramme de Classes Métier)",
            "2.10 Architecture Fonctionnelle et Découpage DDD",
            "2.11 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap2(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("6/10 — Chapitre 3 (Intercalaire Vert Prairie + Contenu Architecture)...")
    story += make_chapter_cover(
        "Chapitre 3",
        "Conception Technique et Technologies",
        "Architecture 4 Tiers, Cartographie des 11 Microservices, Stack Next.js 14 / FastAPI, Persistance & Sécurité",
        [
            "3.1 Introduction",
            "3.2 Architecture Technique Globale 4 Tiers",
            "3.3 Architecture Logicielle Microservices & Pattern Database per Service",
            "3.4 Écosystème Technologique Frontend (Next.js 14, TypeScript, PWA)",
            "3.5 Écosystème Technologique Backend (Python 3.11, FastAPI, SQLAlchemy)",
            "3.6 Persistance, Cache Distribué et Messagerie (PostgreSQL, Redis, RabbitMQ, MinIO)",
            "3.7 Sécurité Périmétrique et Gestion des Identités (Keycloak, WebAuthn, JWT)",
            "3.8 Outils de Développement et Industrialisation DevOps",
            "3.9 Spécification des Contrats d'API RESTful et Codes HTTP",
            "3.10 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap3(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("7/10 — Chapitre 4 (Intercalaire Vert Prairie + 10 Interfaces Clés du Projet)...")
    story += make_chapter_cover(
        "Chapitre 4",
        "Réalisation et Présentation des Interfaces",
        "Infrastructure Docker, Algorithmes Clés (Fiscalité, Clôture, Verrous), 10 Interfaces Clés & Contributions",
        [
            "4.1 Introduction",
            "4.2 Mise en Place de l'Environnement de Développement Conteneurisé",
            "4.3 Développement Backend et Implémentation des Algorithmes Clés",
            "4.4 Développement Frontend et Composants Riches",
            "4.5 Présentation Détaillée des 10 Interfaces Utilisateurs du Projet",
            "4.6 Intégration Globale des Composants",
            "4.7 Bilan des Contributions Individuelles de l'Équipe",
            "4.8 Difficultés Techniques Rencontrées et Solutions d'Ingénierie",
            "4.9 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap4(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("8/10 — Chapitre 5 (Intercalaire Vert Prairie + Tests & Qualité)...")
    story += make_chapter_cover(
        "Chapitre 5",
        "Tests, Validation et Qualité Logicielle",
        "Pyramide des Tests, Suites Pytest (10/10), E2E Playwright, Tests de Charge, OWASP & SonarQube Passed",
        [
            "5.1 Introduction",
            "5.2 Stratégie Globale d'Assurance Qualité (Pyramide des Tests)",
            "5.3 Suites de Tests Unitaires sous Pytest (10/10 Validées)",
            "5.4 Tests d'Intégration des Microservices et Intergiciels",
            "5.5 Tests de Contrats d'API REST avec Postman",
            "5.6 Tests Fonctionnels et Parcours End-to-End (Playwright)",
            "5.7 Tests de Charge et Analyse de Performance Concurrente",
            "5.8 Tests de Sécurité et Audit de Vulnérabilités (OWASP)",
            "5.9 Audit de Qualité de Code sous SonarQube (Quality Gate Passed)",
            "5.10 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap5(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("9/10 — Chapitre 6 (Intercalaire Vert Prairie + Bilan du Stage)...")
    story += make_chapter_cover(
        "Chapitre 6",
        "Bilan du Stage et Apports d'Ingénierie",
        "Apports Techniques & Professionnels, Gestion de Projet Agile, Matrice des Compétences & Perspectives",
        [
            "6.1 Introduction",
            "6.2 Apports Techniques et Maîtrise du Cloud-Native",
            "6.3 Apports Professionnels et Immersion Métier chez Alidentec",
            "6.4 Enseignements Organisationnels et Gestion Agile en Trinôme",
            "6.5 Matrice des Compétences d'Ingénieur Développées",
            "6.6 Contributions Personnelles de Chaque Élève-Ingénieur",
            "6.7 Perspectives d'Évolution et Roadmap Future",
            "6.8 Conclusion du Chapitre"
        ],
        styles, USABLE_WIDTH
    )
    story += build_chap6(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                         get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("10/10 — Conclusion Générale, Bibliographie et Annexes...")
    story += build_conclusion_annexes(styles, USABLE_WIDTH, C_PRIMARY, C_SECONDARY, C_ACCENT,
                                      get_fig_flowable, get_two_figs_flowable, make_table_flowable, make_callout_flowable)
    
    print("Compilation du corps du document...")
    doc.build(story, canvasmaker=NumberedCanvasBody)
    
    # ── Fusion Finale : Page de Garde Officielle + Corps du Document ──────────
    print("Assemblage final : Page de Garde Officielle EMSI (Page 1) + Corps du Mémoire...")
    final_doc = fitz.open()
    
    # 1. Page de garde
    doc_cover = fitz.open(OFFICIAL_COVER_PDF)
    final_doc.insert_pdf(doc_cover, from_page=0, to_page=0)
    doc_cover.close()
    
    # 2. Corps du document
    doc_body = fitz.open(TEMP_BODY_PDF)
    final_doc.insert_pdf(doc_body)
    doc_body.close()
    
    final_doc.save(OUTPUT_PDF)
    total_pages = len(final_doc)
    final_doc.close()
    
    print(f"\n[SUCCES] Rapport complet assemblé avec succès : {OUTPUT_PDF}")
    print(f"[INFO] Nombre total de pages du rapport : {total_pages} pages.")
    print("=" * 70)
    
    # Nettoyage temporaire en toute sécurité
    try:
        if os.path.exists(TEMP_BODY_PDF):
            os.remove(TEMP_BODY_PDF)
    except Exception as e:
        pass
        
    return total_pages

if __name__ == '__main__':
    generate_full_pdf()
