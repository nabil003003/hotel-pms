#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generateur des 6 diagrammes UML pour le Rapport de Stage PMS Alidentec
Produit des PNG haute qualite dans le dossier figures/
"""
import os, math
from matplotlib.colors import to_rgba
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse, Arc
import matplotlib.patheffects as pe
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
FIG  = os.path.join(BASE, 'figures')

# ── Couleurs ──────────────────────────────────────────────────────────────────
C_BLUE   = '#004B87'
C_GOLD   = '#B48C00'
C_LGRAY  = '#F0F4F8'
C_MGRAY  = '#CCCCCC'
C_WHITE  = '#FFFFFF'
C_GREEN  = '#1B6B3A'
C_RED    = '#8B1A1A'
C_LBLUE  = '#D6E8F7'

def save(fig, name, dpi=180):
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  ✅ {name}')


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS COMMUNS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_actor(ax, x, y, label, color=C_BLUE, fontsize=8):
    """Dessine un acteur UML (stick figure)"""
    # Tête
    head = plt.Circle((x, y+0.9), 0.18, color=color, zorder=5)
    ax.add_patch(head)
    # Corps
    ax.plot([x, x], [y+0.72, y+0.3], color=color, lw=1.5, zorder=5)
    # Bras
    ax.plot([x-0.3, x+0.3], [y+0.6, y+0.6], color=color, lw=1.5, zorder=5)
    # Jambes
    ax.plot([x, x-0.25], [y+0.3, y], color=color, lw=1.5, zorder=5)
    ax.plot([x, x+0.25], [y+0.3, y], color=color, lw=1.5, zorder=5)
    ax.text(x, y-0.22, label, ha='center', va='top', fontsize=fontsize,
            fontweight='bold', color=color, wrap=True,
            multialignment='center')

def draw_usecase(ax, x, y, text, w=1.6, h=0.55, color=C_BLUE, bg=C_LBLUE, fontsize=8.5):
    """Dessine un cas d'utilisation (ellipse)"""
    e = Ellipse((x, y), w, h, facecolor=bg, edgecolor=color, linewidth=1.5, zorder=4)
    ax.add_patch(e)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        offset = (len(lines)-1)*0.08 - i*0.16
        ax.text(x, y+offset, line, ha='center', va='center',
                fontsize=fontsize, color=C_BLUE, fontweight='bold', zorder=5)

def arrow(ax, x1, y1, x2, y2, style='->', color=C_MGRAY, lw=1.2, label='', dashed=False):
    ls = '--' if dashed else '-'
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls),
                zorder=3)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my+0.05, label, ha='center', va='bottom',
                fontsize=7, color=color, style='italic')

def sys_box(ax, x, y, w, h, label, color=C_BLUE):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle='round,pad=0.05',
                          facecolor=C_LGRAY, edgecolor=color,
                          linewidth=2, zorder=2)
    ax.add_patch(rect)
    ax.text(x+w/2, y+h+0.1, label, ha='center', va='bottom',
            fontsize=10, fontweight='bold', color=color)

