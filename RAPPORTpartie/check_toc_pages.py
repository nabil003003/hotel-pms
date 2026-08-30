import fitz

doc = fitz.open('PMSV2-main/RAPPORTpartie/RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')
print(f"Total pages in PDF: {len(doc)}")

sections = [
    "DÉDICACE",
    "REMERCIEMENTS",
    "RÉSUMÉ",
    "ABSTRACT",
    "GLOSSAIRE TECHNIQUE",
    "TABLE DES MATIÈRES",
    "LISTE DES FIGURES",
    "LISTE DES TABLEAUX",
    "CHAPITRE 1",
    "1.1 Introduction",
    "1.2 Présentation de l'Entreprise",
    "1.3 Présentation du Stage",
    "1.4 Présentation du Projet",
    "1.5 Méthodologie",
    "1.6 Planification",
    "1.7 Conclusion",
    "CHAPITRE 2",
    "2.1 Introduction",
    "2.2 Étude et Critique",
    "2.3 Solution Proposée",
    "2.4 Identification des Acteurs",
    "2.5 Spécification Détaillée",
    "2.6 Spécification des Besoins",
    "2.7 Modélisation UML des Cas",
    "2.8 Modélisation UML Dynamique",
    "2.9 Modélisation UML Structurelle",
    "2.10 Architecture Fonctionnelle",
    "2.11 Conclusion",
    "CHAPITRE 3",
    "3.1 Introduction",
    "3.2 Architecture Technique",
    "3.3 Architecture Logicielle",
    "3.4 Écosystème Technologique Frontend",
    "3.5 Écosystème Technologique Backend",
    "3.6 Persistance",
    "3.7 Sécurité",
    "3.8 Outils",
    "3.9 Spécification des Contrats",
    "3.10 Conclusion",
    "CHAPITRE 4",
    "4.1 Introduction",
    "4.2 Mise en Place",
    "4.3 Développement Backend",
    "4.4 Développement Frontend",
    "4.5 Présentation Détaillée",
    "4.6 Intégration Globale",
    "4.7 Bilan des Contributions",
    "4.8 Difficultés Techniques",
    "4.9 Conclusion",
    "CHAPITRE 5",
    "5.1 Introduction",
    "5.2 Stratégie Globale",
    "5.3 Suites de Tests",
    "5.4 Tests d'Intégration",
    "5.5 Tests de Contrats",
    "5.6 Tests Fonctionnels",
    "5.7 Tests de Charge",
    "5.8 Tests de Sécurité",
    "5.9 Audit de Qualité",
    "5.10 Conclusion",
    "CHAPITRE 6",
    "6.1 Introduction",
    "6.2 Apports Techniques",
    "6.3 Apports Professionnels",
    "6.4 Enseignements Organisationnels",
    "6.5 Matrice des Compétences",
    "6.6 Contributions Personnelles",
    "6.7 Perspectives d'Évolution",
    "6.8 Conclusion",
    "CONCLUSION GÉNÉRALE",
    "BIBLIOGRAPHIE",
    "WEBOGRAPHIE",
    "ANNEXES TECHNIQUES"
]

page_map = {}
for i, page in enumerate(doc):
    text = page.get_text()
    for sec in sections:
        if sec not in page_map and sec.upper() in text.upper():
            page_map[sec] = i + 1

print("\n--- EXACT PAGE NUMBERS FOUND ---")
for sec in sections:
    print(f"  {sec:35s} -> Page {page_map.get(sec, 'N/A')}")
