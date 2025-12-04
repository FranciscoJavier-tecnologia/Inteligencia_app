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

# Desactivamos la obediencia al robots.txt para acceder a todas las URLs (CRÍTICO para scraping)
ROBOTSTXT_OBEY = False

# User-Agent avanzado: Imitamos un navegador Chrome reciente para máxima evasión.
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# **STRICT THROTLLING (CONFIGURACIÓN DE EVASIÓN):**
# Concurrencia máxima general.
CONCURRENT_REQUESTS = 4
# Limita a 1 petición concurrente POR DOMINIO (Máximo Stealth para no saturar el servidor)
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Retraso entre peticiones para simular comportamiento humano (vital para evitar bloqueos)
DOWNLOAD_DELAY = 1.5 

# Deshabilitamos la consola Telnet
TELNETCONSOLE_ENABLED = False 

# ==============================================================================
# 3. ACTIVACIÓN DEL PIPELINE DE DATOS Y GEOFICACIÓN
# ==============================================================================

# Se definen los Pipelines que procesarán el Item (el Contrato de Datos BeneficioItem).
# La prioridad (número) determina el orden de ejecución (menor número = primero).
ITEM_PIPELINES = {
    # 1. Normalización y Limpieza de datos brutos (300)
    'mi_proyecto.pipelines.NormalizacionPipeline': 300, 
    # 2. Geocodificación: Enriquecimiento del Item con Latitud/Longitud (400)
    'mi_proyecto.pipelines.GeocodificacionPipeline': 400, 
    # 3. Guardado final del resultado limpio en el repositorio Datos_app (800)
    'mi_proyecto.pipelines.GuardadoFinalPipeline': 800, 
}

# ==============================================================================
# 4. CONFIGURACIÓN DEL DOWNLOADER MIDDLEWARE 
# ==============================================================================

DOWNLOADER_MIDDLEWARES = {
    # Aquí puedes añadir tu middleware de Stealth si usas una librería (ej. RandomUserAgent).
}

# ==============================================================================
# 5. CONFIGURACIÓN DE LOGGING
# ==============================================================================

# Nivel de logging. Recomendado 'INFO' para ver progreso o 'DEBUG' para detalles de requests/respuestas.
LOG_LEVEL = 'INFO' 
```eof