def diagram_title(ax, title, subtitle=''):
    ax.set_title(title + ('\n' + subtitle if subtitle else ''),
                 fontsize=13, fontweight='bold', color=C_BLUE, pad=10)


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 1 — CAS D'UTILISATION GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════
def draw_uc_global():
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(-1, 17); ax.set_ylim(-1, 12)
    ax.set_aspect('equal'); ax.axis('off')
    diagram_title(ax, 'Diagramme de Cas d\'Utilisation — Vue Globale du Système PMS',
                  'Figure 2-1')

    # Frontière système
    sys_box(ax, 2.5, 0.2, 11, 10.8, '≪ Système ≫  PMS Alidentec — Plateforme Hôtelière Multi-Établissements')

    # Acteurs gauche
    draw_actor(ax, 0.5, 8.5,   'Réceptionniste\n(Front-Office)')
    draw_actor(ax, 0.5, 5.8,   'Gouvernante\n(Housekeeping)')
    draw_actor(ax, 0.5, 3.0,   'Auditeur\nde Nuit')

    # Acteurs droite
    draw_actor(ax, 15.5, 7.5,  'Administrateur\n/ Directeur')
    draw_actor(ax, 15.5, 4.5,  '≪ Système ≫\nOTA / Booking')

    # Use Cases — colonne gauche
    draw_usecase(ax, 5.2,  9.5, 'S\'authentifier\n(WebAuthn/FIDO2)')
    draw_usecase(ax, 5.2,  8.2, 'Gérer les\nréservations')
    draw_usecase(ax, 5.2,  6.9, 'Check-in /\nCheck-out')
    draw_usecase(ax, 5.2,  5.6, 'Gérer le\nplanning (Tape Chart)')
    draw_usecase(ax, 5.2,  4.3, 'Gérer les\nfolios & facturation')

    # Use Cases — centre
    draw_usecase(ax, 8.5,  9.5, 'Gérer les\nconsignes (News)')
    draw_usecase(ax, 8.5,  8.0, 'Recevoir les\nnotifications')
    draw_usecase(ax, 8.5,  6.5, 'Mettre à jour\nstatut chambre')
    draw_usecase(ax, 8.5,  5.0, 'Clôture Night\nAudit')
    draw_usecase(ax, 8.5,  3.5, 'Gérer le parc\nde chambres')
    draw_usecase(ax, 8.5,  2.0, 'Superviser les\nmicroservices')

    # Use Cases — droite
    draw_usecase(ax, 11.8, 9.0, 'Gérer les\nétablissements')
    draw_usecase(ax, 11.8, 7.5, 'Gérer les\nutilisateurs & RBAC')
    draw_usecase(ax, 11.8, 6.0, 'Consulter les\nKPI & rapports')
    draw_usecase(ax, 11.8, 4.5, 'Synchroniser\nOTA (Channel Mgr)')
    draw_usecase(ax, 11.8, 3.0, 'Configurer\ntarification')

    # Associations acteurs → UC
    for uc_y in [9.5, 8.2, 6.9, 5.6, 4.3]:
        arrow(ax, 1.3, 9.2 if uc_y>7 else (6.5 if uc_y>5 else 3.7), 4.4, uc_y, color=C_MGRAY)

    for uc_y in [9.5, 8.2, 6.9]:
        arrow(ax, 1.3, 6.5, 4.4, uc_y, color=C_MGRAY)

    for uc_y in [8.2, 6.9]:
        arrow(ax, 1.3, 6.5, 4.4, uc_y, color=C_MGRAY)

    for uc_y in [6.5]:
        arrow(ax, 1.3, 6.5, 7.7, uc_y, color=C_GREEN)

    for uc_y in [5.0]:
        arrow(ax, 1.3, 3.7, 7.7, uc_y, color=C_GREEN)

    for uc_y in [9.0, 7.5, 6.0, 4.5, 3.0]:
        arrow(ax, 14.7, 8.2, 12.6, uc_y, color=C_GOLD)

    arrow(ax, 14.7, 5.2, 12.6, 4.5, color=C_GREEN)

    # Légende
    legend_elements = [
        mpatches.Patch(facecolor=C_LBLUE, edgecolor=C_BLUE, label='Cas d\'utilisation'),
        mpatches.Patch(facecolor='white', edgecolor=C_BLUE, label='Frontière système'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8, framealpha=0.9)

    save(fig, 'uc_global.png')

# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 2 — UC RESERVATION & FRONT-OFFICE
# ═══════════════════════════════════════════════════════════════════════════════
def draw_uc_reservation():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(-1, 16); ax.set_ylim(-0.5, 11)
    ax.set_aspect('equal'); ax.axis('off')
    diagram_title(ax, 'Diagramme de Cas d\'Utilisation — Module Réservation & Front-Office',
                  'Figure 2-2')

    sys_box(ax, 2.0, 0.2, 10.5, 10, '≪ Module ≫  Réservation, Planning & Front-Office')

    # Acteurs
    draw_actor(ax, 0.4, 8.0,  'Réceptionniste')
    draw_actor(ax, 0.4, 4.5,  'Gouvernante')
    draw_actor(ax, 14.5, 7.0, '≪ Système ≫\nChannel Manager\n/ OTA')

    # Use Cases détaillés
    draw_usecase(ax, 5.0, 9.2, 'Consulter le\nTape Chart planning', w=2.2)
    draw_usecase(ax, 5.0, 7.8, 'Créer une réservation\n(verrou Redis anti-collision)', w=2.8)
    draw_usecase(ax, 5.0, 6.4, 'Modifier / annuler\nune réservation', w=2.2)
    draw_usecase(ax, 5.0, 5.0, 'Enregistrer Check-in\n(fiche de police)', w=2.4)
    draw_usecase(ax, 5.0, 3.6, 'Effectuer Check-out\n& solde folio', w=2.2)
    draw_usecase(ax, 5.0, 2.2, 'Changer de chambre\n(Room Shift)', w=2.2)
    draw_usecase(ax, 5.0, 0.8, 'Gérer les no-shows', w=2.2)

    draw_usecase(ax, 9.5, 9.2, 'Vérifier disponibilité\nchambre (temps réel)', w=2.4)
    draw_usecase(ax, 9.5, 7.7, 'Calculer tarification\ndynamique', w=2.4)
    draw_usecase(ax, 9.5, 6.2, 'Vérifier propreté\nchambre (CLEAN/INSPECTED)', w=2.6)
    draw_usecase(ax, 9.5, 4.7, 'Émettre facture PDF\n(TVA, TS, TPT marocains)', w=2.6)
    draw_usecase(ax, 9.5, 3.2, 'Synchroniser dispos\nvers OTA', w=2.4)
    draw_usecase(ax, 9.5, 1.7, 'Notifier Housekeeping\n(WebSocket/RabbitMQ)', w=2.4)

    # Associations
    for y in [9.2, 7.8, 6.4, 5.0, 3.6, 2.2, 0.8]:
        arrow(ax, 1.1, 8.7, 4.1, y, color=C_MGRAY, lw=1.0)

    for y in [6.2, 1.7]:
        arrow(ax, 1.1, 5.2, 4.1, y, color=C_GREEN, lw=1.0)

    for y in [9.2, 7.7, 3.2]:
        arrow(ax, 13.7, 7.7, 10.3, y, color=C_MGRAY, lw=1.0)

    # include/extend
    for uc_l, uc_r, lbl in [(7.8, 9.2, '≪include≫'), (7.8, 7.7, '≪include≫'),
                              (5.0, 6.2, '≪include≫'), (3.6, 4.7, '≪include≫'),
                              (5.0, 1.7, '≪extend≫')]:
        arrow(ax, 6.1, uc_l, 8.7, uc_r, dashed=True, color=C_GOLD, label=lbl, lw=1)

    save(fig, 'uc_reservation.png')


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 3 — UC HOUSEKEEPING & ADMINISTRATION
# ═══════════════════════════════════════════════════════════════════════════════
def draw_uc_housekeeping():
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_xlim(-1, 16); ax.set_ylim(-0.5, 11)
    ax.set_aspect('equal'); ax.axis('off')
    diagram_title(ax, 'Diagramme de Cas d\'Utilisation — Module Housekeeping & Administration',
                  'Figure 2-3')

    sys_box(ax, 2.0, 0.2, 10.5, 10, '≪ Module ≫  Housekeeping, Administration & Supervision')

    draw_actor(ax, 0.4, 7.5,  'Gouvernante\n/ Femme de chambre')
    draw_actor(ax, 0.4, 3.5,  'Auditeur\nde Nuit')
    draw_actor(ax, 14.5, 7.5, 'Administrateur\n/ Directeur')
    draw_actor(ax, 14.5, 3.5, 'Système\nReporting')

    # Housekeeping UCs
    draw_usecase(ax, 5.2, 9.5, 'Consulter liste chambres\nassignées (PWA mobile)', w=2.6)
    draw_usecase(ax, 5.2, 8.1, 'Changer statut chambre\n(DIRTY→CLEAN→INSPECTED)', w=2.8)
    draw_usecase(ax, 5.2, 6.7, 'Signaler anomalie\ntechnique', w=2.2)
    draw_usecase(ax, 5.2, 5.3, 'Valider inspection\nchambre (INSPECTED)', w=2.4)

    # Night Audit UCs
    draw_usecase(ax, 5.2, 3.6, 'Déclencher clôture\nNight Audit', w=2.4)
    draw_usecase(ax, 5.2, 2.2, 'Consulter état\nfolios en suspens', w=2.2)
    draw_usecase(ax, 5.2, 0.8, 'Valider rapport\nde clôture PDF', w=2.2)

    # Admin UCs
    draw_usecase(ax, 9.5, 9.5, 'Gérer établissements\n& catégories chambres', w=2.6)
    draw_usecase(ax, 9.5, 8.0, 'Gérer comptes\nutilisateurs (RBAC)', w=2.4)
    draw_usecase(ax, 9.5, 6.5, 'Configurer taxes\n(TVA, TS, TPT)', w=2.4)
    draw_usecase(ax, 9.5, 5.0, 'Consulter KPI\n(RevPAR, ADR, TdO)', w=2.4)
    draw_usecase(ax, 9.5, 3.5, 'Auditer logs\net sessions JWT', w=2.4)
    draw_usecase(ax, 9.5, 2.0, 'Générer rapports\nconsolidés', w=2.4)
    draw_usecase(ax, 9.5, 0.7, 'Superviser état\nmicroservices', w=2.4)

    for y in [9.5, 8.1, 6.7, 5.3]:
        arrow(ax, 1.1, 8.2, 4.1, y, color=C_GREEN, lw=1.0)
    for y in [3.6, 2.2, 0.8]:
        arrow(ax, 1.1, 4.2, 4.1, y, color=C_BLUE, lw=1.0)
    for y in [9.5, 8.0, 6.5, 5.0, 3.5, 2.0, 0.7]:
        arrow(ax, 13.7, 8.2, 10.3, y, color=C_GOLD, lw=1.0)
    for y in [2.0, 0.7]:
        arrow(ax, 13.7, 4.2, 10.3, y, color=C_MGRAY, lw=1.0)

    arrow(ax, 6.1, 5.3, 8.7, 5.0, dashed=True, color=C_GOLD, label='≪include≫', lw=1)
    arrow(ax, 6.1, 3.6, 8.7, 3.5, dashed=True, color=C_GOLD, label='≪include≫', lw=1)

    save(fig, 'uc_housekeeping.png')


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 4 — SÉQUENCE : AUTHENTIFICATION WebAuthn/FIDO2
# ═══════════════════════════════════════════════════════════════════════════════
def draw_seq_auth():
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(-0.5, 16.5); ax.set_ylim(-0.5, 12)
    ax.axis('off')
    diagram_title(ax, 'Diagramme de Séquence — Authentification WebAuthn / FIDO2 par QR Code',
                  'Figure 2-4')

    # Participants
    participants = [
        (1.5,   'Réceptionniste\n(Navigateur)', C_BLUE),
        (4.5,   'Kong\nAPI Gateway', C_GOLD),
        (7.5,   'Auth-Gateway\nService', C_BLUE),
        (10.5,  'Keycloak\nIAM / FIDO2', C_GREEN),
        (13.5,  'PostgreSQL\n/ Redis', C_MGRAY),
    ]

    YMAX = 11.0
    boxes, centers = [], []
    for x, name, color in participants:
        rect = FancyBboxPatch((x-0.9, YMAX-0.5), 1.8, 0.9,
                              boxstyle='round,pad=0.05',
                              facecolor=color, edgecolor='white', linewidth=1.5, zorder=5)
        ax.add_patch(rect)
        for i, line in enumerate(name.split('\n')):
            ax.text(x, YMAX-0.1+(len(name.split('\n'))-1)*0.15 - i*0.28, line,
                    ha='center', va='center', fontsize=7.5, color='white',
                    fontweight='bold', zorder=6)
        ax.plot([x, x], [0.5, YMAX-0.5], color='#CCCCCC',
                ls='--', lw=1.2, zorder=2)
        boxes.append(x); centers.append(x)

    def msg(y1, y2, label, note='', color=C_BLUE, ret=False):
        y = y1
        style = '<-' if ret else '->'
        ax.annotate('', xy=(centers[y2], y), xytext=(centers[y1], y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5))
        mx = (centers[y1]+centers[y2])/2
        ax.text(mx, y+0.1, label, ha='center', va='bottom',
                fontsize=8, color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=color, alpha=0.9, linewidth=0.8))
        if note:
            ax.text(mx, y-0.2, note, ha='center', va='top',
                    fontsize=7, color='#666666', style='italic')

    def activate(participant, y_start, y_end, color=C_LBLUE):
        x = centers[participant] - 0.08
        rect = FancyBboxPatch((x, y_end), 0.16, y_start-y_end,
                              boxstyle='square,pad=0',
                              facecolor=color, edgecolor=C_BLUE, linewidth=1, zorder=4)
        ax.add_patch(rect)

    def note_box(x, y, text, color='#FFF8DC'):
        ax.text(x, y, text, ha='left', va='center', fontsize=7.5,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color,
                          edgecolor=C_GOLD, linewidth=1))

    # Alt frame
    def alt_frame(y_start, y_end, label):
        rect = FancyBboxPatch((0.1, y_end), 15.8, y_start-y_end,
                              boxstyle='square,pad=0',
                              facecolor='#F8F0FF', edgecolor='#9966CC',
                              linewidth=1.5, alpha=0.3, zorder=1)
        ax.add_patch(rect)
        ax.text(0.3, y_start-0.1, label, fontsize=8, color='#9966CC',
                fontweight='bold', style='italic')

    # Séquence
    activate(0, 10.2, 9.0)
    msg(0, 1, '1. GET /auth/login/begin', '[Session ID créée]')
    activate(1, 10.2, 7.0)
    msg(1, 2, '2. POST /auth/challenge', '[Routage JWT vérifié]')
    activate(2, 9.9, 6.5)
    msg(2, 3, '3. Generate authentication_options', '[transport: hybrid, ble]')
    activate(3, 9.6, 6.2)
    msg(3, 4, '4. Store challenge in Redis (TTL=120s)', '[Verrou anti-replay]', color=C_GREEN)
    msg(4, 3, '5. Redis OK', ret=True, color=C_GREEN)
    msg(3, 2, '6. authentication_options JSON', ret=True)
    msg(2, 1, '7. 200 OK + QR Code payload', ret=True)
    msg(1, 0, '8. Display QR Code', ret=True)

    note_box(0.2, 8.5, '★ Staff scanne le QR\n  avec son smartphone\n  → Face ID / Touch ID', '#E8FFE8')

    msg(0, 1, '9. POST /auth/login/finish\n   {credential_id, authenticatorData...}', color=C_GREEN)
    msg(1, 2, '10. Forward credential to auth-service')
    msg(2, 3, '11. Verify assertion (FIDO2 Verifier)')
    msg(3, 4, '12. SELECT public_key WHERE credential_id=?')
    msg(4, 3, '13. Public key + sign_count', ret=True)

    alt_frame(5.8, 2.2, 'alt [Signature valide]')
    msg(3, 2, '14. sign_count++, UPDATE credential', color=C_GREEN)
    msg(2, 3, '15. Emit JWT RS256 (role, establishment_id, 4h)', color=C_GREEN)
    msg(3, 2, '16. JWT token', ret=True, color=C_GREEN)
    msg(2, 1, '17. 200 OK + httpOnly Cookie JWT', ret=True, color=C_GREEN)
    msg(1, 0, '18. Redirect → Dashboard PMS', ret=True, color=C_GREEN)

    note_box(0.2, 2.6, '✗ Signature invalide → 401 Unauthorized\n  + Alerte sécurité RabbitMQ', '#FFE8E8')

    ax.text(8.0, 0.2, 'Standard W3C WebAuthn Level 3 - RFC 8809 - FIDO2 CTAP2',
            ha='center', fontsize=7.5, color='#888888', style='italic')

    save(fig, 'seq_auth.png', dpi=200)


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 5 — SÉQUENCE : RÉSERVATION + VERROU REDIS
# ═══════════════════════════════════════════════════════════════════════════════
def draw_seq_reservation():
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(-0.5, 17); ax.set_ylim(-0.5, 12)
    ax.axis('off')
    diagram_title(ax, 'Diagramme de Séquence — Création de Réservation avec Verrou Redis Anti-Collision',
                  'Figure 2-5')

    participants = [
        (1.3,   'Réceptionniste\n(Next.js UI)', C_BLUE),
        (4.0,   'Kong\nGateway', C_GOLD),
        (6.8,   'Reservation\nService', C_BLUE),
        (9.5,   'Redis 7\n(Verrous)', C_GREEN),
        (12.2,  'PostgreSQL\n(Réservations)', C_BLUE),
        (15.0,  'RabbitMQ\n(Notifications)', C_RED),
    ]
    YMAX = 11.2
    centers = []
    for x, name, color in participants:
        rect = FancyBboxPatch((x-0.9, YMAX-0.5), 1.8, 0.85,
                              boxstyle='round,pad=0.05',
                              facecolor=color, edgecolor='white', lw=1.5, zorder=5)
        ax.add_patch(rect)
        for i, line in enumerate(name.split('\n')):
            ax.text(x, YMAX-0.05 + (len(name.split('\n'))-1)*0.14 - i*0.27, line,
                    ha='center', va='center', fontsize=7.5, color='white',
                    fontweight='bold', zorder=6)
        ax.plot([x, x], [0.3, YMAX-0.5], color='#BBBBBB', ls='--', lw=1.2, zorder=2)
        centers.append(x)

    def msg(src, dst, label, y, note='', color=C_BLUE, ret=False, bold=False):
        style = '<-' if ret else '->'
        ax.annotate('', xy=(centers[dst], y), xytext=(centers[src], y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5))
        mx = (centers[src]+centers[dst])/2
        fw = 'bold' if bold else 'normal'
        ax.text(mx, y+0.12, label, ha='center', va='bottom',
                fontsize=7.5, color=color, fontweight=fw,
                bbox=dict(boxstyle='round,pad=0.12', facecolor='white',
                          edgecolor=color, alpha=0.9, lw=0.8))
        if note:
            ax.text(mx, y-0.18, note, ha='center', va='top',
                    fontsize=6.5, color='#555555', style='italic')

    def alt_f(y0, y1, label, color='#9966CC'):
        r = FancyBboxPatch((0.1, y1), 16.4, y0-y1, boxstyle='square,pad=0',
                           facecolor='#F5EEFF', edgecolor=color, lw=1.5, alpha=0.3, zorder=1)
        ax.add_patch(r)
        ax.text(0.3, y0-0.12, label, fontsize=8, color=color, fontweight='bold', style='italic')

    # Séquence
    msg(0, 1, '1. POST /reservations {room_id, dates, guest_id}', 10.5, bold=True)
    msg(1, 2, '2. Valider JWT + RBAC (role=RECEPTIONIST)', 10.0)
    msg(2, 3, '3. SET NX PX 10000 lock:room:{room_id}:{date}', 9.5,
        '[Commande atomique Redis — bail 10 sec]', color=C_GREEN, bold=True)

    alt_f(9.1, 5.5, 'alt [Verrou acquis — chambre libre]')
    msg(3, 2, '4. OK — Verrou acquis', 8.7, ret=True, color=C_GREEN)
    msg(2, 4, '5. SELECT availability WHERE room_id=? AND dates OVERLAP ?', 8.2,
        color=C_BLUE)
    msg(4, 2, '6. Disponible — 0 conflit trouvé', 7.7, ret=True)
    msg(2, 4, '7. INSERT INTO reservations (...) RETURNING id', 7.2, color=C_BLUE, bold=True)
    msg(4, 2, '8. reservation_id=UUID generé', 6.7, ret=True)
    msg(2, 3, '9. DEL lock:room:{room_id}:{date}', 6.2, '[Libération verrou Redis]', color=C_GREEN)
    msg(2, 5, '10. PUBLISH reservation.created (RabbitMQ fanout)', 5.8, color=C_RED)
    msg(2, 1, '11. 201 Created {reservation_id, status=CONFIRMED}', 5.3, color=C_GREEN, bold=True)
    msg(1, 0, '12. Afficher confirmation + mise à jour Tape Chart', 4.8, ret=True, color=C_GREEN)

    alt_f(4.4, 1.8, 'alt [Verrou refusé — chambre prise concurremment]')
    msg(3, 2, '13. NIL — Verrou non acquis (409)', 4.0, ret=True, color=C_RED, bold=True)
    msg(2, 1, '14. 409 Conflict — chambre réservée', 3.5, color=C_RED)
    msg(1, 0, '15. Afficher toast d\'erreur utilisateur', 3.0, ret=True, color=C_RED)

    ax.text(8.5, 0.2, 'Pattern : Distributed Lock (Redlock) — TTL 10s — Idempotence X-Idempotency-Key',
            ha='center', fontsize=7.5, color='#888888', style='italic')

    save(fig, 'seq_reservation.png', dpi=200)


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME 6 — SÉQUENCE : NIGHT AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
def draw_seq_nightaudit():
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.set_xlim(-0.5, 16.5); ax.set_ylim(-0.5, 13)
    ax.axis('off')
    diagram_title(ax, 'Diagramme de Séquence — Clôture Journalière Night Audit (Transactionnel)',
                  'Figure 2-6')

    participants = [
        (1.3,   'Auditeur\nde Nuit', C_BLUE),
        (4.0,   'Night-Audit\nService', C_BLUE),
        (6.8,   'PostgreSQL\n(Folios)', C_GREEN),
        (9.5,   'MinIO S3\n(Rapports)', C_GOLD),
        (12.2,  'RabbitMQ\n(Alertes)', C_RED),
        (15.0,  'Business\nDate Service', C_MGRAY),
    ]
    YMAX = 12.5
    centers = []
    for x, name, color in participants:
        rect = FancyBboxPatch((x-0.9, YMAX-0.5), 1.8, 0.9,
                              boxstyle='round,pad=0.05',
                              facecolor=color, edgecolor='white', lw=1.5, zorder=5)
        ax.add_patch(rect)
        for i, line in enumerate(name.split('\n')):
            ax.text(x, YMAX-0.05+(len(name.split('\n'))-1)*0.15-i*0.28, line,
                    ha='center', va='center', fontsize=7.5, color='white',
                    fontweight='bold', zorder=6)
        ax.plot([x, x], [0.3, YMAX-0.5], color='#BBBBBB', ls='--', lw=1.2, zorder=2)
        centers.append(x)

    def msg(s, d, label, y, note='', color=C_BLUE, ret=False, bold=False):
        style = '<-' if ret else '->'
        ax.annotate('', xy=(centers[d], y), xytext=(centers[s], y),
                    arrowprops=dict(arrowstyle=style, color=color, lw=1.5))
        mx = (centers[s]+centers[d])/2
        ax.text(mx, y+0.12, label, ha='center', va='bottom', fontsize=7.5,
                color=color, fontweight='bold' if bold else 'normal',
                bbox=dict(boxstyle='round,pad=0.12', facecolor='white',
                          edgecolor=color, alpha=0.9, lw=0.8))
        if note:
            ax.text(mx, y-0.18, note, ha='center', va='top',
                    fontsize=6.5, color='#555555', style='italic')

    def loop_frame(y0, y1, label):
        r = FancyBboxPatch((0.2, y1), 16.0, y0-y1, boxstyle='square,pad=0',
                           facecolor='#E8F8FF', edgecolor='#0066AA', lw=1.5, alpha=0.3, zorder=1)
        ax.add_patch(r)
        ax.text(0.4, y0-0.12, label, fontsize=8, color='#0066AA', fontweight='bold', style='italic')

    def alt_f(y0, y1, label):
        r = FancyBboxPatch((0.2, y1), 16.0, y0-y1, boxstyle='square,pad=0',
                           facecolor='#FFF5E8', edgecolor='#CC6600', lw=1.5, alpha=0.3, zorder=1)
        ax.add_patch(r)
        ax.text(0.4, y0-0.12, label, fontsize=8, color='#CC6600', fontweight='bold', style='italic')

    msg(0, 1, '1. POST /night-audit/execute {business_date}', 11.8, bold=True)
    msg(1, 2, '2. SELECT séjours actifs (status=IN_HOUSE) WHERE date=?', 11.2)
    msg(2, 1, '3. Liste des 50 folios actifs', 10.7, ret=True)

    msg(1, 1, '4. BEGIN TRANSACTION SERIALIZABLE', 10.2, color=C_GREEN, bold=True)

    loop_frame(9.7, 5.8, 'loop [Pour chaque folio actif]')
    msg(1, 2, '5. LOCK folio_id (FOR UPDATE NOWAIT)', 9.3, color=C_BLUE)
    msg(1, 1, '6. Calcul fiscal asyncio :\n   nuitée + TVA 10% + TS 25MAD + TPT 12MAD', 8.7,
        '[Decimal ROUND_HALF_EVEN — arrondi bancaire]', color=C_GREEN, bold=True)
    msg(1, 2, '7. INSERT folio_lines (charges nuitée + taxes)', 8.1)
    msg(2, 1, '8. folio_line_id créé', 7.7, ret=True)
    msg(1, 2, '9. UPDATE folio SET balance=balance+montant', 7.2)

    alt_f(5.4, 3.0, 'alt [Succès total] / [Erreur → ROLLBACK]')
    msg(1, 2, '10. COMMIT TRANSACTION', 5.0, color=C_GREEN, bold=True)
    msg(2, 1, '11. Transaction validée — 50/50 folios', 4.5, ret=True, color=C_GREEN)
    msg(1, 3, '12. PUT rapport_cloture_{date}.pdf → MinIO S3', 4.0, color=C_GOLD, bold=True)
    msg(3, 1, '13. URL rapport immuable S3', 3.5, ret=True, color=C_GOLD)
    msg(1, 4, '14. PUBLISH night_audit.completed → RabbitMQ', 3.0, color=C_RED)
    msg(1, 5, '15. PATCH business_date = business_date + 1 jour', 2.5, bold=True)
    msg(5, 1, '16. Nouvelle Business Date confirmée', 2.0, ret=True)
    msg(1, 0, '17. 200 OK — Clôture en 45s — Rapport PDF généré', 1.5, ret=True,
        color=C_GREEN, bold=True)

    ax.text(8.0, 0.2, '⚡ Parallélisation asyncio.gather() — 30× plus rapide vs séquentiel — '
                       'p95 < 45s pour 50 chambres',
            ha='center', fontsize=7.5, color='#555555', style='italic')

    save(fig, 'seq_nightaudit.png', dpi=200)


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGRAMME CLASSES (override avec version détaillée)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_class_diagram():
    fig, ax = plt.subplots(figsize=(18, 13))
    ax.set_xlim(-0.5, 18.5); ax.set_ylim(-0.5, 14)
    ax.axis('off')
    diagram_title(ax, 'Diagramme de Classes UML — Domaine Métier PMS Alidentec',
                  'Figure 2-7')

    def cls_box(ax, x, y, name, attrs, ops, w=2.8, stereotype=''):
        lh = 0.38
        nattrs = len(attrs); nops = len(ops)
        total_h = lh*(1 + nattrs + nops) + 0.25
        # Fond
        rect = FancyBboxPatch((x, y), w, total_h, boxstyle='square,pad=0',
                              facecolor='white', edgecolor=C_BLUE, lw=1.5, zorder=4)
        ax.add_patch(rect)
        # En-tête
        head = FancyBboxPatch((x, y+total_h-lh*1.4), w, lh*1.4, boxstyle='square,pad=0',
                              facecolor=C_BLUE, edgecolor=C_BLUE, lw=0, zorder=5)
        ax.add_patch(head)
        if stereotype:
            ax.text(x+w/2, y+total_h-lh*0.55, f'≪{stereotype}≫',
                    ha='center', va='center', fontsize=6.5, color=C_GOLD,
                    style='italic', zorder=6)
            ax.text(x+w/2, y+total_h-lh*1.1, name,
                    ha='center', va='center', fontsize=8, color='white',
                    fontweight='bold', zorder=6)
        else:
            ax.text(x+w/2, y+total_h-lh*0.8, name,
                    ha='center', va='center', fontsize=8, color='white',
                    fontweight='bold', zorder=6)
        # Séparateurs
        sep1_y = y+total_h-lh*1.4
        sep2_y = y+nops*lh if nops else None
        ax.plot([x, x+w], [sep1_y, sep1_y], color=C_BLUE, lw=1, zorder=5)
        if sep2_y:
            ax.plot([x, x+w], [sep2_y, sep2_y], color='#BBBBBB', lw=0.8, zorder=5)
        # Attributs
        for i, attr in enumerate(attrs):
            ay = sep1_y - (i+1)*lh + lh*0.1
            ax.text(x+0.1, ay, attr, ha='left', va='center', fontsize=6.5,
                    color=DGRAY, zorder=6, fontfamily='monospace')
        # Opérations
        for i, op in enumerate(ops):
            oy = y + (nops-i-1)*lh + lh*0.5 if nops else 0
            ax.text(x+0.1, oy, op, ha='left', va='center', fontsize=6.5,
                    color=C_GREEN, zorder=6, fontfamily='monospace', style='italic')
        return x+w/2, y+total_h, x, y, w, total_h  # cx, cy_top, x, y, w, h

    from matplotlib.colors import to_hex

    def rel(ax, x1, y1, x2, y2, label='', card1='', card2='', style='assoc', color=C_BLUE):
        ls = '--' if style == 'dep' else '-'
        ax.plot([x1, x2], [y1, y2], color=color, ls=ls, lw=1.3, zorder=3)
        if card1:
            ax.text(x1+(x2-x1)*0.08, y1+(y2-y1)*0.08, card1,
                    fontsize=7, color=color, ha='center')
        if card2:
            ax.text(x2-(x2-x1)*0.08, y2-(y2-y1)*0.08, card2,
                    fontsize=7, color=color, ha='center')
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2+0.1, label,
                    fontsize=6.5, color=color, ha='center', style='italic')
        # Flèche
        dx = x2-x1; dy = y2-y1
        length = math.sqrt(dx*dx+dy*dy)
        if length > 0:
            ax.annotate('', xy=(x2, y2), xytext=(x2-dx*0.15/length*1.5, y2-dy*0.15/length*1.5),
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.2), zorder=4)

    DGRAY = '#333333'

    # Définir les classes
    classes = {
        'Establishment': cls_box(ax, 0.2, 9.5, 'Establishment',
            ['+id: UUID', '+name: String', '+address: String', '+commune: String',
             '+tva_rate: Decimal(10%)', '+ts_rate: Decimal(25MAD)', '+tpt_rate: Decimal(12MAD)'],
            ['+create()', '+get_business_date()'],
            w=3.0),
        'Room': cls_box(ax, 0.2, 5.5, 'Room',
            ['+id: UUID', '+establishment_id: UUID', '+number: String', '+category: Enum',
             '+capacity: int', '+base_price: Decimal', '+status: RoomStatus'],
            ['+is_available(dates)', '+change_status()'],
            w=3.0),
        'GuestProfile': cls_box(ax, 4.2, 10.5, 'GuestProfile',
            ['+id: UUID', '+first_name: String', '+last_name: String',
             '+passport_number: String', '+nationality: String', '+vip_level: int'],
            ['+get_history()', '+flag_vip()'],
            w=3.2),
        'Reservation': cls_box(ax, 4.2, 6.5, 'Reservation',
            ['+id: UUID', '+room_id: UUID', '+guest_id: UUID',
             '+arrival_date: Date', '+departure_date: Date',
             '+status: ResvStatus', '+total_amount: Decimal'],
            ['+confirm()', '+cancel()', '+check_in()', '+check_out()'],
            w=3.2),
        'Folio': cls_box(ax, 8.5, 8.0, 'Folio',
            ['+id: UUID', '+reservation_id: UUID',
             '+total_debit: Decimal', '+total_credit: Decimal',
             '+balance: Decimal', '+currency: String'],
            ['+add_charge()', '+add_payment()', '+close()'],
            w=3.0),
        'FolioLine': cls_box(ax, 8.5, 4.2, 'FolioLine',
            ['+id: UUID', '+folio_id: UUID', '+description: String',
             '+amount: Decimal', '+tax_type: Enum', '+date: Date'],
            ['+calculate_tax()'],
            w=3.0),
        'NightAudit': cls_box(ax, 12.5, 9.0, 'NightAuditReport',
            ['+id: UUID', '+business_date: Date',
             '+total_revenue: Decimal', '+rooms_audited: int',
             '+status: AuditStatus', '+pdf_s3_url: String'],
            ['+execute()', '+generate_pdf()', '+rollback()'],
            w=3.2),
        'HousekeepingTask': cls_box(ax, 12.5, 5.2, 'HousekeepingTask',
            ['+id: UUID', '+room_id: UUID', '+assigned_to: UUID',
             '+status: TaskStatus', '+priority: int'],
            ['+start()', '+complete()', '+inspect()'],
            w=3.2),
        'User': cls_box(ax, 4.2, 1.5, 'User',
            ['+id: UUID', '+username: String', '+role: Role',
             '+establishment_id: UUID', '+fido2_credential_id: String'],
            ['+authenticate()', '+revoke_token()'],
            w=3.2, stereotype='entity'),
        'Notification': cls_box(ax, 8.5, 0.8, 'Notification',
            ['+id: UUID', '+type: NotifType', '+payload: JSON',
             '+is_read: bool', '+created_at: Timestamp'],
            ['+send()', '+mark_read()'],
            w=3.0),
    }

    # Relations — utiliser coordonnées cx (x+w/2) et cy_top (y + total_h)
    # On récupère les centres des boîtes approximativement
    def midpoint(x, y, w, h):
        return x+w/2, y+h/2

    # Establishment ─── Room  (1..*) 
    ax.annotate('', xy=(1.7, 5.5+2.5), xytext=(1.7, 9.5),
                arrowprops=dict(arrowstyle='->', color=C_BLUE, lw=1.3))
    ax.text(1.4, 8.0, '1', fontsize=8, color=C_BLUE)
    ax.text(1.4, 7.0, '0..*', fontsize=8, color=C_BLUE)

    # Reservation ─── Room
    ax.annotate('', xy=(3.2, 7.0), xytext=(4.2, 7.0),
                arrowprops=dict(arrowstyle='->', color=C_BLUE, lw=1.3))
    ax.text(3.6, 7.2, 'utilise', fontsize=6.5, color=C_BLUE, style='italic')

    # Reservation ─── GuestProfile
    ax.annotate('', xy=(5.8, 10.5+0.5), xytext=(5.8, 6.5+3.5),
                arrowprops=dict(arrowstyle='->', color=C_BLUE, lw=1.3))

    # Reservation ─── Folio
    ax.annotate('', xy=(8.5, 9.0), xytext=(7.4, 8.8),
                arrowprops=dict(arrowstyle='->', color=C_BLUE, lw=1.3))
    ax.text(7.6, 9.1, '1', fontsize=8, color=C_BLUE)
    ax.text(8.2, 9.1, '1', fontsize=8, color=C_BLUE)

    # Folio ─── FolioLine
    ax.annotate('', xy=(10.0, 4.2+1.5), xytext=(10.0, 8.0),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.3))
    ax.text(10.2, 6.2, '1..*', fontsize=8, color=C_GREEN)

    # NightAudit ─── Folio
    ax.annotate('', xy=(11.5, 9.5), xytext=(12.5, 9.8),
                arrowprops=dict(arrowstyle='->', color=C_GOLD, lw=1.3))
    ax.text(11.8, 9.8, 'clôture', fontsize=6.5, color=C_GOLD, style='italic')

    # HousekeepingTask ─── Room
    ax.annotate('', xy=(3.2, 6.0), xytext=(12.5, 6.5),
                arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1.3))

    # User ─── Reservation
    ax.annotate('', xy=(5.8, 6.5), xytext=(5.8, 1.5+3.0),
                arrowprops=dict(arrowstyle='->', color='#884400', lw=1.3))

    # Légende
    legend = [
        mpatches.Patch(facecolor=C_BLUE, label='Association'),
        mpatches.Patch(facecolor=C_GREEN, label='Composition'),
        mpatches.Patch(facecolor=C_GOLD, label='Dépendance'),
    ]
    ax.legend(handles=legend, loc='lower right', fontsize=8)
    ax.text(9.0, 0.1, '≪ Architecture Domain-Driven Design (DDD) — Database per Service Pattern ≫',
            ha='center', fontsize=8, color='#555555', style='italic')

    save(fig, 'class_diagram_pms.png', dpi=200)


