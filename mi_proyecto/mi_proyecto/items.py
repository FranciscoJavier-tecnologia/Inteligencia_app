import scrapy
from scrapy.item import Field

class BeneficioItem(scrapy.Item):
    """
    Define el esquema de datos (Item) para el Super Bot.
    Optimizados para la Extracción de Dos Fases (Lista y Detalle).
    """
    # --- 1. DATOS BRUTOS DE LA PÁGINA DE LISTA (FASE 1) ---
    marca_nombre = Field()
    descuento_valor_bruto = Field()
    validez_corta_texto = Field()

    # --- 2. DATOS BRUTOS DE LA PÁGINA DE DETALLE (FASE 2) ---
    link_canje_directo = Field()
    validez_larga_texto = Field()
    lugar_referencia = Field()

    # --- 3. CAMPOS DE GESTIÓN Y METADATOS (INFERIDOS) ---
    institucion_nombre = Field()
    categoria_fuente = Field()
    segmento = Field()
    url_origen_segmento = Field()

    # --- 4. ACTIVOS DE NEGOCIO (GENERADOS POR EL PIPELINE) ---
    descuento_normalizado = Field()
    latitud = Field()
    longitud = Field()
    id_unico = Field()
    fecha_extraccion = Field()
