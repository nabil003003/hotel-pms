import os
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.units import cm

C_VERT_PRAIRIE = HexColor('#2E7D32')       # Vert prairie soutenu
C_VERT_PRAIRIE_BG = HexColor('#E8F5E9')    # Fond vert prairie très doux
C_VERT_PRAIRIE_ACCENT = HexColor('#43A047')# Vert prairie éclatant

def make_chapter_cover(chap_num_str, chap_title, chap_theme, sections_list, styles, usable_width):
    story = []
    
    story.append(Spacer(1, 4 * cm))
    
    # Numéro du Chapitre
    p_num = Paragraph(f"<b><font size='16' color='{C_VERT_PRAIRIE.hexval()}'>{chap_num_str.upper()}</font></b>", styles['CoverMeta'])
    story.append(p_num)
    story.append(Spacer(1, 12))
    
    # Ligne décorative Vert prairie
    story.append(HRFlowable(width="100%", thickness=2.5, color=C_VERT_PRAIRIE, spaceBefore=0, spaceAfter=18))
    
    # Titre du Chapitre
    p_title = Paragraph(f"<b><font size='22' color='#1B5E20'>{chap_title.upper()}</font></b>", styles['CoverTitle'])
    story.append(p_title)
    story.append(Spacer(1, 10))
    
    # Thématique / Sous-titre
    if chap_theme:
        p_theme = Paragraph(f"<b><font size='11.5' color='{C_VERT_PRAIRIE_ACCENT.hexval()}'>{chap_theme}</font></b>", styles['CoverSubtitle'])
        story.append(p_theme)
        story.append(Spacer(1, 20))
        
    # Encadré Sommaire et Objectifs du Chapitre en Vert prairie doux
    summary_content = [
        Paragraph(f"<b><font size='11' color='{C_VERT_PRAIRIE.hexval()}'>OBJECTIFS ET SOMMAIRE DU CHAPITRE :</font></b>", styles['Sec3Title']),
        Spacer(1, 8)
    ]
    for sec in sections_list:
        summary_content.append(Paragraph(f"&bull; <b>{sec}</b>", styles['TblCellBold']))
        summary_content.append(Spacer(1, 3))
        
    t_summary = Table([[summary_content]], colWidths=[usable_width])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_VERT_PRAIRIE_BG),
        ('BOX', (0,0), (-1,-1), 1.5, C_VERT_PRAIRIE),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 18),
        ('RIGHTPADDING', (0,0), (-1,-1), 18),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 2 * cm))
    story.append(HRFlowable(width="100%", thickness=1.0, color=C_VERT_PRAIRIE, spaceBefore=10, spaceAfter=0))
    
    story.append(PageBreak())
    return story
