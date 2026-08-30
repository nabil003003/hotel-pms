import fitz
import unicodedata

doc = fitz.open('PMSV2-main/RAPPORTpartie/RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

targets = [
    ("Chapitre 1 : Présentation", "CHAPITRE 1"),
    ("Chapitre 2 : Analyse des Besoins", "CHAPITRE 2"),
    ("Chapitre 3 : Conception Technique", "CHAPITRE 3"),
    ("Chapitre 4 : Réalisation", "CHAPITRE 4"),
    ("Chapitre 5 : Tests & Qualité", "CHAPITRE 5"),
    ("Chapitre 6 : Bilan du Stage", "CHAPITRE 6"),
    ("Conclusion Générale", "CONCLUSION GENERALE"),
    ("Bibliographie", "BIBLIOGRAPHIE"),
    ("Webographie", "WEBOGRAPHIE"),
    ("Annexes Techniques", "ANNEXES TECHNIQUES")
]

print("Scanning pages 10 to", len(doc))
for name, query in targets:
    found_page = None
    for p in range(10, len(doc)):
        txt = strip_accents(doc[p].get_text()).upper()
        if query in txt:
            found_page = p + 1
            break
    arabic_page = found_page - 10 if found_page else 'N/A'
    print(f"  {name:35s} -> PDF Page {found_page:2d} (Numbered Page {arabic_page})")
