# LLM/rag/retrieval_pipeline.py

import logging

from RAG.reranker.category_classifier import (
    clasificar_categoria
)

from RAG.rag.document_filter import (
    filtrar_documentos
)

from RAG.rag.noise_filter import (
    filtrar_ruido
)

from RAG.reranker.rerank_service import (
    rerank_documentos
)

from RAG.validators.retrieval_validator import (
    validar_retriever
)

from RAG.rag.query_type_detector import (
    detectar_tipo_consulta,
    detectar_tipos_consulta
)

from RAG.rag.document_detector import (
    detectar_documento
)

logger = logging.getLogger(__name__)


class RetrievalPipeline:

    def __init__(
        self,
        retriever,
        top_k=4,
        max_candidatos=8,
        rerank_k=4
    ):

        self.retriever = retriever
        self.top_k = top_k
        self.max_candidatos = max_candidatos
        self.rerank_k = rerank_k


    def _recuperar_documentos(

        self,

        pregunta_busqueda,

        documento=None,

        documentos_relevantes=None,

        tipos_consulta=None

    ):

        documentos = []

        #
        # Cuando el benchmark conoce explícitamente
        # el documento objetivo, aplicar el filtro
        # directamente en Chroma.
        #

        if documentos_relevantes:

            logger.info(
                "[RETRIEVER] Filtro multidocumento: %s",
                documentos_relevantes
            )

            vectorstore = self.retriever.vectorstore

            search_kwargs = getattr(
                self.retriever,
                "search_kwargs",
                {}
            )

            k = search_kwargs.get(
                "k",
                30
            )

            documentos_por_fuente = {}

            vistos = set()

            for item in documentos_relevantes:

                nombre_documento = item[0]
                documentos_fuente = []
                anio_documento = item[1]

                logger.info(
                    "[RETRIEVER] Documento objetivo: %s | año=%s",
                    nombre_documento,
                    anio_documento
                )

                filtro = {
                    "documento": nombre_documento
                }

                consultas_por_tipo = {
                    "BENEFICIOS": (
                        "Beneficios y Plazos "
                        "monto máximo de financiamiento "
                        "tope de financiamiento "
                        "duración del proyecto "
                        "12 meses"
                    ),
                    "FINANCIAMIENTO": (
                        "Beneficios y Plazos "
                        "ANID financiará a proyectos con un tope "
                        "monto máximo de financiamiento "
                        "presupuesto"
                    ),
                }

                consultas_retrieval = []

                for tipo in tipos_consulta or []:

                    consulta_tipo = consultas_por_tipo.get(tipo)

                    if consulta_tipo:
                        consultas_retrieval.append(
                            consulta_tipo
                        )

                if not consultas_retrieval:

                    consultas_retrieval = [
                        pregunta_busqueda
                    ]


                mejores_documentos = {}


                for consulta in consultas_retrieval:

                    resultados = (
                        vectorstore.similarity_search_with_score(

                            consulta,

                            k=k,

                            filter=filtro

                        )
                    )

                    for doc, score in resultados:

                        clave = (
                            doc.metadata.get("documento"),
                            doc.metadata.get("pagina"),
                            doc.page_content
                        )

                        score = float(score)

                        score_anterior = (
                            mejores_documentos
                            .get(clave, (None, float("inf")))[1]
                        )

                        if score < score_anterior:

                            doc.metadata["retrieval_score"] = score

                            mejores_documentos[clave] = (
                                doc,
                                score
                            )


                documentos_fuente = [
                    doc
                    for doc, _ in mejores_documentos.values()
                ]

                documentos_por_fuente[nombre_documento] = documentos_fuente

            documentos = []

            fuentes = list(
                documentos_por_fuente.values()
            )

            #
            # Distribuir aproximadamente de forma
            # equilibrada, pero priorizando diversidad
            # de secciones dentro de cada fuente.
            #

            categorias_preferidas = []

            for tipo in tipos_consulta or []:

                if tipo == "OBJETIVO_GENERAL":

                    categorias_preferidas.extend(
                        [
                            "OBJETIVO_GENERAL",
                            "OBJETIVOS"
                        ]
                    )

                elif tipo == "REQUISITOS":

                    categorias_preferidas.append(
                        "REQUISITOS"
                    )

                elif tipo == "FINANCIAMIENTO":

                    categorias_preferidas.extend(
                        [
                            "BENEFICIOS",
                            "FINANCIAMIENTO"
                        ]
                    )

                elif tipo == "OBJETIVOS_ESPECIFICOS":

                    categorias_preferidas.extend(
                        [
                            "OBJETIVOS_ESPECIFICOS",
                            "OBJETIVOS"
                        ]
                    )

                elif tipo == "BENEFICIOS":

                    categorias_preferidas.append(
                        "BENEFICIOS"
                    )

                elif tipo == "POSTULANTES":

                    categorias_preferidas.append(
                        "POSTULANTES"
                    )

                elif tipo == "EVALUACION":

                    categorias_preferidas.append(
                        "EVALUACION"
                    )

            categorias_preferidas = list(
                dict.fromkeys(
                    categorias_preferidas
                )
            )

            posiciones_fuente = []

            for docs_fuente in fuentes:

                seleccion_fuente = []
                claves_fuente = set()
                categorias_fuente = set()

                #
                # Primera pasada:
                # una categoría distinta por cada candidato.
                #

                for categoria in categorias_preferidas:

                    for doc in docs_fuente:

                        clave = (
                            doc.metadata.get("documento"),
                            doc.metadata.get("pagina"),
                            doc.page_content
                        )

                        if clave in claves_fuente:
                            continue

                        seccion = (
                            doc.metadata.get(
                                "seccion",
                                ""
                            )
                            .upper()
                        )

                        texto_doc = (
                            f"{doc.metadata.get('encabezado_original', '')} "
                            f"{doc.page_content}"
                        ).upper()

                        if categoria == "BENEFICIOS":

                            es_beneficios = (
                                "BENEFICIOS Y PLAZOS" in texto_doc
                                or seccion == "BENEFICIOS"
                            )

                            if not es_beneficios:
                                continue

                        elif seccion != categoria:

                            continue

                        seleccion_fuente.append(doc)
                        claves_fuente.add(clave)
                        categorias_fuente.add(seccion)

                        break

                #
                # Segunda pasada:
                # completar con los mejores resultados restantes.
                #

                for doc in docs_fuente:

                    if len(
                        seleccion_fuente
                    ) >= 3:

                        break

                    clave = (
                        doc.metadata.get("documento"),
                        doc.metadata.get("pagina"),
                        doc.page_content
                    )

                    if clave in claves_fuente:
                        continue

                    seleccion_fuente.append(doc)
                    claves_fuente.add(clave)

                posiciones_fuente.append(
                    seleccion_fuente
                )

            #
            # Reparto round-robin entre fuentes.
            #

            indices = [
                0
                for _ in posiciones_fuente
            ]

            while (
                len(documentos)
                < self.max_candidatos
            ):

                agregados = 0

                for indice, docs_fuente in enumerate(
                    posiciones_fuente
                ):

                    if len(documentos) >= self.max_candidatos:
                        break

                    posicion = indices[indice]

                    if posicion >= len(docs_fuente):
                        continue

                    documentos.append(
                        docs_fuente[posicion]
                    )

                    indices[indice] += 1
                    agregados += 1

                if agregados == 0:
                    break

        elif documento:

            logger.info(
                "[RETRIEVER] Filtro por documento: %s",
                documento
            )

            vectorstore = self.retriever.vectorstore

            search_kwargs = getattr(
                self.retriever,
                "search_kwargs",
                {}
            )

            k = search_kwargs.get(
                "k",
                30
            )

            resultados = vectorstore.similarity_search_with_score(

                pregunta_busqueda,

                k=k,

                filter={
                    "documento": documento
                }

            )

            documentos = []

            for doc, score in resultados:

                doc.metadata["retrieval_score"] = float(score)

                documentos.append(doc)

        else:

            #
            # Comportamiento normal de /chat:
            # buscar en toda la colección.
            #

            documentos = self.retriever.invoke(
                pregunta_busqueda
            )

        logger.info(
            "Retriever recuperó %s documentos.",
            len(documentos)
        )

        for i, doc in enumerate(documentos):

            logger.info(
                "[%02d] %s | página=%s | sección=%s",
                i + 1,
                doc.metadata.get("documento"),
                doc.metadata.get("pagina"),
                doc.metadata.get("seccion")
            )

        return documentos


    def _filtrar_documentos(

        self,

        documentos,

        pregunta_original

    ):

        documentos = filtrar_documentos(

            documentos,

            pregunta_original

        )

        documentos = filtrar_ruido(
            documentos
        )

        validar_retriever(
            "FILTRO",
            pregunta_original,
            documentos
        )

        return documentos[:self.max_candidatos]


    def _rerank(
        self,
        documentos,
        pregunta_original,
        tipo_consulta,
        documento_pregunta,
        anio_pregunta,
        metricas,
        documentos_relevantes=None,
        tipos_consulta=None
    ):

        top_k_rerank = (
            self.max_candidatos
            if documentos_relevantes
            else self.rerank_k
        )

        return rerank_documentos(

            pregunta=pregunta_original,

            documentos=documentos,

            tipo_consulta=tipo_consulta,

            documento_pregunta=documento_pregunta,

            anio_pregunta=anio_pregunta,

            top_k=top_k_rerank,

            metricas=metricas,

            tipos_consulta=tipos_consulta,

        )


    def _registrar_metricas(

        self,

        metricas,

        recuperados,

        finales

    ):

        if metricas is None:
            return

        metricas.retrieval.registrar(

            documentos_recuperados=recuperados,

            documentos_finales=finales

        )


    def _generar_logs(

        self,

        documentos,

        titulo

    ):

        logger.info("========== %s ==========", titulo)

        for i, doc in enumerate(documentos):

            logger.info(

                "[%s]",

                i + 1

            )

            logger.info(
                "Documento: %s",
                doc.metadata.get("documento")
            )

            logger.info(
                "Página: %s",
                doc.metadata.get("pagina")
            )

            logger.info(
                "Sección: %s",
                doc.metadata.get("seccion")
            )

            logger.info(
                "Encabezado: %s",
                doc.metadata.get("encabezado_original")
            )

            logger.info(
                doc.page_content[:400]
            )


    def recuperar(

        self,

        pregunta_busqueda,

        pregunta_original,

        metricas=None,

        documento=None,

        documentos_relevantes=None

    ):

        tipos_consulta = detectar_tipos_consulta(
            pregunta_original
        )

        documentos = self._recuperar_documentos(

            pregunta_busqueda,

            documento=documento,

            documentos_relevantes=documentos_relevantes,

            tipos_consulta=tipos_consulta

        )

        documentos_recuperados = list(
            documentos
        )

        self._generar_logs(

            documentos,

            "DOCUMENTOS RECUPERADOS"

        )

        validar_retriever(

            "RETRIEVER",

            pregunta_busqueda,

            documentos

        )

        tipo_consulta = detectar_tipo_consulta(

            pregunta_original

        )

        info = detectar_documento(
            pregunta_original
        )

        if documentos_relevantes:

            documento_rerank = None

            anio_rerank = None

        else:

            documento_rerank = (
                documento
                if documento
                else info["documento"]
            )

            anio_rerank = info["anio"]

        if documentos_relevantes:

            documentos = filtrar_ruido(
                documentos
            )

            validar_retriever(
                "FILTRO MULTIDOCUMENTO",
                pregunta_original,
                documentos
            )

            documentos = documentos[:self.max_candidatos]

        else:

            documentos = self._filtrar_documentos(
                documentos,
                pregunta_original
            )

        self._registrar_metricas(

            metricas,

            documentos_recuperados,

            documentos

        )

        ranking = self._rerank(

            documentos,

            pregunta_original,

            tipo_consulta,

            documento_rerank,

            anio_rerank,

            metricas,

            documentos_relevantes=documentos_relevantes,

            tipos_consulta=tipos_consulta

        )

        for resultado in ranking:

            resultado.documento.metadata["rerank_score"] = float(
                resultado.score_final
            )

        if documentos_relevantes:

            if (
                documentos_relevantes
                and {"BENEFICIOS", "FINANCIAMIENTO"}.issubset(
                    set(tipos_consulta or [])
                )
            ):
                # En consultas comparativas de financiamiento,
                # dejamos espacio para evidencia que puede aparecer
                # después de los primeros candidatos del ranking.
                top_k_final = min(
                    self.max_candidatos,
                    max(
                        self.top_k,
                        len(tipos_consulta or []) + len(documentos_relevantes) + 2
                    )
                )
            else:
                top_k_final = min(
                    self.max_candidatos,
                    max(
                        self.top_k,
                        len(tipos_consulta or []) + len(documentos_relevantes)
                    )
                )

            documentos_seleccionados = []
            claves_seleccionadas = set()
            categorias_cubiertas = set()

            #
            # 1. Garantizar al menos un fragmento
            #    por cada documento solicitado.
            #

            for item in documentos_relevantes:

                nombre_documento = item[0]

                for resultado in ranking:

                    doc = resultado.documento

                    if (
                        doc.metadata.get("documento")
                        != nombre_documento
                    ):
                        continue

                    clave = (
                        doc.metadata.get("documento"),
                        doc.metadata.get("pagina"),
                        doc.page_content
                    )

                    if clave in claves_seleccionadas:
                        continue

                    doc.metadata["rerank_score"] = float(
                        resultado.score_final
                    )

                    documentos_seleccionados.append(
                        doc
                    )

                    claves_seleccionadas.add(
                        clave
                    )

                    categoria = clasificar_categoria(
                        doc
                    )["categoria"]

                    categorias_cubiertas.add(
                        categoria
                    )

                    break

            #
            # 2. Completar priorizando intenciones
            #    que todavía no estén cubiertas.
            #

            tipos_objetivo = list(
                tipos_consulta or []
            )

            intenciones_cubiertas = set()

            for categoria in categorias_cubiertas:

                if categoria in (
                    "OBJETIVO_GENERAL",
                    "OBJETIVOS"
                ):

                    intenciones_cubiertas.add(
                        "OBJETIVO_GENERAL"
                    )

                elif categoria == "REQUISITOS":

                    intenciones_cubiertas.add(
                        "REQUISITOS"
                    )

                elif categoria in (
                    "FINANCIAMIENTO",
                    "BENEFICIOS"
                ):

                    intenciones_cubiertas.add(
                        "FINANCIAMIENTO"
                    )

            for tipo in tipos_objetivo:

                if len(documentos_seleccionados) >= top_k_final:
                    break

                if tipo in intenciones_cubiertas:
                    continue

                mejor_resultado = None
                mejor_categoria = None

                for resultado in ranking:

                    doc = resultado.documento

                    clave = (
                        doc.metadata.get("documento"),
                        doc.metadata.get("pagina"),
                        doc.page_content
                    )

                    if clave in claves_seleccionadas:
                        continue

                    categoria = clasificar_categoria(
                        doc
                    )["categoria"]

                    coincide = False

                    if (
                        tipo == "OBJETIVO_GENERAL"
                        and categoria in (
                            "OBJETIVO_GENERAL",
                            "OBJETIVOS"
                        )
                    ):

                        coincide = True

                    elif (
                        tipo == "REQUISITOS"
                        and categoria == "REQUISITOS"
                    ):

                        coincide = True

                    elif (
                        tipo == "FINANCIAMIENTO"
                        and categoria in (
                            "FINANCIAMIENTO",
                            "BENEFICIOS"
                        )
                    ):

                        coincide = True

                    if not coincide:
                        continue

                    if (
                        mejor_resultado is None
                        or resultado.score_final
                        > mejor_resultado.score_final
                    ):

                        mejor_resultado = resultado
                        mejor_categoria = categoria

                if mejor_resultado is None:
                    continue

                doc = mejor_resultado.documento

                clave = (
                    doc.metadata.get("documento"),
                    doc.metadata.get("pagina"),
                    doc.page_content
                )

                doc.metadata["rerank_score"] = float(
                    mejor_resultado.score_final
                )

                documentos_seleccionados.append(
                    doc
                )

                claves_seleccionadas.add(
                    clave
                )

                categorias_cubiertas.add(
                    mejor_categoria
                )

                intenciones_cubiertas.add(
                    tipo
                )

            #
            # 3. Si todavía quedan espacios,
            #    completar con los mejores scores.
            #

            for resultado in ranking:

                if len(documentos_seleccionados) >= top_k_final:
                    break

                doc = resultado.documento

                clave = (
                    doc.metadata.get("documento"),
                    doc.metadata.get("pagina"),
                    doc.page_content
                )

                if clave in claves_seleccionadas:
                    continue

                doc.metadata["rerank_score"] = float(
                    resultado.score_final
                )

                documentos_seleccionados.append(
                    doc
                )

                claves_seleccionadas.add(
                    clave
                )

            documentos = documentos_seleccionados[
                :top_k_final
            ]

        else:

            documentos = []

            for r in ranking[:self.top_k]:

                doc = r.documento

                doc.metadata["rerank_score"] = float(
                    r.score_final
                )

                documentos.append(
                    doc
                )

        self._generar_logs(

            documentos,

            "DOCUMENTOS FINALES"

        )

        validar_retriever(

            "TOP FINAL",

            pregunta_original,

            documentos

        )

        return documentos
