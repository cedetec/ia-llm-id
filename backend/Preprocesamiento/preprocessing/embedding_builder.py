# LLM/preprocessing/embedding_builder.py

def construir_texto_embedding(

    documento,

    tipo,

    titulo_padre,

    titulo_hijo,

    subtitulo,

    encabezado_original,

    seccion,

    pagina,

    palabras_clave,

    contenido

):

    """
    Construye el texto enriquecido que será indexado
    en la base vectorial.
    """

    return f"""
DOCUMENTO:
{documento}

TIPO:
{tipo}

TÍTULO PADRE:
{titulo_padre}

TÍTULO HIJO:
{titulo_hijo}

SUBTÍTULO:
{subtitulo}

ENCABEZADO:
{encabezado_original}

SECCIÓN:
{seccion}

PÁGINA:
{pagina}

PALABRAS CLAVE:
{palabras_clave}

CONTENIDO:

{contenido}
""".strip()