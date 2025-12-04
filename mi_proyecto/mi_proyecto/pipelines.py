# -*- coding: utf-8 -*-

from scrapy.exceptions import DropItem
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from pathlib import Path
import os
import json
import logging

# Se definen las rutas para el Output
# Asume que Datos_app es un repositorio hermano de Inteligencia_app
DATOS_APP_PATH = Path(os.getcwd()).parents[3] / 'Datos_app' 
# NOTA: Usamos parents[3] porque estamos en /spiders/ y necesitamos subir 3 niveles: 
# /spiders/ -> /mi_proyecto/ -> /mi_proyecto/ -> /Inteligencia_app/ -> /CarpetaSuperior/

class NormalizacionPipeline(object):
    """
    Pipeline 1: Limpieza, validación y estandarización inicial de campos.
    """
    def process_item(self, item, spider):
        # 1. Validación de campos críticos de la Fase 1
        if not item.get('marca_nombre') or not item.get('descuento_valor_bruto'):
            raise DropItem(f"Item incompleto y descartado (Fase 1): {item.get('url_origen_segmento')}")

        # 2. Normalización de descuento_valor_bruto (Ejemplo simple)
        descuento_str = item.get('descuento_valor_bruto', '').strip().replace('%', '')
        try:
            item['descuento_normalizado'] = float(descuento_str) / 100.0 if descuento_str else 0.0
        except ValueError:
            item['descuento_normalizado'] = 0.0
            logging.warning(f"Error normalizando descuento: {descuento_str}")

        # 3. Asignación de metadatos de gestión
        # La fecha se obtiene del sistema (configurada con TIMEZONE en settings.py)
        item['fecha_extraccion'] = datetime.now().isoformat()
        
        # Generar un ID único (ej. hash de la URL de origen y la marca)
        item['id_unico'] = hash(item.get('url_origen_segmento') + item.get('marca_nombre'))
        
        return item


class GeocodificacionPipeline(object):
    """
    Pipeline 2: Toma la referencia de ubicación (lugar_referencia) y la convierte a Latitud/Longitud.
    """
    def __init__(self):
        # Inicializa el geocodificador Nominatim (servicio gratuito de OpenStreetMap)
        self.geolocator = Nominatim(user_agent="super_bot_aggregator_cl")
        self.geocode_timeout = 5 # Tiempo límite para la petición de geocodificación

    def process_item(self, item, spider):
        # 1. Validar si hay ubicación para geocodificar
        lugar = item.get('lugar_referencia')
        if not lugar or lugar == 'N/A':
            item['latitud'] = None
            item['longitud'] = None
            return item
        
        # 2. Intentar la geocodificación
        try:
            # Agregamos 'Chile' para enfocar la búsqueda y mejorar la precisión
            location = self.geolocator.geocode(f"{lugar}, Chile", timeout=self.geocode_timeout)
            
            if location:
                item['latitud'] = location.latitude
                item['longitud'] = location.longitude
                logging.debug(f"Geocodificación exitosa: {lugar} -> ({location.latitude}, {location.longitude})")
            else:
                item['latitud'] = None
                item['longitud'] = None
                logging.warning(f"No se pudo geocodificar la ubicación: {lugar}")
        
        except GeocoderTimedOut:
            logging.error("Timeout en el servicio de geocodificación.")
            # Se permite que el Item pase sin geocodificar
        except GeocoderServiceError as e:
            logging.error(f"Error en el servicio de geocodificación: {e}")
            # Se permite que el Item pase sin geocodificar
            
        return item


class GuardadoFinalPipeline(object):
    """
    Pipeline 3: Exporta el Item limpio y enriquecido al repositorio Datos_app.
    """
    def open_spider(self, spider):
        # Crea el archivo de salida al inicio del proceso de la araña
        self.file_path = DATOS_APP_PATH / 'output' / f'{spider.name}_output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
        self.file_path.parent.mkdir(parents=True, exist_ok=True) # Asegura que la carpeta output exista
        self.file = open(self.file_path, 'w', encoding='utf-8')
        logging.info(f"El Output se guardará en: {self.file_path}")

    def close_spider(self, spider):
        # Cierra el archivo de salida al finalizar el proceso
        self.file.close()
        
    def process_item(self, item, spider):
        # Escribe cada Item como una línea JSON (JSON Lines format)
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
```eof

---

### 🟢 Próximo Paso: Ejecución del MVP

¡Felicidades! Has completado la codificación de todos los componentes clave para tu Producto Mínimo Viable (MVP) del **Super Bot Aggregator CL**.

Tu motor `Inteligencia_app` ahora tiene:
1.  **Contrato de Datos (`items.py`)**
2.  **Cerebro de Extracción (`bancochile_spider.py`)** con lógica de Dos Fases.
3.  **Sala de Control (`settings.py`)** con Stealth y Pipelines activados.
4.  **Cerebros de Limpieza (`pipelines.py`)** con Normalización, Geocodificación y Guardado.

**El único paso pendiente es la instalación de la librería `geopy` y luego la ejecución del bot.**

¿Quieres que te recuerde el comando para ejecutar el bot y te prepare para la fase de pruebas?
