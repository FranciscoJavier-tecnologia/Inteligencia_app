# -*- coding: utf-8 -*-

# Scrapy settings for mi_proyecto project
#
# Este archivo contiene la configuración de la Sala de Control para el Super Bot Aggregator CL.
# Se enfoca en el Stealth (Evasión), la Concurrencia y la activación de los Pipelines.

# ==============================================================================
# 1. CONFIGURACIÓN BÁSICA DEL PROYECTO
# ==============================================================================

BOT_NAME = 'super_bot_aggregator_cl'

SPIDER_MODULES = ['mi_proyecto.spiders']
NEWSPIDER_MODULE = 'mi_proyecto.spiders'

# Configuramos la zona horaria para el Item de fecha_extraccion (Chile)
TIMEZONE = 'America/Santiago'
FEED_EXPORT_ENCODING = 'utf-8'

# ==============================================================================
# 2. CONFIGURACIONES CRÍTICAS DE EXTRACCIÓN Y EVASIÓN (Stealth)
# ==============================================================================

# Desactivamos la obediencia al robots.txt (CRÍTICO para scraping profesional)
ROBOTSTXT_OBEY = False

# ELIMINAMOS EL USER_AGENT FIJO. Usaremos el middleware de rotación.
# USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Wi...' 

# Lista de User-Agents para el Middleware de rotación
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]


# **STRICT THROTLLING (CONFIGURACIÓN DE EVASIÓN):**
CONCURRENT_REQUESTS = 16 # Aumentamos para eficiencia general
CONCURRENT_REQUESTS_PER_DOMAIN = 1 # CRÍTICO: 1 petición concurrente POR DOMINIO (Máximo Stealth)

# Retraso entre peticiones para simular comportamiento humano (vital para evitar bloqueos)
DOWNLOAD_DELAY = 2.5 # Aumentamos de 1.5s a 2.5s para mayor cortesía.
RANDOMIZE_DOWNLOAD_DELAY = True # CRÍTICO: Añade un retardo aleatorio (Stealth)


# ==============================================================================
# 3. ACTIVACIÓN DE MIDDLEWARES DE ÉLITE (Soluciona el fallo de log)
# ==============================================================================

DOWNLOADER_MIDDLEWARES = {
    # 1. Desactivamos el User-Agent por defecto de Scrapy
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None, 
    # 2. Activamos nuestro Middleware de Rotación de Identidad (Stealth)
    'mi_proyecto.middlewares.RandomUserAgentMiddleware': 400, 
    # 3. CRÍTICO: Activamos la Evasión Dinámica para ver el JavaScript (Playwright)
    'mi_proyecto.middlewares.PlaywrightMiddleware': 500, 
}

# Deshabilitamos la consola Telnet
TELNETCONSOLE_ENABLED = False

# Deshabilitamos las cookies para simplificar la sesión
COOKIES_ENABLED = False


# ==============================================================================
# 4. ACTIVACIÓN DEL PIPELINE DE DATOS Y GEOFICACIÓN
# ==============================================================================

# Se definen los Pipelines que procesarán el Item.
# ORDEN CORREGIDO: Geocodificación debe ir DESPUÉS de la Normalización (Limpieza).
ITEM_PIPELINES = {
    # 1. Normalización y Limpieza (ej. "50% dto." -> 0.50 y generación de id_unico)
    'mi_proyecto.pipelines.DataCleaningPipeline': 300, 
    # 2. Geocodificación (Requiere el lugar_referencia limpio para funcionar)
    'mi_proyecto.pipelines.GeocodingPipeline': 400, 
    # 3. Guardado final del resultado limpio en el repositorio Datos_app
    'mi_proyecto.pipelines.JsonWriterPipeline': 800, 
}

# ==============================================================================
# 5. CONFIGURACIÓN DE LOGGING
# ==============================================================================

# Nivel de logging. Recomendado 'INFO' para ver progreso.
LOG_LEVEL = 'INFO'
