import glob

files = glob.glob('PMSV2-main/RAPPORTpartie/gen_*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        txt = fp.read()
    if 'Table(' in txt and 'from reportlab.platypus' in txt:
        if 'Table' not in txt.split('from reportlab.platypus import')[1].split('\n')[0]:
            print(f"Adding Table imports to {f}")
            txt = txt.replace('from reportlab.platypus import Paragraph', 'from reportlab.platypus import Paragraph, Table, TableStyle')
            with open(f, 'w', encoding='utf-8') as fp:
                fp.write(txt)
print("Import check completed.")
