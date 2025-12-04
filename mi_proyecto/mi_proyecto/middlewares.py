# Repositorio: Inteligencia_app
# Archivo: mi_proyecto/mi_proyecto/pipelines.py
# Implementa la limpieza, geocodificación y guardado del Super Bot.

from scrapy.exceptions import DropItem
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import json
import logging
import hashlib # Para generar un ID estable
import os
from pathlib import Path

# --- RUTA DE SALIDA (MVP OFFLINE) ---
# Usamos el path relativo para guardar en 'output/' dentro de mi_proyecto
OUTPUT_DIR = Path(os.getcwd()) / 'output'


class DataCleaningPipeline(object):
    """
    Pipeline 1 (300): Limpieza, validación, generación de ID ÚNICO y estandarización inicial.
    """
    def process_item(self, item, spider):
        # 1. Validación de campos críticos
        if not item.get('marca_nombre') or not item.get('descuento_valor_bruto'):
            raise DropItem(f"Item incompleto descartado: {item.get('url_origen_segmento')}")

        # 2. Normalización de descuento_valor_bruto (Convertir "50% dto." a 0.50)
        descuento_str = item.get('descuento_valor_bruto', '').strip().replace('%', '').replace('dto.', '')
        try:
            # Asumimos que el descuento es un porcentaje
            descuento_float = float(descuento_str) / 100.0 if descuento_str else 0.0
            item['descuento_normalizado'] = round(descuento_float, 2)
        except ValueError:
            item['descuento_normalizado'] = 0.0
            logging.warning(f"Error normalizando descuento: '{descuento_str}'. Se estableció en 0.0.")

        # 3. Asignación de metadatos de gestión
        item['fecha_extraccion'] = datetime.now().isoformat()
        
        # 4. Generar ID ÚNICO ESTABLE (CRÍTICO: Usamos SHA-256 para deduplicación)
        unique_key = (
            item.get('url_origen_segmento', '') + 
            item.get('marca_nombre', '') + 
            item.get('descuento_valor_bruto', '')
        ).encode('utf-8')
        item['id_unico'] = hashlib.sha256(unique_key).hexdigest()
        
        return item


class GeocodingPipeline(object):
    """
    Pipeline 2 (400): Enriquecimiento del Item con Latitud/Longitud (CRÍTICO).
    """
    def __init__(self):
        # Inicializa el geocodificador Nominatim con User-Agent profesional
        self.geolocator = Nominatim(user_agent="super_bot_aggregator_cl")
        self.geocode_timeout = 5

    def process_item(self, item, spider):
        # 1. Validar si hay ubicación para geocodificar
        lugar = item.get('lugar_referencia')
        
        # Agregamos "Santiago, Chile" a la búsqueda para mejorar precisión
        search_query = f"{lugar}, Santiago, Chile" if lugar else None

        if not search_query or search_query == 'N/A, Santiago, Chile':
            item['latitud'] = None
            item['longitud'] = None
            return item
        
        # 2. Intentar la geocodificación
        try:
            # CRÍTICO: El geocodificador debe ser lento y cortes
            location = self.geolocator.geocode(search_query, timeout=self.geocode_timeout)
            
            if location:
                item['latitud'] = location.latitude
                item['longitud'] = location.longitude
            else:
                logging.warning(f"No se pudo geocodificar la ubicación: '{search_query}'.")
        
        except (GeocoderTimedOut, GeocoderServiceError):
            logging.error("FALLO: Timeout o Error en el servicio de geocodificación. Saltando item.")
            
        return item


class JsonWriterPipeline(object):
    """
    Pipeline 3 (800): Exporta el Item limpio y enriquecido al disco local (MVP).
    """
    def open_spider(self, spider):
        # Crea el archivo de salida (JSON Lines format)
        output_file_name = f'{spider.name}_output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
        self.file_path = OUTPUT_DIR / output_file_name
        
        # Asegura que la carpeta 'output' exista en la raíz del proyecto
        self.file_path.parent.mkdir(parents=True, exist_ok=True) 
        
        # Abre el archivo en modo escritura
        self.file = open(self.file_path, 'w', encoding='utf-8')
        spider.logger.info(f"El Output final se guardará en: {self.file_path}")

    def close_spider(self, spider):
        # Cierra el archivo de salida al finalizar el proceso
        if hasattr(self, 'file'):
            self.file.close()
            
    def process_item(self, item, spider):
        # Escribe cada Item como una línea JSON (JSON Lines format)
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
