import glob

files = glob.glob('PMSV2-main/RAPPORTpartie/gen_*.py') + glob.glob('PMSV2-main/RAPPORTpartie/build_*.py')
for f in files:
    with open(f, 'r', encoding='utf-8') as fp:
        txt = fp.read()
    if "'Bullet'" in txt or '"Bullet"' in txt:
        print(f, "has Bullet")
        # Replace 'Bullet' with 'ReportBullet'
        txt = txt.replace("styles['Bullet']", "styles['ReportBullet']")
        txt = txt.replace("styles.add(ParagraphStyle(\n        'Bullet',", "styles.add(ParagraphStyle(\n        'ReportBullet',")
        txt = txt.replace("styles.add(ParagraphStyle('Bullet',", "styles.add(ParagraphStyle('ReportBullet',")
        with open(f, 'w', encoding='utf-8') as fp:
            fp.write(txt)
print("Replacement completed.")
