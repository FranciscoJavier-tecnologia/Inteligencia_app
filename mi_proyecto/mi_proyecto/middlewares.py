# Repositorio: Inteligencia_app
# Archivo: mi_proyecto/mi_proyecto/middlewares.py
# Implementa la Evasión Dinámica (Playwright) y la rotación de User-Agent (Stealth).

from scrapy.http import HtmlResponse, Request
from playwright.sync_api import sync_playwright
import random
import time
import logging
import os 
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
        # 1. Rotación de User-Agent: Selecciona una identidad aleatoria
        if USER_AGENT_LIST:
            selected_user_agent = random.choice(USER_AGENT_LIST)
            request.headers.setdefault('User-Agent', selected_user_agent)
            
        # 2. Inyección de Headers de Cortesía
        request.headers.setdefault('Accept-Language', 'es-CL,es;q=0.9')
        
        return None 
    
    def process_response(self, request, response, spider):
        """
        Maneja la respuesta: Si detectamos un código de bloqueo, reintentamos.
        """
        # Si la respuesta es un código de bloqueo (403 o 429)
        if response.status in [403, 429]:
            spider.logger.warning(f"BLOQUEO DETECTADO. STATUS: {response.status}. Reintentando con nueva identidad.")
            
            new_request = request.copy()
            new_request.dont_filter = True 
            
            # Aplicamos un retardo de reintento forzado (Stealth)
            time.sleep(random.uniform(5, 10)) 
            
            return new_request 
            
        return response


# ====================================================================
# MIDDLEWARE 2: PLAYWRIGHT (EVASIÓN DINÁMICA - Soluciona Cero Items)
# ====================================================================

class PlaywrightMiddleware:
    """
    Downloader Middleware que usa Playwright para renderizar la página dinámicamente.
    Soluciona el problema de "Cero Items" ejecutando JavaScript.
    """
    
    def process_request(self, request, spider):
        # CRÍTICO: Identificamos si la URL es de nuestro target (Banco de Chile)
        if 'bancochile.cl' in request.url:
            spider.logger.info(f"PLAYWRIGHT ACTIVO: Renderizando URL para JavaScript: {request.url}")
            
            # Usamos Playwright de forma síncrona
            with sync_playwright() as p:
                # Usamos Chromium sin interfaz gráfica (headless=True)
                browser = p.chromium.launch(headless=True) 
                
                # Contexto: Usamos el User-Agent ya definido por el RandomUserAgentMiddleware
                user_agent = request.headers.get('User-Agent').decode() if request.headers.get('User-Agent') else None
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()
                
                try:
                    page.goto(request.url, wait_until="domcontentloaded")
                    
                    # Espera Inteligente: Esperamos hasta que las tarjetas aparezcan (Soluciona Cero Items)
                    page.wait_for_selector("div.group-hover", timeout=5000) 
                    
                    # Simulación de Scroll para Lazy Loading
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000) # Espera un segundo extra
                    
                    html_content = page.content()
                    
                finally:
                    browser.close()
            
            # Devolvemos el HTML renderizado a Scrapy
            return HtmlResponse(
                url=request.url,
                body=html_content,
                encoding='utf-8',
                request=request
            )
        
        return None
