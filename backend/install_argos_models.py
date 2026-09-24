# install_argos_models.py

from argostranslate import package
from argostranslate import translate

print("Actualizando índice...")

package.update_package_index()

packages = package.get_available_packages()


def instalar(origen, destino):

    pkg = next(

        (

            p

            for p in packages

            if p.from_code == origen
            and p.to_code == destino

        ),

        None

    )

    if pkg is None:

        raise RuntimeError(

            f"No existe el paquete Argos {origen}->{destino}."

        )

    print(f"Descargando {origen}->{destino}...")

    path = pkg.download()

    print(f"Instalando {origen}->{destino}...")

    package.install_from_path(path)


#
# Instalar ambos modelos
#

instalar("es", "en")

instalar("en", "es")


print("\nIdiomas instalados:\n")

translate.load_installed_languages()

for lang in translate.get_installed_languages():

    print(

        f"- {lang.code}"

    )


#
# Verificar ambos traductores
#

es_en = translate.get_translation_from_codes(

    "es",

    "en"

)

en_es = translate.get_translation_from_codes(

    "en",

    "es"

)

if es_en is None:

    raise RuntimeError(

        "La traducción es->en no quedó instalada."

    )

if en_es is None:

    raise RuntimeError(

        "La traducción en->es no quedó instalada."

    )

print("\nModelos Argos instalados correctamente.")
