import scrapy
from pathlib import Path
import os
import logging
# CRÍTICO: Importamos PlaywrightRequest para activar la ejecución de JavaScript
from scrapy_playwright.page_pool import PlaywrightRequest 

# Importamos el Contrato de Datos
from mi_proyecto.items import BeneficioItem

# --- CONFIGURACIÓN DE RUTA ABSOLUTA PARA FUENTES_APP ---
# Usa la variable de entorno de usuario (ej. C:\Users\nombre_usuario)
USER_PROFILE = os.environ.get('USERPROFILE', Path.home()) 
FUENTES_APP_PATH = Path(USER_PROFILE) / 'Fuentes_app'
# -----------------------------------------------------

class BancoChileSpider(scrapy.Spider):
    """
    Araña de Extracción de Dos Fases para el Banco de Chile.
    CORRECCIÓN: Usa PlaywrightRequest para el contenido dinámico (JavaScript).
    """
    name = 'bancochile_spider'
    # Agregamos los dominios permitidos para Scrapy
    allowed_domains = ['bancochile.cl', 'www.bancochile.cl'] 

    def start_requests(self):
        """
        Lee las URLs de los archivos .txt de forma recursiva y genera peticiones PlaywrightRequest.
        """
        logging.info("Iniciando requests: Leyendo archivos de Fuentes_app...")
        
        # Define la ruta específica a la materia prima
        ruta_segmentos = FUENTES_APP_PATH / 'Bancos y Tarjetas' / 'banco_chile'
        
        if not ruta_segmentos.is_dir():
             logging.error(f"¡ERROR CRÍTICO! No se encontró la ruta: {ruta_segmentos}")
             return

        # Itera sobre cada archivo .txt en el directorio
        for archivo_segmento in ruta_segmentos.glob('*.txt'):
            segmento_nombre = archivo_segmento.stem  # Extrae el nombre del segmento (ej: 'sabores')
            
            try:
                with open(archivo_segmento, 'r', encoding='utf-8') as f:
                    urls = f.read().splitlines()
            except Exception as e:
                logging.error(f"Error al leer el archivo {archivo_segmento.name}: {e}")
                continue
            
            logging.info(f"Segmento '{segmento_nombre}': {len(urls)} URLs cargadas.")
            
            # Genera PlaywrightRequest para la Fase 1
            for url in urls:
                if url.strip():
                    # --- CORRECCIÓN C1: Usa PlaywrightRequest en Fase 1 ---
                    yield PlaywrightRequest(
                        url=url,
                        callback=self.parse_list,  # Envía la respuesta al método de la Fase 1
                        meta={'segmento': segmento_nombre, 'url_origen_segmento': url} # Pasa metadatos
                    )


    def parse_list(self, response):
        """
        FASE 1: Procesa la lista de promociones y genera la petición para la Fase 2 (Detalle).
        """
        logging.info(f"FASE 1 (Lista): Procesando URL: {response.url}")
        
        # RIESGO R1: Selector placeholder. Debe ser validado.
        for tarjeta in response.css('div.promocion-card'): 
            item = BeneficioItem()
            
            # 1. Rellenar campos de la FASE 1 (SELECTORES DE EJEMPLO: DEBEN SER REEMPLAZADOS)
            item['marca_nombre'] = tarjeta.css('h2::text').get()
            item['descuento_valor_bruto'] = tarjeta.css('span.descuento::text').get()
            item['validez_corta_texto'] = tarjeta.css('p.vigencia-corta::text').get()
            
            # 2. Obtener el LINK DE DETALLE (¡CRÍTICO!)
            link_detalle = tarjeta.css('a.btn-detalle::attr(href)').get()
            
            # 3. Rellenar campos de Gestión (metadatos)
            item['institucion_nombre'] = 'Banco de Chile'
            item['categoria_fuente'] = 'Promo General'
            item['segmento'] = response.meta.get('segmento')
            item['url_origen_segmento'] = response.meta.get('url_origen_segmento')
            
            # 4. Iniciar la Petición de la FASE 2
            if link_detalle:
                url_detalle = response.urljoin(link_detalle)
                # MEJORA M1: Guarda la URL en el Item para trazabilidad
                item['link_canje_directo'] = url_detalle 
                
                # --- CORRECCIÓN C2: Usa PlaywrightRequest en Fase 2 ---
                yield PlaywrightRequest(
                    url=url_detalle,
                    callback=self.parse_detail, # Envía la respuesta al método de la Fase 2
                    meta={'item': item} # Pasa el Item parcialmente llenado al siguiente callback
                )
            else:
                # Si no hay link de detalle, envía el Item incompleto al Pipeline (para guardado o descarte)
                yield item

    def parse_detail(self, response):
        """
        FASE 2: Enriquecimiento del Item con la información oculta.
        """
        logging.info(f"FASE 2 (Detalle): Procesando URL: {response.url}")
        
        # Recupera el Item que venía de la Fase 1
        item = response.meta['item'] 
        
        # 1. Rellenar campos de la FASE 2 (SELECTORES DE EJEMPLO: DEBEN SER REEMPLAZADOS - RIESGO R2)
        item['validez_larga_texto'] = response.css('div.vigencia-larga::text').get()
        item['lugar_referencia'] = response.css('span.direccion::text').get()
        
        # Opcional: Sobreescribe el link_canje_directo si la página de detalle tiene un link más directo
        link_canje = response.css('a.btn-canje::attr(href)').get()
        if link_canje:
            item['link_canje_directo'] = response.urljoin(link_canje)
        
        # 2. Finalmente, se envía el Item completo al Pipeline (pipelines.py)
        yield item
