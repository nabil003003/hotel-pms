#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module : Conclusion Générale, Bibliographie, Webographie et Annexes
Réponse structurée aux 4 questions fondamentales, références normées et 3 annexes techniques complètes.
"""

from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.units import cm
from reportlab.lib.colors import white, HexColor

def build_conclusion_annexes(styles, usable_width, c_primary, c_secondary, c_accent, get_fig, get_two_figs, make_table, make_callout):
    story = []
    
    # ── CONCLUSION GÉNÉRALE ET PERSPECTIVES ──────────────────────────────────
    story.append(Paragraph("CONCLUSION GÉNÉRALE ET PERSPECTIVES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    story.append(Paragraph(
        "Arrivés au terme de ce mémoire de fin d'année réalisé au sein de l'entreprise <b>Alidentec</b>, "
        "il convient de dresser un bilan synthétique de l'ensemble du projet d'ingénierie en répondant aux quatre questions fondamentales "
        "qui ont guidé notre démarche :", styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # 1. Quel problème ?
    story.append(Paragraph("1. Quel était le problème initialement posé ?", styles['Sec2Title']))
    story.append(Paragraph(
        "L'exploitation des établissements hôteliers traditionnels et des Riads à Marrakech était lourdement pénalisée par des outils logiciels fragmentés "
        "et des processus manuels obsolètes : des surréservations fréquentes (<i>overbooking</i>) causées par une synchronisation imparfaite avec les plateformes OTA, "
        "une clôture journalière (<i>Night Audit</i>) fastidieuse et source d'erreurs de calcul sur la TVA (10%) et les taxes communales (TS et TPT), "
        "des risques majeurs de sécurité liés au partage de mots de passe sur les postes de réception, et un manque criant de visibilité en temps réel "
        "sur l'état de propreté des chambres entre la réception et les équipes d'étage.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # 2. Quelle solution ?
    story.append(Paragraph("2. Quelle solution d'ingénierie avons-nous conçue et réalisée ?", styles['Sec2Title']))
    story.append(Paragraph(
        "Pour résoudre durablement ces problématiques, nous avons conçu et développé la plateforme <b>PMS Alidentec Hospitality</b>, une architecture logicielle "
        "distribuée cloud-native articulée autour de <b>onze microservices autonomes en Python (FastAPI)</b> selon le patron <i>Database per Service</i>. "
        "La solution intègre une passerelle d'API <b>Kong</b>, un serveur d'authentification <b>Keycloak</b> avec standard biométrique sans mot de passe <b>WebAuthn / FIDO2</b> "
        "par QR Code dynamique, un cache distribué <b>Redis 7</b> pour les verrous atomiques anti-collision, un bus de messages <b>RabbitMQ</b> pour la diffusion d'événements, "
        "un stockage objet <b>MinIO S3</b> pour l'archivage immuable des rapports financiers, et une interface réactive sous <b>Next.js 14</b> avec planning interactif "
        "<i>Tape Chart</i> et Progressive Web App (PWA) pour le Housekeeping.",
        styles['Body']
    ))
    story.append(Spacer(1, 6))
    
    # 3. Quels résultats ?
    story.append(Paragraph("3. Quels résultats concrets et mesurables ont été obtenus ?", styles['Sec2Title']))
    story.append(Paragraph(
        "Les campagnes de tests et de qualification industrielle menées chez Alidentec démontrent l'excellence des résultats obtenus :", styles['Body']
    ))
    story.append(Paragraph(
        "&bull; <b>Zéro collision de surréservation :</b> 100% de succès sur les tests de charge concurrents (30 réservations simultanées à concurrence 15).<br/>"
        "&bull; <b>Clôture Night Audit ultra-rapide :</b> Exécution automatisée en <b>45 secondes</b> pour 50 suites (contre plus d'une heure en manuel).<br/>"
        "&bull; <b>Latence optimisée de -74% :</b> Temps de réponse p95 ramené de 2338 ms à <b>604 ms</b> après optimisation asynchrone.<br/>"
        "&bull; <b>100% de succès sur les tests unitaires :</b> Les 10 suites Pytest fondamentales validées avec 0 échec.<br/>"
        "&bull; <b>Certification SonarQube :</b> Statut officiel <i>Quality Gate : Passed</i> avec 0 vulnérabilité et une note maximale A.<br/>"
        "&bull; <b>Sécurité sans mot de passe certifiée :</b> Connexion biométrique fluide en moins de 2 secondes sur poste fixe via smartphone.",
        styles['ReportBullet']
    ))
    story.append(Spacer(1, 6))
    
    # 4. Quelles perspectives ?
    story.append(Paragraph("4. Quelles sont les perspectives d'évolution future ?", styles['Sec2Title']))
    story.append(Paragraph(
        "Les perspectives à court et moyen terme s'articulent autour de l'intégration d'un moteur de tarification prédictive basé sur l'Intelligence Artificielle "
        "(Machine Learning pour l'optimisation du RevPAR), le déploiement sur un cluster Kubernetes multi-zones managé avec Auto-Scaling horizontal, "
        "et la certification des connecteurs directs 2-Way avec les API partenaires de Booking.com et Airbnb.",
        styles['Body']
    ))
    story.append(PageBreak())
    
    # ── BIBLIOGRAPHIE & WEBOGRAPHIE ─────────────────────────────────────────
    story.append(Paragraph("BIBLIOGRAPHIE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    biblio_items = [
        ("[1]", "FOWLER, Martin. <i>Patterns of Enterprise Application Architecture</i>. Addison-Wesley Professional, 2002. ISBN : 978-0321127426."),
        ("[2]", "EVANS, Eric. <i>Domain-Driven Design: Tackling Complexity in the Heart of Software</i>. Addison-Wesley, 2003. ISBN : 978-0321125217."),
        ("[3]", "NEWMAN, Sam. <i>Building Microservices: Designing Fine-Grained Systems</i>. 2nd Edition, O'Reilly Media, 2021. ISBN : 978-1492034025."),
        ("[4]", "RICHARDSON, Chris. <i>Microservices Patterns: With examples in Java</i>. Manning Publications, 2018. ISBN : 978-1617294549."),
        ("[5]", "MARTIN, Robert C. <i>Clean Architecture: A Craftsman's Guide to Software Structure and Design</i>. Prentice Hall, 2017. ISBN : 978-0134494166."),
        ("[6]", "W3C & FIDO ALLIANCE. <i>Web Authentication: An API for accessing Public Key Credentials Level 2 & 3</i>. W3C Recommendation, 2021."),
        ("[7]", "ROYAUME DU MAROC. <i>Loi n° 09-08 relative à la protection des personnes physiques à l'égard du traitement des données à caractère personnel</i>. Bulletin Officiel, 2009."),
        ("[8]", "ROYAUME DU MAROC. <i>Code Général des Impôts : Dispositions relatives à la TVA et aux taxes de séjour touristiques</i>. Direction Générale des Impôts, 2025.")
    ]
    
    t_bib_rows = []
    for ref, txt in biblio_items:
        t_bib_rows.append([Paragraph(f"<b>{ref}</b>", styles['TblCellBold']), Paragraph(txt, styles['TblCell'])])
    t_bib = Table(t_bib_rows, colWidths=[usable_width * 0.10, usable_width * 0.90])
    t_bib.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_bib)
    story.append(Spacer(1, 14))
    
    story.append(Paragraph("WEBOGRAPHIE", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    webo_items = [
        ("[W1]", "<b>FastAPI Official Documentation :</b> Modern, fast (high-performance), web framework for building APIs with Python 3.8+.<br/><font color='#0080A0'><u>https://fastapi.tiangolo.com/</u></font> (Consulté en mai 2026)."),
        ("[W2]", "<b>Next.js 14 Documentation :</b> The React Framework for the Web (App Router, Server Components).<br/><font color='#0080A0'><u>https://nextjs.org/docs</u></font> (Consulté en mai 2026)."),
        ("[W3]", "<b>Keycloak Documentation :</b> Open Source Identity and Access Management for Modern Applications.<br/><font color='#0080A0'><u>https://www.keycloak.org/documentation</u></font> (Consulté en avril 2026)."),
        ("[W4]", "<b>Redis Distributed Locks (Redlock Algorithm) :</b> Distributed locks with Redis.<br/><font color='#0080A0'><u>https://redis.io/docs/manual/patterns/distributed-locks/</u></font> (Consulté en mars 2026)."),
        ("[W5]", "<b>RabbitMQ AMQP Documentation :</b> Messaging that just works — Tutorials and Best Practices.<br/><font color='#0080A0'><u>https://www.rabbitmq.com/documentation.html</u></font> (Consulté en avril 2026)."),
        ("[W6]", "<b>PostgreSQL 15 Documentation :</b> The World's Most Advanced Open Source Relational Database.<br/><font color='#0080A0'><u>https://www.postgresql.org/docs/15/</u></font> (Consulté en février 2026)."),
        ("[W7]", "<b>SonarQube Documentation :</b> Continuous Code Quality & Security Inspection Platform.<br/><font color='#0080A0'><u>https://docs.sonarqube.org/latest/</u></font> (Consulté en mai 2026)."),
        ("[W8]", "<b>OWASP Foundation :</b> OWASP Top 10 Web Application Security Risks.<br/><font color='#0080A0'><u>https://owasp.org/www-project-top-ten/</u></font> (Consulté en mai 2026).")
    ]
    
    t_web_rows = []
    for ref, txt in webo_items:
        t_web_rows.append([Paragraph(f"<b>{ref}</b>", styles['TblCellBold']), Paragraph(txt, styles['TblCell'])])
    t_web = Table(t_web_rows, colWidths=[usable_width * 0.10, usable_width * 0.90])
    t_web.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_web)
    story.append(PageBreak())
    
    # ── ANNEXES TECHNIQUES ───────────────────────────────────────────────────
    story.append(Paragraph("ANNEXES TECHNIQUES", styles['ChapTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=14))
    
    story.append(Paragraph("Annexe 1 : Extrait de Configuration Docker Compose Multi-Services", styles['Sec2Title']))
    story.append(Paragraph(
        "Extrait du fichier <code>docker-compose.yml</code> orchestrant l'infrastructure réseau privée, la passerelle Kong et les microservices :",
        styles['Body']
    ))
    
    code_text = (
        "version: '3.8'\n"
        "services:\n"
        "  kong-gateway:\n"
        "    image: kong:3.4-alpine\n"
        "    environment:\n"
        "      KONG_DATABASE: 'off'\n"
        "      KONG_DECLARATIVE_CONFIG: /etc/kong/kong.yml\n"
        "      KONG_PROXY_ACCESS_LOG: /dev/stdout\n"
        "    ports:\n"
        "      - '8000:8000'\n"
        "    networks:\n"
        "      - pms-internal-net\n\n"
        "  reservation-service:\n"
        "    build: ./services/reservation-service\n"
        "    environment:\n"
        "      DATABASE_URL: postgresql+asyncpg://resv_u:resv_p@postgres:5432/resv_db\n"
        "      REDIS_URL: redis://redis:6379/0\n"
        "      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/\n"
        "    depends_on:\n"
        "      - postgres\n"
        "      - redis\n"
        "      - rabbitmq\n"
        "    networks:\n"
        "      - pms-internal-net\n"
    )
    
    story += make_callout(f"<font face='Courier' size='7.5'>{code_text.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>",
                          "EXTRAIT DOCKER-COMPOSE.YML (ORCHESTRATION DES SERVICES)", styles=styles)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Annexe 2 : Exemple de Payload JSON et Schéma Pydantic v2", styles['Sec2Title']))
    story.append(Paragraph(
        "Modèle Pydantic de création de réservation avec validation de date et politique d'arrondi monétaire :", styles['Body']
    ))
    
    pydantic_code = (
        "from pydantic import BaseModel, Field, field_validator\n"
        "from decimal import Decimal\n"
        "from datetime import date\n"
        "from uuid import UUID\n\n"
        "class BookingCreateRequest(BaseModel):\n"
        "    room_id: UUID\n"
        "    guest_id: UUID\n"
        "    check_in: date\n"
        "    check_out: date\n"
        "    adults_count: int = Field(ge=1, le=6)\n"
        "    base_night_rate: Decimal = Field(gt=0, decimal_places=2)\n\n"
        "    @field_validator('check_out')\n"
        "    def validate_dates(cls, v, values):\n"
        "        if 'check_in' in values.data and v <= values.data['check_in']:\n"
        "            raise ValueError('La date de départ doit être strictement postérieure à l\\'arrivée.')\n"
        "        return v\n"
    )
    story += make_callout(f"<font face='Courier' size='7.5'>{pydantic_code.replace(chr(10), '<br/>').replace(' ', '&nbsp;')}</font>",
                          "SCHÉMA PYDANTIC V2 DE VALIDATION DES RÉSERVATIONS", styles=styles)
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("Annexe 3 : Matrice des Données d'Essais et Fixtures de Référence", styles['Sec2Title']))
    story.append(Paragraph(
        "Tableau récapitulatif des suites pilotes enregistrées dans les fixtures du Riad Yasmine pour les campagnes de tests :", styles['Body']
    ))
    
    fixtures_data = [
        ["Numéro Suite", "Dénomination", "Catégorie", "Capacité", "Tarif Base HT", "Taux TVA", "TS Communale"],
        ["Suite 101", "Suite Royale Bahia", "Suite Royale", "4 personnes", "2 500.00 MAD", "10% (250 MAD)", "25 MAD / pers."],
        ["Suite 102", "Suite Junior Majorelle", "Suite Junior", "2 personnes", "1 800.00 MAD", "10% (180 MAD)", "25 MAD / pers."],
        ["Chambre 201", "Chambre Deluxe Koutoubia", "Chambre Deluxe", "2 personnes", "1 200.00 MAD", "10% (120 MAD)", "25 MAD / pers."],
        ["Chambre 202", "Chambre Deluxe Menara", "Chambre Deluxe", "2 personnes", "1 200.00 MAD", "10% (120 MAD)", "25 MAD / pers."],
        ["Chambre 203", "Chambre Supérieure Agdal", "Chambre Supérieure", "2 personnes", "950.00 MAD", "10% (95 MAD)", "25 MAD / pers."]
    ]
    story += make_table(fixtures_data, [usable_width * 0.14, usable_width * 0.24, usable_width * 0.18, usable_width * 0.14, usable_width * 0.14, usable_width * 0.16],
                        "Tableau A-1 : Inventaire des suites de test du Riad pilote (Fixtures de référence)", styles)
    
    return story
