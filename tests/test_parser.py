import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
# Adiciona o diretório raiz ao path para permitir a importação de 'crawler'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bs4 import BeautifulSoup
from crawler.parsers import extract_price_from_search

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

files = [
    ('debug_ml.html',     'Mercado Livre'),
    ('debug_kabum.html',  'KaBuM!'),
    ('debug_tera.html',   'Terabyteshop'),
    ('debug_pichau.html', 'Pichau'),
]

print("--- Teste Sem Filtros (Primeiro Produto Qualquer) ---")
for filename, loja in files:
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, encoding='utf-8') as f:
        html = f.read()
    preco, link = extract_price_from_search(html, loja)
    print(f"[{loja}] Preco: {preco} | Link: {link}")

print("\n--- Teste Com Filtros (PlayStation 5, min R$ 2000) ---")
for filename, loja in files:
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, encoding='utf-8') as f:
        html = f.read()
    preco, link = extract_price_from_search(html, loja, preco_minimo=2000.0, query="PlayStation 5")
    print(f"[{loja}] Preco: {preco} | Link: {link}")
