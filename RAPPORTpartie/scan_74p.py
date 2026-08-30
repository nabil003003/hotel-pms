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
    ("Table des Matières", "TABLE DES MATIERES", 1),
    ("Liste des Figures", "LISTE DES FIGURES", 1),
    ("Liste des Tableaux", "LISTE DES TABLEAUX", 1),
    ("Introduction Générale", "INTRODUCTION GENERALE", 10),
    ("Chapitre 1 : Intercalaire", "CHAPITRE 1", 12),
    ("Chapitre 1 : Contenu", "1.1 INTRODUCTION", 13),
    ("Chapitre 2 : Intercalaire", "CHAPITRE 2", 18),
    ("Chapitre 2 : Contenu", "2.1 INTRODUCTION", 19),
    ("Chapitre 3 : Intercalaire", "CHAPITRE 3", 30),
    ("Chapitre 3 : Contenu", "3.1 INTRODUCTION", 33),
    ("Chapitre 4 : Intercalaire", "CHAPITRE 4", 40),
    ("Chapitre 4 : Contenu", "4.1 INTRODUCTION", 42),
    ("Chapitre 5 : Intercalaire", "CHAPITRE 5", 55),
    ("Chapitre 5 : Contenu", "5.1 INTRODUCTION", 58),
    ("Chapitre 6 : Intercalaire", "CHAPITRE 6", 63),
    ("Chapitre 6 : Contenu", "6.1 INTRODUCTION", 65),
    ("Conclusion Générale", "CONCLUSION GENERALE", 67),
    ("Bibliographie", "BIBLIOGRAPHIE", 70),
    ("Webographie", "WEBOGRAPHIE", 70),
    ("Annexes Techniques", "ANNEXES TECHNIQUES", 72)
]

print(f"Total pages: {len(doc)}")
for name, query, start_p in targets:
    found_p = None
    for p in range(start_p - 1, len(doc)):
        txt = strip_accents(doc[p].get_text()).upper()
        if p < 10 and "TABLE DES MATIERES" in txt and query != "TABLE DES MATIERES":
            continue
        if query in txt:
            found_p = p + 1
            break
    arabic_p = found_p - 10 if found_p and found_p > 10 else 'N/A'
    print(f"  {name:30s} -> PDF Page {found_p:2d} (Numbered Page {arabic_p})")
