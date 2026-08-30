import fitz

doc = fitz.open('PMSV2-main/RAPPORTpartie/RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')

sections = [
    ("Dédicace", "DEDICACE"),
    ("Remerciements", "REMERCIEMENTS"),
    ("Résumé & Abstract", "RESUME"),
    ("Glossaire Technique", "GLOSSAIRE"),
    ("Table des Matières", "TABLE DES"),
    ("Liste des Figures", "LISTE DES FIGURES"),
    ("Liste des Tableaux", "LISTE DES TABLEAUX"),
    ("Chapitre 1", "CHAPITRE 1"),
    ("Chapitre 2", "CHAPITRE 2"),
    ("Chapitre 3", "CHAPITRE 3"),
    ("Chapitre 4", "CHAPITRE 4"),
    ("Chapitre 5", "CHAPITRE 5"),
    ("Chapitre 6", "CHAPITRE 6"),
    ("Conclusion Générale", "CONCLUSION"),
    ("Bibliographie", "BIBLIOGRAPHIE"),
    ("Webographie", "WEBOGRAPHIE"),
    ("Annexes Techniques", "ANNEXES")
]

import unicodedata
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

print("\n--- ACTUAL START PAGES ---")
for title, query in sections:
    q_clean = strip_accents(query).upper()
    found_page = None
    for p in range(len(doc)):
        txt = strip_accents(doc[p].get_text()).upper()
        # skip TOC page matches
        if p < 12 and "TABLE DES MATIERES" in txt and query != "TABLE DES":
            continue
        if q_clean in txt:
            found_page = p + 1
            break
    print(f"  {title:35s} -> Page {found_page}")
