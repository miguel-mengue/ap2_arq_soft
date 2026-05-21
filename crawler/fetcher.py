import asyncio
import logging
from playwright.async_api import async_playwright

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});
"""

class CrawlerFetcher:
    """
    Classe responsável por baixar o HTML das páginas usando um navegador real (Playwright),
    evitando ser bloqueado por mecanismos "anti-bot".
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    async def start(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

    async def stop(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def fetch_html(self, url: str) -> str:
        if not self._browser:
            await self.start()
        
        ctx = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1366, "height": 768}
        )
        await ctx.add_init_script(STEALTH_INIT_SCRIPT)
        
        # Otimização: bloquear imagens e recursos que não afetam o preço para deixar mais rápido
        await ctx.route(
            "**/*",
            lambda route: route.abort() if route.request.resource_type in {"image", "media", "font", "stylesheet"} else route.continue_()
        )
        
        page = await ctx.new_page()
        try:
            log.info(f"Acessando URL: {url}")
            await page.goto(url, wait_until="load", timeout=60000)
            
            # Pequeno delay para garantir que scripts do site renderizem o preço
            await asyncio.sleep(4) 
            
            # Tenta pegar o conteúdo da página com resiliência a navegações em andamento (redirecionamentos)
            html = ""
            for attempt in range(3):
                try:
                    html = await page.content()
                    if html:
                        break
                except Exception as e:
                    if "navigating" in str(e).lower() or "navigation" in str(e).lower():
                        log.info(f"Navegação em andamento detectada (tentativa {attempt + 1}/3). Aguardando carregamento...")
                        try:
                            await page.wait_for_load_state("load", timeout=10000)
                        except Exception:
                            pass
                        await asyncio.sleep(2)
                    else:
                        raise e
            return html
        except Exception as e:
            log.error(f"Erro ao acessar {url}: {e}")
            return ""
        finally:
            await page.close()
            await ctx.close()
