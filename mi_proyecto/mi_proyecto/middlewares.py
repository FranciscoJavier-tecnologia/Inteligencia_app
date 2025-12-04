# Repositorio: Inteligencia_app
# Archivo: mi_proyecto/mi_proyecto/middlewares.py
# Implementa la Evasión Dinámica (Playwright) y la rotación de User-Agent (Stealth).

from scrapy.http import HtmlResponse, Request
from playwright.sync_api import sync_playwright
import random
import time
from scrapy import signals
from itemadapter import ItemAdapter
import os 
import logging

# Importamos la lista de User-Agents desde settings
# Asumimos que esta lista existe en mi_proyecto/mi_proyecto/settings.py
try:
    from mi_proyecto.settings import USER_AGENT_LIST
except ImportError:
    USER_AGENT_LIST = []
    logging.warning("USER_AGENT_LIST no está definida. Usando lista vacía.")


class RandomUserAgentMiddleware:
    """
    Downloader Middleware que implementa el Stealth.
    Rota el User-Agent para cada solicitud y maneja reintentos por bloqueo.
    """
    
    def process_request(self, request, spider):
        # 1. Rotación de User-Agent: Selecciona una identidad aleatoria
        if USER_AGENT_LIST:
            selected_user_agent = random.choice(USER_AGENT_LIST)
            request.headers.setdefault('User-Agent', selected_user_agent)
            
        # 2. Inyección de Headers de Cortesía (Simulación de usuario chileno)
        request.headers.setdefault('Accept-Language', 'es-CL,es;q=0.9')
        
        return None 
    
    def process_response(self, request, response, spider):
        """
        Maneja la respuesta: Si detectamos un bloqueo (403 o 429), reintentamos.
        """
        # Si la respuesta es un código de bloqueo
        if response.status in [403, 429]:
            spider.logger.warning(f"BLOQUEO DETECTADO. STATUS: {response.status}. Reintentando con nueva identidad.")
            
            new_request = request.copy()
            new_request.dont_filter = True 
            
            # Aplicamos un retardo de reintento forzado (Stealth)
            time.sleep(random.uniform(5, 10)) 
            
            return new_request 
            
        return response


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
                    
                    # Espera Inteligente: Esperamos hasta que las tarjetas (div.group-hover) aparezcan
                    page.wait_for_selector("div.group-hover", timeout=5000) 
                    
                    # Simulación de Scroll para cargar contenido (Lazy Loading)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000) 
                    
                    html_content = page.content()
                    
                finally:
                    browser.close()
            
            # Devolvemos el HTML renderizado a Scrapy para que el Spider lo procese
            return HtmlResponse(
                url=request.url,
                body=html_content,
                encoding='utf-8',
                request=request
            )
        
        return None
