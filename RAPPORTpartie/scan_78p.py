import fitz
import unicodedata

doc = fitz.open('PMSV2-main/RAPPORTpartie/RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

targets = [
    ("Dédicace", "DEDICACE", 1),
    ("Remerciements", "REMERCIEMENTS", 1),
    ("Résumé & Abstract", "RESUME", 1),
    ("Glossaire Technique", "GLOSSAIRE", 1),
    ("Table des Matières", "TABLE DES", 1),
    ("Liste des Figures", "LISTE DES FIGURES", 1),
    ("Liste des Tableaux", "LISTE DES TABLEAUX", 1),
    ("Introduction Générale", "INTRODUCTION GENERALE", 10),
    ("Chapitre 1 : Intercalaire", "CHAPITRE 1", 11),
    ("Chapitre 2 : Intercalaire", "CHAPITRE 2", 20),
    ("Chapitre 3 : Intercalaire", "CHAPITRE 3", 35),
    ("Chapitre 4 : Intercalaire", "CHAPITRE 4", 43),
    ("Chapitre 5 : Intercalaire", "CHAPITRE 5", 59),
    ("Chapitre 6 : Intercalaire", "CHAPITRE 6", 67),
    ("Conclusion Générale", "CONCLUSION GENERALE", 70),
    ("Bibliographie", "BIBLIOGRAPHIE", 72),
    ("Webographie", "WEBOGRAPHIE", 72),
    ("Annexes Techniques", "ANNEXES TECHNIQUES", 74)
]

print(f"Total pages in PDF: {len(doc)}")
for name, query, start_p in targets:
    found_p = None
    for p in range(start_p - 1, len(doc)):
        txt = strip_accents(doc[p].get_text()).upper()
        if p < 10 and "TABLE DES MATIERES" in txt and query != "TABLE DES":
            continue
        if query in txt:
            found_p = p + 1
            break
    arabic_p = found_p - 10 if found_p and found_p > 10 else 'N/A'
    print(f"  {name:30s} -> PDF Page {found_p:2d} (Numbered Page {arabic_p})")
