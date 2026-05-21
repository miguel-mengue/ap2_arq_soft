# Price Crawler - Comparador de Preços 🛒

Este projeto consiste em um **Web Crawler** desenvolvido para automatizar a busca e comparação de preços de produtos em múltiplos *marketplaces* (e-commerces).

O objetivo do sistema é consumir uma lista de produtos, processar pesquisas dinâmicas nos sites informados (via URL base), realizar a extração do menor preço (*scraping*) e persistir os resultados em um log histórico de preços.

---

## 🚀 Guia de Instalação e Execução

### 1. Preparando o Ambiente
O projeto utiliza bibliotecas modernas de automação e parseamento de HTML. Para executar, instale as dependências e o binário do navegador headless:

```bash
# Crie e ative um ambiente virtual (recomendado)
python -m venv .venv
.\.venv\Scripts\activate

# Instale as dependências e o binário do Chromium
pip install -r requirements.txt
playwright install chromium
```

### 2. Configurando o Input de Dados (`produtos.json`)
O crawler é alimentado pelo arquivo `produtos.json`. Você deve informar o nome do produto desejado e um array de *endpoints* (URLs base) dos *marketplaces* que deseja rastrear.

```json
[
  {
    "nome": "PlayStation 5",
    "links": [
      {
        "loja": "Amazon",
        "url": "https://www.amazon.com.br"
      },
      {
        "loja": "Mercado Livre",
        "url": "https://www.mercadolivre.com.br"
      }
    ]
  }
]
```

### 3. Executando o Crawler
Com o payload configurado, basta rodar o *entrypoint* da aplicação na raiz do projeto:

```bash
python main.py
```

O script irá importar as dependências do pacote `crawler`, orquestrar a geração das URIs de pesquisa, o *fetching* das páginas e a extração. O *output* contendo o menor preço encontrado será serializado em `historico.json`.

Para executar os testes locais com base nos fixtures HTML:
```bash
python tests/test_parser.py
```

---

## 🧩 Arquitetura do Projeto

O sistema foi desenhado visando **Modularidade** e **Separação de Preocupações (Separation of Concerns)**. O projeto está estruturado da seguinte forma:

```
ap2_arq_soft/
├── crawler/                  # Pacote principal com o código-fonte
│   ├── __init__.py
│   ├── main.py               # Lógica de orquestração do crawler
│   ├── models.py             # Modelos de domínio (dataclasses)
│   ├── fetcher.py            # Camada de rede e Playwright (headless)
│   └── parsers.py            # Extratores de preços específicos por loja
├── tests/                    # Testes automatizados e fixtures
│   ├── fixtures/             # Arquivos HTML estáticos para testes offline
│   │   ├── debug_ml.html
│   │   ├── debug_kabum.html
│   │   ├── debug_pichau.html
│   │   ├── debug_tera.html
│   │   ├── kabum.html
│   │   └── ml.html
│   └── test_parser.py        # Executável de testes locais dos parsers
├── scripts/                  # Scripts utilitários e de depuração pontuais
│   ├── debug_selectors.py
│   └── debug_tera.py
├── main.py                   # Entrypoint principal (raiz)
├── produtos.json             # Lista de entrada de produtos (payload)
├── historico.json            # Log histórico de preços gerado
├── requirements.txt          # Dependências do Python
└── README.md                 # Documentação
```

### Componentes Principais (dentro de `crawler/`):

1. **`models.py` (Domain Data Layer)**  
   Utiliza a biblioteca padrão `dataclasses` para definir as entidades principais (`Produto`, `Link`, `RegistroHistorico`). Fornece *type safety* básico e abstrai a lógica de serialização/desserialização de dicionários para objetos em Python.

2. **`fetcher.py` (Network & Headless Browser Layer)**  
   Módulo encarregado de lidar com o *I/O* de rede. Como *e-commerces* utilizam mecanismos rigorosos de *anti-bot*, o módulo encapsula a instância assíncrona do **Playwright**. Ele lança um navegador *headless* (sem interface gráfica) e injeta scripts de *stealth evasion* para burlar captchas e bloqueios de Web Application Firewalls (WAF), entregando o DOM da página limpo para extração.

3. **`parsers.py` (HTML Scraping Layer)**  
   Abstrai o acoplamento aos seletores CSS e estruturas HTML de cada loja. Utilizando o **BeautifulSoup4**, o *parser* localiza os nós do DOM que contêm o preço nos *cards* da vitrine de pesquisa, limpa a formatação da string (regex, remoção de caracteres de moeda) e efetua o *casting* para ponto flutuante (`float`).

4. **`main.py` (Orchestrator)**  
   O orquestrador do pipeline. Suas responsabilidades são:
   - Ler o *payload* JSON.
   - Compilar as queries strings via `urllib.parse`.
   - Delegar os disparos assíncronos de HTTP para o `fetcher`.
   - Invocar o *parser* apropriado.
   - Processar a lógica de comparação para identificar o valor *Min*.
   - Acionar o *I/O* em disco gravando o `historico.json`.

---

## 🛠 Escalabilidade: Como implementar suporte a novas lojas

Devido ao desacoplamento, integrar um novo marketplace (ex: Kabum) exige apenas a implementação de sua interface de *parser*, sem necessidade de refatorar o núcleo de acesso ou modelos.

**Fluxo de integração:**

1. **Input**: Adicione a URL base no `produtos.json` (ex: `"url": "https://www.kabum.com.br"`).
2. **Rotas**: No módulo `crawler/main.py` -> `build_search_url()`, registre a lógica de *path* de busca do e-commerce (ex: `return f"{base_url}/busca?q={query}"`).
3. **Seletor CSS**: No módulo `crawler/parsers.py`, crie a função de extração especializada, informando o seletor correspondente ao *card* do produto (ex: `soup.select_one('.productCard .price')`).
