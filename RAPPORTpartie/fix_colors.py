import re
with open('PMSV2-main/RAPPORTpartie/gen_diagrams.py', 'r', encoding='utf-8') as f:
    content = f.read()
# Replace HexColor('#XXXXXX') -> '#XXXXXX'
content = re.sub(r"HexColor\('(#[0-9A-Fa-f]+)'\)", r"'\1'", content)
content = re.sub(r'HexColor\("(#[0-9A-Fa-f]+)"\)', r'"\1"', content)
with open('PMSV2-main/RAPPORTpartie/gen_diagrams.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
