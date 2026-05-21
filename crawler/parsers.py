import re
import unicodedata
from bs4 import BeautifulSoup

def normalize_text(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    return "".join([c for c in text if not unicodedata.combining(c)]).lower()

def _match_title(title: str, query: str) -> bool:
    if not query:
        return True
    
    title_norm = normalize_text(title)
    query_norm = normalize_text(query)
    
    # 1. Filtro de palavras negativas para evitar falsos positivos de categorias diferentes
    # Se procuramos uma Placa de Vídeo
    if 'placa' in query_norm:
        negatives = ['notebook', 'computador', 'pc gamer', 'monitor', 'gabinete', 'kit gamer', 'computador gamer']
        if any(neg in title_norm for neg in negatives):
            return False
            
    # Se procuramos o Console PlayStation 5
    if 'playstation 5' in query_norm or 'ps5' in query_norm:
        if 'controle' not in query_norm and 'jogo' not in query_norm and 'base' not in query_norm:
            is_console = 'console' in title_norm
            negatives = ['base', 'headset', 'suporte', 'carregador', 'cabo', 'tampa', 'case', 'capa', 'pasta termica', 'ssd', 'portal', 'skin', 'volante', 'hd externo', 'adaptador', 'camera']
            if not is_console:
                negatives.extend(['controle', 'jogo'])
            if any(neg in title_norm for neg in negatives):
                return False
                
    # Se procuramos o Controle
    if 'controle' in query_norm:
        negatives = ['console', 'suporte', 'carregador', 'cabo', 'capa', 'grip', 'analogo']
        if any(neg in title_norm for neg in negatives):
            return False

    # 2. Verificação de números de modelos
    query_numbers = re.findall(r'\b\d+\w*\b', query_norm)
    if ('playstation' in query_norm or 'ps5' in query_norm) and any(x in title_norm for x in ['playstation', 'ps5', 'ps4']):
        query_numbers = [n for n in query_numbers if n != '5']
        
    for num in query_numbers:
        if len(num) > 1 or num in ('5', '4'):
            if num not in title_norm:
                return False
                
    # 3. Verificação de palavras-chave importantes da GPU
    if 'rtx' in query_norm and 'rtx' not in title_norm:
        return False
    if 'gtx' in query_norm and 'gtx' not in title_norm:
        return False
        
    return True

def extract_price_from_search(html: str, store: str, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """
    Extrai o preço e a URL diretamente do primeiro resultado na página de busca que atenda aos critérios.
    preco_minimo: descarta resultados abaixo desse valor (evita pegar acessórios).
    Retorna uma tupla: (preco, url_do_produto)
    """
    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")
    store_lower = store.lower()

    if "mercado livre" in store_lower or "mercadolivre" in store_lower:
        return _parse_mercadolivre_search(soup, preco_minimo, query)
    elif "kabum" in store_lower:
        return _parse_kabum_search(soup, preco_minimo, query)
    elif "terabyte" in store_lower:
        return _parse_terabyte_search(soup, preco_minimo, query)
    elif "pichau" in store_lower:
        return _parse_pichau_search(soup, preco_minimo, query)
    elif "amazon" in store_lower:
        return _parse_amazon_search(soup, preco_minimo, query)
    else:
        print(f"Aviso: Loja '{store}' não suportada pelo parser ainda.")
        return None, None

def _clean_price(text: str) -> float | None:
    """Converte uma string de preço (ex: 'R$ 4.230,00' ou 'R$ 4.230') para float."""
    try:
        s = re.sub(r'[^\d,.]', '', text)
        if ',' in s:
            # Tem vírgula: formato brasileiro. Remove pontos (milhar) e troca vírgula por ponto (decimal)
            s = s.replace('.', '').replace(',', '.')
        else:
            # Não tem vírgula: pode ser formato US (169.99) ou brasileiro sem centavos (4.230)
            # Se houver um ponto seguido de exatamente 3 dígitos no final, é separador de milhar.
            if re.search(r'\.\d{3}$', s):
                s = s.replace('.', '')
            # Caso contrário, mantém o ponto como separador decimal.
        return float(s) if s else None
    except Exception:
        return None

def _parse_mercadolivre_search(soup: BeautifulSoup, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """
    Parser para Mercado Livre. Agrupa elementos usando a classe de card .poly-card.
    """
    cards = soup.select(".poly-card")
    for card in cards:
        title_el = card.select_one(".poly-component__title")
        if not title_el:
            continue
        href = title_el.get("href", "")
        if not href:
            continue
        href = href.split("#")[0]

        title = title_el.get_text(strip=True)
        if query and not _match_title(title, query):
            continue

        price_el = card.select_one(".poly-price__current .andes-money-amount__fraction")
        if not price_el:
            # Fallback para qualquer fração de preço dentro do card
            price_el = card.select_one(".andes-money-amount__fraction")
            
        if price_el:
            price = _clean_price(price_el.get_text(strip=True))
            if price and price >= preco_minimo:
                return price, href

    # Fallback se a estrutura de cards mudou
    price_els = soup.select(".poly-price__current .andes-money-amount__fraction")
    link_els  = soup.select("a[href*='mercadolivre.com.br/'][href*='/p/']")
    for price_el, link_el in zip(price_els, link_els):
        price = _clean_price(price_el.get_text(strip=True))
        href  = link_el["href"].split("#")[0]
        if price and price >= preco_minimo:
            return price, href
            
    return None, None

def _parse_kabum_search(soup: BeautifulSoup, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """
    Parser para KaBuM!. Cada produto fica dentro de uma tag <a> que aponta para '/produto/'.
    """
    cards = soup.find_all('a', href=lambda h: h and '/produto/' in h)
    for card in cards:
        href = card.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.kabum.com.br" + href

        title_el = card.select_one("span.text-gray-800")
        title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)
        if query and not _match_title(title, query):
            continue

        # Encontra todas as possíveis ocorrências de preços no card
        prices = []
        for span in card.find_all('span', class_=lambda cl: cl and 'text-base' in cl and 'font-semibold' in cl):
            val = _clean_price(span.get_text())
            if val:
                prices.append(val)
                
        if not prices:
            for pt in re.findall(r'R\$\s*[\d\.,]+', card.get_text()):
                val = _clean_price(pt)
                if val:
                    prices.append(val)

        # Filtra pelo preço mínimo e pega o menor valor (Pix/à vista)
        valid_prices = [p for p in prices if p >= preco_minimo]
        if valid_prices:
            return min(valid_prices), href

    return None, None

def _parse_terabyte_search(soup: BeautifulSoup, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """
    Parser para Terabyteshop. Cada card é a classe '.tss-result-card'.
    """
    cards = soup.select(".tss-result-card")
    for card in cards:
        href = card.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.terabyteshop.com.br" + href

        title_el = card.select_one(".tss-card-name")
        title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)
        if query and not _match_title(title, query):
            continue

        price_el = card.select_one(".tss-card-price")
        if not price_el:
            continue
        price = _clean_price(price_el.get_text(strip=True))
        if price and price >= preco_minimo:
            return price, href

    return None, None

def _parse_pichau_search(soup: BeautifulSoup, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """
    Parser para Pichau. Evita mismatch subindo no máximo 4 níveis e checando se o pai contém outros produtos.
    """
    links = soup.select("a[href*='/produto/']")
    for link_el in links:
        href = link_el.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.pichau.com.br" + href

        title = link_el.get_text(strip=True)
        if not title:
            title_el = link_el.find_next(string=True)
            title = str(title_el).strip() if title_el else ""
            
        if query and title and not _match_title(title, query):
            continue

        parent = link_el.find_parent("div")
        for _ in range(4):
            if not parent:
                break
            
            # Se o pai contiver mais de um produto diferente, saímos para evitar mismatch
            product_links = {a.get("href") for a in parent.find_all("a", href=True) if "/produto/" in a.get("href")}
            if len(product_links) > 1:
                break
                
            price_texts = [el.get_text() for el in parent.find_all(string=True) if 'R$' in str(el)]
            for pt in price_texts:
                price = _clean_price(pt)
                if price and price >= preco_minimo:
                    return price, href
            parent = parent.find_parent("div")

    return None, None

def _parse_amazon_search(soup: BeautifulSoup, preco_minimo: float = 50.0, query: str = "") -> tuple[float | None, str | None]:
    """Parser da Amazon."""
    items = soup.select("div[data-component-type='s-search-result']")
    for item in items:
        asin = item.get("data-asin")
        if asin:
            link_el = item.select_one('h2 a')
            if link_el and "href" in link_el.attrs:
                href = link_el["href"]
                if href.startswith("/"):
                    href = "https://www.amazon.com.br" + href
                href = href.split("?")[0]
                
                title = link_el.get_text(strip=True)
                if query and not _match_title(title, query):
                    continue
                    
                price_el = item.select_one('.a-price .a-offscreen')
                if price_el:
                    price = _clean_price(price_el.get_text(strip=True))
                    if price and price >= preco_minimo:
                        return price, href
    return None, None
