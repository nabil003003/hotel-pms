with open('PMSV2-main/RAPPORTpartie/build_alidentec_pfa_80p.py', 'r', encoding='utf-8') as fp:
    txt = fp.read()

txt = txt.replace('✅', '[SUCCES]')
txt = txt.replace('📄', '[INFO]')
txt = txt.replace('—', '-')
txt = txt.replace('–', '-')

header = "import sys\nif hasattr(sys.stdout, 'reconfigure'):\n    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
if "sys.stdout.reconfigure" not in txt:
    txt = header + txt

with open('PMSV2-main/RAPPORTpartie/build_alidentec_pfa_80p.py', 'w', encoding='utf-8') as fp:
    fp.write(txt)

print("build_alidentec_pfa_80p.py updated cleanly.")
