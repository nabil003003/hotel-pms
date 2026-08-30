import fitz
import os

doc = fitz.open('PMSV2-main/RAPPORTpartie/RAPPORT_STAGE_ALIDENTEC_PMS_80P.pdf')
out_dir = 'PMSV2-main/RAPPORTpartie/pdf_previews'
os.makedirs(out_dir, exist_ok=True)

# Render pages to preview images: page 1 (cover), page 22 (chap 2), page 43 (chap 4 - UI), page 44 (table_ / tape chart)
pages_to_render = [1, 13, 22, 28, 36, 43, 44, 45, 46, 53, 59]

for p_num in pages_to_render:
    if p_num <= len(doc):
        page = doc[p_num - 1]
        pix = page.get_pixmap(dpi=150)
        out_path = os.path.join(out_dir, f'page_{p_num:02d}.png')
        pix.save(out_path)
        print(f"Rendered page {p_num} -> {out_path}")

print("Previews rendered successfully.")
