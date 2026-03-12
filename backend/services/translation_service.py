import argostranslate.package
import argostranslate.translate


def traducir(texto: str, from_code: str, to_code: str) -> str:
    if not texto:
        return texto

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == from_code), None)
    to_lang = next((l for l in installed_languages if l.code == to_code), None)

    if not from_lang or not to_lang:
        return texto  # fallback

    translation = from_lang.get_translation(to_lang)
    return translation.translate(texto)