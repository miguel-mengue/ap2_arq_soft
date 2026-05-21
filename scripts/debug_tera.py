import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import os
from bs4 import BeautifulSoup

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests', 'fixtures'))
filepath = os.path.join(FIXTURES_DIR, 'debug_tera.html')

with open(filepath, encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

for i, el in enumerate(soup.select('.tss-card-price')[:3]):
    print(f'--- Card {i+1} ---')
    print('Preco:', el.get_text(strip=True)[:50])
    p = el.parent
    for lvl in range(6):
        if not p:
            break
        link = p.find('a', href=True)
        href_txt = link['href'][:80] if link else 'None'
        classes_txt = str(p.get('class', []))[:50]
        print(f'  nivel {lvl}: tag={p.name} classes={classes_txt} | link={href_txt}')
        p = p.parent
    print()
