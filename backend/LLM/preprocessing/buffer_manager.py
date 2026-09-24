# LLM/preprocessing/buffer_manager.py

from copy import deepcopy

from LLM.preprocessing.section_constants import GENERAL


class BufferManager:

    def __init__(self):

        self.buffer = ""

        self.metadata = None

        self.seccion = GENERAL

        self.subtitulo = None

        self.chunk_recien_abierto = False


    def abrir(

        self,

        metadata,

        seccion,

        encabezado=""

    ):

        self.buffer = ""

        self.metadata = deepcopy(metadata)

        print(

            "[BUFFER METADATA]",

            {

                "seccion": self.metadata.get("seccion"),

                "titulo_padre": self.metadata.get("titulo_padre"),

                "titulo_hijo": self.metadata.get("titulo_hijo"),

                "subtitulo": self.metadata.get("subtitulo")

            }

        )

        self.seccion = seccion

        self.subtitulo = metadata.get(
            "subtitulo"
        )

        if encabezado:

            self.buffer += encabezado
            self.buffer += "\n"

        self.chunk_recien_abierto = True


    def reiniciar(

        self,

        metadata,

        seccion,

        encabezado=""

    ):

        habia_contenido = self.tiene_contenido()

        if habia_contenido:

            print(

                "[REINICIANDO BUFFER]",

                {

                    "seccion": self.seccion,

                    "subtitulo": self.subtitulo,

                    "lineas": self.lineas(),

                    "palabras": self.palabras()

                }

            )

            print(
                self.buffer[:500]
            )

        self.abrir(

            metadata,

            seccion,

            encabezado

        )

        return habia_contenido


    def agregar_linea(

        self,

        linea

    ):

        self.buffer += linea.strip()

        self.buffer += "\n"

        self.chunk_recien_abierto = False


    def vaciar(self):

        self.buffer = ""

        self.chunk_recien_abierto = False


    def contenido(self):

        return self.buffer


    def palabras(self):

        return len(

            self.buffer.split()

        )


    def lineas(self):

        return len(

            self.buffer.splitlines()

        )


    def tiene_contenido(self):

        return bool(

            self.buffer.strip()

        )


    def tiene_texto_util(self):

        contenido = [

            linea.strip()

            for linea in self.buffer.splitlines()

            if linea.strip()

        ]

        return len(contenido) > 1


    def puede_guardarse(self):
        """
        Indica si el contenido actual puede convertirse
        en uno o más chunks.
        """

        return (

            self.metadata is not None

            and

            self.tiene_texto_util()

            and

            not self.chunk_recien_abierto

        )


    def esta_recien_abierto(self):

        return self.chunk_recien_abierto


    def guardar_si_corresponde(

        self,

        guardar_buffer

    ):

        if self.puede_guardarse():

            guardar_buffer()

        elif self.esta_recien_abierto():

            print(
                "[INFO] Chunk recién abierto."
            )

        else:

            print(
                "[INFO] Solo existe el encabezado."
            )

    def actualizar_pagina(self, metadata):

        if self.metadata is None:

            self.metadata = deepcopy(metadata)

            return

        for campo in (
            "source",
            "page",
            "page_label",
            "pagina",
            "total_pages",
        ):

            if campo in metadata:

                self.metadata[campo] = (
                    metadata[campo]
                )

        print(
            "[BUFFER CAMBIO PAGINA]",
            {
                "page": self.metadata.get("page"),
                "page_label": self.metadata.get("page_label"),
                "pagina": self.metadata.get("pagina"),
                "seccion": self.metadata.get("seccion"),
                "subtitulo": self.metadata.get("subtitulo")
            }
        )


    def metadata_actual(self):

        return self.metadata
