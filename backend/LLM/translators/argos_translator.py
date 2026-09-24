# LLM/translators/argos_translator.py

from argostranslate import translate


METADATOS = {

    "DOCUMENTO:",
    "TIPO:",
    "SECCIÓN:",
    "SUBTÍTULO:",
    "PÁGINA:",
    "PALABRAS_CLAVE:",
    "TITULO_PADRE:",
    "TITULO_HIJO:",

}


NO_TRADUCIR = {

    "ANID",
    "FONDECYT",
    "FONDEF",
    "FONIS",
    "FONDAP",
    "BASAL",
    "INGENIERÍA 2030",
    "OBJETIVO_GENERAL",
    "OBJETIVOS",
    "POSTULANTES",
    "REQUISITOS",
    "FINANCIAMIENTO",
    "BENEFICIOS",
    "EVALUACION"

}


class ArgosTranslator:

    def __init__(self):

        self.es_en = translate.get_translation_from_codes(
            "es",
            "en"
        )

        self.en_es = translate.get_translation_from_codes(
            "en",
            "es"
        )

        if self.es_en is None:

            raise RuntimeError(
                "No se encontró el traductor Argos es->en."
            )

        if self.en_es is None:

            raise RuntimeError(
                "No se encontró el traductor Argos en->es."
            )

    def es_a_en(self, texto):

        return self._traducir(
            texto,
            self.es_en,
            "ES->EN"
        )

    def en_a_es(self, texto):

        return self._traducir(
            texto,
            self.en_es,
            "EN->ES"
        )

    def _traducir(

        self,

        texto,

        traductor,

        direccion

    ):

        if not texto:

            return ""

        print(f"\n[ARGOS {direccion} ENTRADA]\n")
        print(texto)

        resultado = []

        for linea in texto.splitlines():

            linea = linea.rstrip()

            if not linea:

                resultado.append("")
                continue

            #
            # No traducir metadata
            #

            if any(

                linea.startswith(campo)

                for campo in METADATOS

            ):

                resultado.append(linea)
                continue

            #
            # No traducir encabezados normalizados
            #

            if linea.strip() in NO_TRADUCIR:

                resultado.append(linea)
                continue

            resultado.append(

                traductor.translate(
                    linea
                )

            )

        texto_traducido = "\n".join(resultado)

        print(f"\n[ARGOS {direccion} SALIDA]\n")
        print(texto_traducido)

        return texto_traducido


translator = ArgosTranslator()
