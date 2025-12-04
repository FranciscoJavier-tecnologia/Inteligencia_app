import scrapy
from pathlib import Path
import os
import logging

# Importamos el Contrato de Datos que definiste
from mi_proyecto.items import BeneficioItem

# --- CORRECCIÓN CRÍTICA DE RUTA PARA WINDOWS (USERPROFILE) ---
# Se utiliza la variable de entorno de Windows (C:\Users\PCXTEC05) para asegurar la ruta absoluta,
# ya que el cálculo relativo parents[] falló en este entorno.
USER_PROFILE = os.environ.get('USERPROFILE', Path.home()) 
FUENTES_APP_PATH = Path(USER_PROFILE) / 'Fuentes_app'
# -------------------------------------------------------------

FUENTES_BASE_URL = 'https://www.bancochile.cl/api/promociones' # URL base para la API o sitio

class BancoChileSpider(scrapy.Spider):
    """
    Araña para la Extracción de Dos Fases de promociones del Banco de Chile.
    Fase 1: Extrae la lista de promociones desde los archivos .txt.
    Fase 2: Sigue el link de detalle para enriquecer el Item con Ubicación y Vigencia.
    """
    name = 'bancochile_spider'
    # Agregamos tanto el dominio base como el subdominio www para mayor robustez en la navegación.
    allowed_domains = ['bancochile.cl', 'www.bancochile.cl'] 

    def start_requests(self):
        """
        Método inicial que lee las URLs de los archivos .txt y genera las peticiones.
        """
        logging.info("Iniciando requests: Leyendo archivos de Fuentes_app...")
        
        # 1. Definir la ruta de los archivos .txt usando la ruta absoluta corregida
        ruta_segmentos = FUENTES_APP_PATH / 'Bancos y Tarjetas' / 'banco_chile'
        
        if not ruta_segmentos.is_dir():
             # Este error ahora solo ocurrirá si Fuentes_app no existe en el directorio de usuario.
             logging.error(f"¡ERROR CRÍTICO! No se encontró la ruta: {ruta_segmentos}")
             return

        # 2. Iterar sobre cada archivo de segmento (ej. sabores.txt, viajes.txt)
        for archivo_segmento in ruta_segmentos.glob('*.txt'):
            segmento_nombre = archivo_segmento.stem  # Ej: 'sabores'
            
            try:
                with open(archivo_segmento, 'r', encoding='utf-8') as f:
                    urls = f.read().splitlines()
            except Exception as e:
                logging.error(f"Error al leer el archivo {archivo_segmento.name}: {e}")
                continue
            
            logging.info(f"Segmento '{segmento_nombre}': {len(urls)} URLs cargadas.")
            
            # 3. Generar una petición HTTP (Request) por cada URL cargada
            for url in urls:
                if url.strip():
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_list,  # Envía la respuesta a la Fase 1
                        meta={'segmento': segmento_nombre, 'url_origen_segmento': url} # Pasa metadatos
                    )


    def parse_list(self, response):
        """
        FASE 1: Extrae los datos visibles de la tarjeta y el link de detalle.
        """
        logging.info(f"FASE 1 (Lista): Procesando URL: {response.url}")
        
        # Selector de EJEMPLO: Recorrer cada tarjeta de promoción
        for tarjeta in response.css('div.promocion-card'): 
            item = BeneficioItem()
            
            # 1. Rellenar campos de la FASE 1 (SELECTORES DE EJEMPLO: DEBEN SER REEMPLAZADOS)
            item['marca_nombre'] = tarjeta.css('h2::text').get()
            item['descuento_valor_bruto'] = tarjeta.css('span.descuento::text').get()
            item['validez_corta_texto'] = tarjeta.css('p.vigencia-corta::text').get()
            
            # 2. Obtener el LINK DE DETALLE (¡CRÍTICO!)
            link_detalle = tarjeta.css('a.btn-detalle::attr(href)').get()
            
            # 3. Rellenar campos de Gestión (desde el meta)
            item['institucion_nombre'] = 'Banco de Chile'
            item['categoria_fuente'] = 'Promo General'
            item['segmento'] = response.meta.get('segmento')
            item['url_origen_segmento'] = response.meta.get('url_origen_segmento')
            
            # 4. Iniciar la Petición de la FASE 2
            if link_detalle:
                url_detalle = response.urljoin(link_detalle)
                yield scrapy.Request(
                    url=url_detalle,
                    callback=self.parse_detail, # Envía la respuesta a la Fase 2
                    meta={'item': item} # Pasa el Item parcialmente llenado
                )
            else:
                # Si no hay link de detalle, se envía el Item incompleto al Pipeline (para depuración)
                yield item

    def parse_detail(self, response):
        """
        FASE 2: Enriquecimiento del Item con la información oculta.
        """
        logging.info(f"FASE 2 (Detalle): Procesando URL: {response.url}")
        
        # Recuperar el Item que venía de la Fase 1
        item = response.meta['item'] 
        
        # 1. Rellenar campos de la FASE 2 (SELECTORES DE EJEMPLO: DEBEN SER REEMPLAZADOS)
        item['validez_larga_texto'] = response.css('div.vigencia-larga::text').get()
        item['lugar_referencia'] = response.css('span.direccion::text').get()
        item['link_canje_directo'] = response.css('a.btn-canje::attr(href)').get()
        
        # 2. Finalmente, se envía el Item completo al Pipeline (pipelines.py)
        yield item

