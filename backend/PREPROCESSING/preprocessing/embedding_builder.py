# LLM/preprocessing/embedding_builder.py

def construir_texto_embedding(documento, tipo, titulo_padre, titulo_hijo, subtitulo, encabezado_original, seccion, pagina, palabras_clave, contenido):
    
    # Solo recopilamos metadatos que tengan información útil (que no estén vacíos o sean 'None')
    metadatos = []
    if documento: metadatos.append(f"Documento: {documento}")
    if tipo: metadatos.append(f"Tipo: {tipo}")
    if seccion: metadatos.append(f"Sección: {seccion}")
    if pagina: metadatos.append(f"Página: {pagina}")
    
    # Creamos un encabezado limpio y compacto
    cabecera = " | ".join(metadatos)
    
    # Retornamos todo de manera limpia
    return f"[{cabecera}]\n\n{contenido}".strip()