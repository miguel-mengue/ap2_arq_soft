import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
from bs4 import BeautifulSoup

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tests', 'fixtures'))

def inspect_html(filename, store_name, link_selector):
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    print(f"\n{'='*60}")
    print(f"=== {store_name} PRICE CLASSES ===")
    items = soup.find_all(class_=lambda c: c and 'price' in c.lower())
    for el in items[:8]:
        txt = el.get_text(strip=True)[:80].encode('ascii', errors='replace').decode()
        print(el.get('class'), '|', txt)
    
    print(f"\n=== {store_name} PRODUCT LINKS ===")
    links = soup.select(link_selector)
    for l in links[:5]:
        print(l.get('href', '')[:120])
    
    # Procura qualquer texto com R$
    print(f"\n=== {store_name} R$ TEXTS ===")
    rs = [el for el in soup.find_all(string=True) if 'R$' in str(el)]
    for r in rs[:5]:
        parent = r.parent
        txt = str(r).strip()[:60].encode('ascii', errors='replace').decode()
        print(parent.get('class'), '|', txt)

inspect_html('debug_ml.html',     'ML',       'a[href*="MLB"]')
inspect_html('debug_kabum.html',  'KABUM',    'a[href*="/produto/"]')
inspect_html('debug_tera.html',   'TERABYTE', 'a[href*="/produto/"]')
inspect_html('debug_pichau.html', 'PICHAU',   'a[href*="/produto/"]')
