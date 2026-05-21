import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler.fetcher import CrawlerFetcher
from crawler.parsers import BeautifulSoup, _parse_kabum_search, _clean_price, _match_title

async def main():
    fetcher = CrawlerFetcher(headless=True)
    await fetcher.start()
    try:
        url = "https://www.kabum.com.br/busca/Placa+de+Video+RTX+4060"
        html = await fetcher.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        
        cards = soup.find_all('a', href=lambda h: h and '/produto/' in h)
        print(f"Total cards found: {len(cards)}")
        for idx, card in enumerate(cards[:20]):
            href = card.get("href", "")
            title_el = card.select_one("span.text-gray-800")
            title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)
            
            prices = []
            for span in card.find_all('span', class_=lambda cl: cl and 'text-base' in cl and 'font-semibold' in cl):
                val = _clean_price(span.get_text())
                if val:
                    prices.append(val)
            if not prices:
                import re
                for pt in re.findall(r'R\$\s*[\d\.,]+', card.get_text()):
                    val = _clean_price(pt)
                    if val:
                        prices.append(val)
            
            matches = _match_title(title, "Placa de Video RTX 4060")
            print(f"Card {idx}: Title={title[:80]} | Prices={prices} | Matches={matches} | Href={href[:60]}")
    finally:
        await fetcher.stop()

if __name__ == '__main__':
    asyncio.run(main())
