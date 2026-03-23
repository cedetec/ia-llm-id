def asegurar_texto(x):
    """
    Convierte dict, list o cualquier cosa en string seguro.
    """
    if x is None:
        return ""

    if isinstance(x, str):
        return x

    if isinstance(x, dict):
        return x.get("contenido") or x.get("texto") or str(x)

    if isinstance(x, list):
        return " ".join(
            e.get("contenido", "") if isinstance(e, dict) else str(e)
            for e in x
        )

    return str(x)