# ═══════════════════════════════════════════════════════════════════════════════
# GANTT (override avec version détaillée)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_gantt():
    fig, ax = plt.subplots(figsize=(18, 9))
    ax.set_xlim(-0.5, 17); ax.set_ylim(-1, 13)
    ax.axis('off')
    diagram_title(ax, 'Diagramme de Gantt — Planning des 8 Sprints (16 semaines)',
                  'Figure 1-3')

    sprints = [
        ('Sprint 1\nFondations & Auth',      0, 2,   C_BLUE,   'Auth-Gateway, Keycloak, FIDO2, Docker Compose infra'),
        ('Sprint 2\nTarification & OTA',     2, 4,   C_GREEN,  'Pricing-Service, Partner-Service, Channel Manager'),
        ('Sprint 3\nRéservations',           4, 6,   '#6B3FA0','Reservation-Service, verrou Redis, anti-overbooking'),
        ('Sprint 4\nFront-Office',           6, 8,   C_GOLD,   'Check-in/out, Tape Chart Drag&Drop, dashboards'),
        ('Sprint 5\nFacturation & Audit',    8, 10,  '#A04040','Billing/Folio, Night Audit, MinIO S3, Alertes'),
        ('Sprint 6\nIntégration Frontend',   10, 12, '#408040','Next.js App Router, WebSockets, PWA Housekeeping'),
        ('Sprint 7\nTests & Sécurité',       12, 14, '#404080','Pytest, Playwright E2E, tests charge, OWASP'),
        ('Sprint 8\nOptimisation & Livraison',14, 16, C_BLUE,  'Perf +74%, Docker prod, Prometheus/Grafana, docs'),
    ]

    tasks_sub = [
        # (sprint_idx, label, start, end, row_offset)
        (0, 'Auth-Gateway Service',      0.1, 1.5,  0),
        (0, 'Keycloak IAM / FIDO2',     0.3, 2.0,  1),
        (1, 'Pricing + Partner Service', 2.1, 4.0,  0),
        (1, 'Channel Manager',           2.5, 4.0,  1),
        (2, 'Reservation Service',       4.1, 6.0,  0),
        (2, 'Verrou Redis + Tests',      4.3, 6.0,  1),
        (3, 'Front-Office Service',      6.1, 8.0,  0),
        (3, 'Tape Chart UI / UX',        6.2, 8.0,  1),
        (4, 'Billing & Folio Service',   8.1, 10.0, 0),
        (4, 'Night Audit Engine',        8.4, 10.0, 1),
        (5, 'Next.js App Router',        10.1, 12.0, 0),
        (5, 'PWA + WebSockets',          10.3, 12.0, 1),
        (6, 'Tests Pytest / Playwright', 12.1, 14.0, 0),
        (6, 'Tests Charge + Sécurité',   12.5, 14.0, 1),
        (7, 'Optimisation p95 latence',  14.1, 15.5, 0),
        (7, 'Docs + Déploiement prod',   14.2, 16.0, 1),
    ]

    colors = [C_BLUE, C_GREEN, '#6B3FA0', C_GOLD, '#A04040', '#408040', '#404080', C_BLUE]

    NSPRINTS = 8
    BAR_H = 0.6
    Y_SPRINT = 11.5
    Y_SUB_START = 9.5

    # Semaines (colonnes)
    for i in range(17):
        x = i
        ax.plot([x, x], [-0.5, 12.5], color='#EEEEEE', lw=0.8, zorder=1)
        if i < 16:
            ax.text(x+0.5, 12.3, f'S{i+1}', ha='center', fontsize=7,
                    color='#888888', fontweight='bold')

    # Sprints
    for i, (label, start, end, color, desc) in enumerate(sprints):
        y = Y_SPRINT - i*1.2
        rect = FancyBboxPatch((start+0.05, y-BAR_H/2), end-start-0.1, BAR_H,
                              boxstyle='round,pad=0.05',
                              facecolor=color, edgecolor='white', lw=1.5,
                              alpha=0.9, zorder=4)
        ax.add_patch(rect)
        for j, line in enumerate(label.split('\n')):
            ax.text(start+(end-start)/2, y+0.05-j*0.22, line,
                    ha='center', va='center', fontsize=7.5, color='white',
                    fontweight='bold', zorder=5)
        ax.text(end+0.1, y, desc, ha='left', va='center',
                fontsize=6.5, color='#444444', style='italic')

    # Tâches sous-niveau
    for sprint_idx, label, start, end, row_off in tasks_sub:
        color = colors[sprint_idx]
        y = Y_SUB_START - (sprint_idx * 0.38 * 2 + row_off * 0.38)
        rect = FancyBboxPatch((start, y-0.14), end-start, 0.28,
                              boxstyle='round,pad=0.02',
                              facecolor=color, edgecolor='white', lw=1, alpha=0.6, zorder=3)
        ax.add_patch(rect)
        ax.text(start+(end-start)/2, y, label, ha='center', va='center',
                fontsize=5.8, color='white', fontweight='bold', zorder=4)

    # Étiquettes lignes
    ax.text(-0.3, 11.5, 'Sprints:', ha='right', va='center', fontsize=8,
            fontweight='bold', color=C_BLUE)
    ax.text(-0.3, 9.5, 'Tâches:', ha='right', va='center', fontsize=8,
            fontweight='bold', color=C_BLUE)

    # Légende durée
    ax.text(8.0, -0.6, 'Durée totale : 16 semaines (Février — Mai 2026)  —  '
                        'Méthode : Agile Scrum  —  Équipe : 3 ingénieurs',
            ha='center', fontsize=8, color='#555555', style='italic')

    # Jalons
    for x, label in [(2, 'Infra\nvalidée'), (6, 'Core\nlivré'),
                      (10, 'Full\nstack'), (14, 'Tests\nOK'), (16, 'Livraison\nfinale')]:
        ax.plot(x, -0.2, 'D', color=C_GOLD, markersize=8, zorder=6)
        ax.text(x, -0.55, label, ha='center', fontsize=6.5, color=C_GOLD,
                fontweight='bold', multialignment='center')

    save(fig, 'gantt_pms.png', dpi=180)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    print('[1/8] Use Case Global ...')
    draw_uc_global()
    print('[2/8] Use Case Reservation & Front-Office ...')
    draw_uc_reservation()
    print('[3/8] Use Case Housekeeping & Administration ...')
    draw_uc_housekeeping()
    print('[4/8] Sequence: Authentification WebAuthn ...')
    draw_seq_auth()
    print('[5/8] Sequence: Reservation + Redis Lock ...')
    draw_seq_reservation()
    print('[6/8] Sequence: Night Audit ...')
    draw_seq_nightaudit()
    print('[7/8] Diagramme de Classes ...')
    draw_class_diagram()
    print('[8/8] Diagramme de Gantt ...')
    draw_gantt()
    print('DONE - All diagrams saved to figures/')
