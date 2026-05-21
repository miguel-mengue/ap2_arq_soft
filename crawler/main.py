import json
import asyncio
import urllib.parse
from datetime import date
import os
from .models import Produto, RegistroHistorico
from .fetcher import CrawlerFetcher
from .parsers import extract_price_from_search

# Preço mínimo esperado por categoria de produto (em R$)
# Evita que o parser confunda acessórios baratos com o produto principal
PRECO_MINIMO_PADRAO = 100.0
PRECO_MINIMO_MAP = {
    "placa de video": 800.0,
    "playstation":    2000.0,
    "xbox":           1500.0,
    "notebook":       1500.0,
    "processador":    500.0,
    "monitor":        600.0,
    "controle":       200.0,
}

def inferir_preco_minimo(nome_produto: str) -> float:
    nome_lower = nome_produto.lower()
    for chave, minimo in PRECO_MINIMO_MAP.items():
        if chave in nome_lower:
            return minimo
    return PRECO_MINIMO_PADRAO

def build_search_url(base_url: str, loja: str, query: str) -> str:
    """Monta a URL de pesquisa a partir da base_url fornecida no JSON"""
    loja_lower = loja.lower()
    base_url = base_url.rstrip("/")
    if loja_lower == "amazon":
        return f"{base_url}/s?k={urllib.parse.quote_plus(query)}"
    elif loja_lower == "mercado livre" or loja_lower == "mercadolivre":
        # ML usa "lista.mercadolivre.com.br" para busca, vamos adaptar se ele der apenas a home
        if "lista." not in base_url:
            base_url = base_url.replace("www.", "lista.")
        return f"{base_url}/{query.replace(' ', '-')}"
    elif "kabum" in loja_lower:
        return f"{base_url}/busca/{urllib.parse.quote_plus(query)}"
    elif "terabyte" in loja_lower:
        return f"{base_url}/busca?str={urllib.parse.quote_plus(query)}"
    elif "pichau" in loja_lower:
        return f"{base_url}/search?q={urllib.parse.quote_plus(query)}"
    else:
        # Fallback genérico para lojas novas
        return f"{base_url}/busca?q={urllib.parse.quote_plus(query)}"

async def run_crawler():
    if not os.path.exists("produtos.json"):
        print("Arquivo produtos.json não encontrado.")
        return
        
    with open("produtos.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        produtos = [Produto.from_dict(p) for p in data]
        
    print(f"Iniciando crawler para {len(produtos)} produtos...")
    fetcher = CrawlerFetcher(headless=True)
    await fetcher.start()
    
    historico_novo = []
    
    try:
        for produto in produtos:
            print(f"\n=========================================")
            print(f"Produto: {produto.nome}")
            menor_preco = None
            loja_menor_preco = None
            link_menor_preco = None
            preco_minimo = inferir_preco_minimo(produto.nome)
            
            for link in produto.links:
                print(f" -> Acessando loja {link.loja} a partir de {link.url}...")
                search_url = build_search_url(link.url, link.loja, produto.nome)
                
                html = await fetcher.fetch_html(search_url)
                preco, link_produto = extract_price_from_search(html, link.loja, preco_minimo, query=produto.nome)
                
                if preco is not None:
                    print(f"    Preço encontrado na busca: R$ {preco:.2f}")
                    if menor_preco is None or preco < menor_preco:
                        menor_preco = preco
                        loja_menor_preco = link.loja
                        link_menor_preco = link_produto
                else:
                    print(f"    [!] Não foi possível extrair o preço na vitrine da {link.loja}.")
            
            if menor_preco is not None:
                registro = RegistroHistorico(
                    produto=produto.nome,
                    preco=menor_preco,
                    loja=loja_menor_preco,
                    data=date.today().isoformat(),
                    url=link_menor_preco
                )
                historico_novo.append(registro.to_dict())
                print(f"\n=> RESULTADO: O menor preço de '{produto.nome}' é R$ {menor_preco:.2f} na loja {loja_menor_preco}")
            else:
                print(f"\n=> RESULTADO: Não foi encontrado preço válido para '{produto.nome}'.")
    finally:
        await fetcher.stop()
        
    if historico_novo:
        salvar_historico(historico_novo)

def salvar_historico(novos_registros):
    arquivo_hist = "historico.json"
    historico_atual = []
    if os.path.exists(arquivo_hist):
        try:
            with open(arquivo_hist, "r", encoding="utf-8") as f:
                historico_atual = json.load(f)
        except json.JSONDecodeError:
            historico_atual = []
            
    historico_atual.extend(novos_registros)
    with open(arquivo_hist, "w", encoding="utf-8") as f:
        json.dump(historico_atual, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Histórico atualizado! ({len(novos_registros)} novos registros em {arquivo_hist})")

if __name__ == "__main__":
    asyncio.run(run_crawler())
