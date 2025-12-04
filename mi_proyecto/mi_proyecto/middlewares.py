# Repositorio: Inteligencia_app
# Archivo: mi_proyecto/mi_proyecto/middlewares.py
# Implementa la Evasión Dinámica (Playwright) y la rotación de User-Agent (Stealth).

from scrapy.http import HtmlResponse, Request
from playwright.async_api import async_playwright
from twisted.internet.defer import Deferred 
import random
import time
import logging
import asyncio
from scrapy.utils.project import get_project_settings 

# Intentamos importar la lista de User-Agents desde settings
try:
    settings = get_project_settings()
    USER_AGENT_LIST = settings.getlist('USER_AGENT_LIST')
except Exception:
    USER_AGENT_LIST = []

# ====================================================================
# MIDDLEWARE 1: RANDOM USER AGENT (STEALTH) 
# ====================================================================

class RandomUserAgentMiddleware:
    """
    Downloader Middleware que implementa el Stealth (Rotación de User-Agent) 
    y maneja reintentos por bloqueo (403/429).
    """
    
    def process_request(self, request, spider):
        if USER_AGENT_LIST:
            selected_user_agent = random.choice(USER_AGENT_LIST)
            request.headers.setdefault('User-Agent', selected_user_agent)
            
        request.headers.setdefault('Accept-Language', 'es-CL,es;q=0.9')
        return None 
    
    def process_response(self, request, response, spider):
        if response.status in [403, 429]:
            spider.logger.warning(f"BLOQUEO DETECTADO. STATUS: {response.status}. Reintentando con nueva identidad.")
            
            new_request = request.copy()
            new_request.dont_filter = True 
            time.sleep(random.uniform(5, 10)) 
            return new_request 
            
        return response


# ====================================================================
# MIDDLEWARE 2: PLAYWRIGHT ASÍNCRONO (SOLUCIÓN DEL ERROR CRÍTICO)
# ====================================================================

class PlaywrightMiddleware:
    """
    Downloader Middleware que usa Playwright de forma ASÍNCRONA.
    Resuelve el conflicto del asyncio loop.
    """
    def process_request(self, request, spider):
        # CRÍTICO: Solo se ejecuta para nuestro dominio objetivo.
        if 'bancochile.cl' in request.url:
            spider.logger.info(f"PLAYWRIGHT ACTIVO: Renderizando URL para JavaScript: {request.url}")
            
            # Devolvemos un Deferred para que Scrapy sepa que es una operación asíncrona.
            d = Deferred()
            d.addCallback(self._render_page, request, spider)
            return d
        
        return None

    async def _render_page(self, response, request, spider):
        """
        Función asíncrona que maneja la lógica de Playwright.
        """
        async with async_playwright() as p:
            # Usamos Chromium sin interfaz gráfica (headless=True)
            browser = await p.chromium.launch(headless=True) 
            
            user_agent = request.headers.get('User-Agent').decode() if request.headers.get('User-Agent') else None
            context = await browser.new_context(user_agent=user_agent)
            page = await context.new_page()
            
            try:
                await page.goto(request.url, wait_until="domcontentloaded")
                
                # Espera Inteligente: Esperamos a que las tarjetas aparezcan (selector de clase estable)
                await page.wait_for_selector("div.group-hover", timeout=5000) 
                
                # Simulación de Scroll para Lazy Loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000) 
                
                html_content = await page.content()
                
            finally:
                await browser.close()
        
        # Devolvemos el HTML renderizado (con las tarjetas cargadas)
        return HtmlResponse(
            url=request.url,
            body=html_content.encode('utf-8'), # Codificamos el cuerpo
            encoding='utf-8',
            request=request
        )
