# backend/LLM/evaluation/ragas_metrics.py

import copy
import time

from ragas.run_config import RunConfig

from ragas import evaluate

from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    Faithfulness
)

from ragas.metrics._faithfulness import (
    NLIStatementOutput,
    StatementGeneratorPrompt,
    NLIStatementPrompt,
    StatementGeneratorOutput
)

from ragas.exceptions import (
    RagasOutputParserException
)

from datasets import Dataset

from langchain_ollama import (
    ChatOllama,
    OllamaEmbeddings
)

from ragas.llms import (
    LangchainLLMWrapper
)

from ragas.metrics._context_recall import (
    ContextRecallClassificationPrompt,
    ContextRecallClassifications
)

from ragas.metrics._context_precision import (
    ContextPrecisionPrompt,
    Verification
)


class BatchedFaithfulness(Faithfulness):

    def __init__(
        self,
        statement_llm,
        verdict_llm,
        run_config,
        verdict_batch_size=6,
        **kwargs
    ):
        super().__init__(
            llm=statement_llm,
            **kwargs
        )

        self.statement_llm = statement_llm
        self.verdict_llm = verdict_llm
        self.run_config = run_config
        self.verdict_batch_size = verdict_batch_size

        self.statement_prompt = (
            StatementGeneratorPrompt()
        )

        self.statement_prompt.examples = []

        self.statement_prompt.instruction = (
            "Given a question and an answer, "
            "break the answer into concise, "
            "fully understandable factual statements. "
            "Do not use pronouns. "
            "Return only valid JSON matching the required schema."
        )

        self.verdict_prompt = (
            NLIStatementPrompt()
        )

        self.verdict_prompt.examples = []

        self.verdict_prompt.instruction = (
            "Judge the faithfulness of each statement "
            "based on the provided context. "
            "Return verdict=1 when the statement can be "
            "directly inferred from the context and verdict=0 otherwise. "
            "Return only valid JSON matching the required schema."
        )

    async def _create_statements(
        self,
        row,
        callbacks
    ):

        text = row["response"]
        question = row["user_input"]

        from ragas.metrics._faithfulness import (
            StatementGeneratorInput
        )

        prompt_input = StatementGeneratorInput(
            question=question,
            answer=text
        )

        return await self.statement_prompt.generate(
            llm=self.statement_llm,
            data=prompt_input,
            callbacks=callbacks
        )

    def _crear_llm_veredictos(
        self,
        cantidad: int
    ):
        schema = copy.deepcopy(
            NLIStatementOutput.model_json_schema()
        )

        schema["properties"]["statements"][
            "minItems"
        ] = cantidad

        schema["properties"]["statements"][
            "maxItems"
        ] = cantidad

        llm = ChatOllama(
            model="gemma4:e2b",
            base_url="http://ollama:11434",
            temperature=0.0,
            num_ctx=4096,
            num_predict=1024,
            reasoning=False,
            format=schema
        )

        return LangchainLLMWrapper(
            llm,
            run_config=self.run_config
        )

    async def _create_verdicts(
        self,
        row,
        statements,
        callbacks
    ):

        from ragas.metrics._faithfulness import (
            NLIStatementInput
        )

        todos_los_veredictos = []

        for inicio in range(
            0,
            len(statements),
            self.verdict_batch_size
        ):

            lote = statements[
                inicio:
                inicio + self.verdict_batch_size
            ]

            print(
                f"[FAITHFULNESS] "
                f"Veredictos "
                f"{inicio + 1}-"
                f"{inicio + len(lote)} "
                f"de {len(statements)}"
            )

            contexts_str = "\n".join(
                row["retrieved_contexts"]
            )

            verdict_llm = (
                self._crear_llm_veredictos(
                    len(lote)
                )
            )

            resultado = (
                await self.verdict_prompt.generate(
                    llm=verdict_llm,
                    data=NLIStatementInput(
                        context=contexts_str,
                        statements=lote
                    ),
                    callbacks=callbacks
                )
            )

            if len(resultado.statements) != len(lote):
                raise ValueError(
                    "Faithfulness devolvió "
                    f"{len(resultado.statements)} "
                    "veredictos para "
                    f"{len(lote)} afirmaciones."
                )

            todos_los_veredictos.extend(
                resultado.statements
            )

        return NLIStatementOutput(
            statements=todos_los_veredictos
        )


class RagasMetrics:

    def __init__(self):

        #
        # LLM juez de RAGAS.
        #
        # Se mantiene fijo para que todas las
        # evaluaciones sean comparables.
        #

        self.llm = ChatOllama(
            model="gemma4:e2b",
            base_url="http://ollama:11434",
            temperature=0,
            num_ctx=4096,
            num_predict=512,
            reasoning=False
        )

        self.context_recall_llm = ChatOllama(
            model="mistral:latest",
            base_url="http://ollama:11434",
            temperature=0.0,
            num_ctx=4096,
            num_predict=1024,
            reasoning=False,
            format=ContextRecallClassifications.model_json_schema()
        )

        self.context_precision_llm = ChatOllama(
            model="gemma4:e2b",
            base_url="http://ollama:11434",
            temperature=0.0,
            num_ctx=4096,
            num_predict=256,
            reasoning=False,
            format=Verification.model_json_schema()
        )

        self.context_precision_prompt = (
            ContextPrecisionPrompt()
        )

        self.context_precision_prompt.examples = []

        self.context_precision_prompt.instruction = (
            "Given the question, answer, and context, "
            "determine whether the context is useful for "
            "arriving at the answer. "
            "Return verdict=1 if useful and verdict=0 otherwise. "
            "Return only valid JSON matching the required schema."
        )

        self.context_recall_prompt = (
            ContextRecallClassificationPrompt()
        )

        self.context_recall_prompt.examples = []

        self.context_recall_prompt.instruction = (
            "Given the question, context, and reference answer, "
            "analyze each factual statement in the reference answer "
            "and classify whether it is supported by the context. "
            "Use attributed=1 when supported and attributed=0 when not. "
            "Return only valid JSON matching the required schema."
        )

        #
        # LLM específico para Faithfulness.
        #
        # Se utiliza un límite mayor porque la generación
        # de afirmaciones requiere más tokens.
        #

        self.llm_faithfulness_statements = ChatOllama(
            model="gemma4:e2b",
            base_url="http://ollama:11434",
            temperature=0.0,
            num_ctx=4096,
            num_predict=2048,
            reasoning=False,
            format=StatementGeneratorOutput.model_json_schema()
        )

        self.llm_faithfulness_verdicts = ChatOllama(
            model="gemma4:e2b",
            base_url="http://ollama:11434",
            temperature=0.0,
            num_ctx=4096,
            num_predict=1024,
            reasoning=False,
            format=NLIStatementOutput.model_json_schema()
        )

        #
        # Embeddings utilizados por las métricas
        # que requieren comparación semántica.
        #

        self.embeddings = OllamaEmbeddings(

            model="embeddinggemma",
            base_url="http://ollama:11434"

        )

        self.run_config = RunConfig(
            timeout=900,
            max_retries=1,
            max_wait=5,
            max_workers=1
        )

        #
        # Wrapper utilizado por RAGAS para adaptar
        # ChatOllama a BaseRagasLLM.
        #

        self.wrapped_llm_faithfulness_statements = (
            LangchainLLMWrapper(
                self.llm_faithfulness_statements,
                run_config=self.run_config
            )
        )

        self.wrapped_llm_faithfulness_verdicts = (
            LangchainLLMWrapper(
                self.llm_faithfulness_verdicts,
                run_config=self.run_config
            )
        )

        #
        # Faithfulness modificada para procesar
        # los veredictos en lotes de 6.
        #

        self.faithfulness_batched = BatchedFaithfulness(
            statement_llm=(
                self.wrapped_llm_faithfulness_statements
            ),
            verdict_llm=(
                self.wrapped_llm_faithfulness_verdicts
            ),
            run_config=self.run_config,
            verdict_batch_size=3,
            max_retries=1
        )

    def evaluar(

        self,

        pregunta: str,

        respuesta: str,

        contextos: list[str],

        referencia: str

    ):

        #
        # Dataset de una sola evaluación.
        #

        dataset = Dataset.from_dict(

            {

                "question": [
                    pregunta
                ],

                "answer": [
                    respuesta
                ],

                "contexts": [
                    contextos
                ],

                "ground_truth": [
                    referencia
                ]

            }

        )

        #
        # Resultado final.
        #
        # None significa que la métrica no pudo
        # ser evaluada correctamente.
        #

        resultados = {

            "answer_relevancy": None,

            "faithfulness": None,

            "context_precision": None,

            "context_recall": None

        }

        #
        # Métricas individuales.
        #

        metricas = [

            (
                "answer_relevancy",
                answer_relevancy
            ),

            (
                "faithfulness",
                self.faithfulness_batched
            ),

            (
                "context_precision",
                context_precision
            ),

            (
                "context_recall",
                context_recall
            )

        ]

        #
        # Evaluar cada métrica por separado.
        #

        for nombre, metrica in metricas:

            inicio = time.perf_counter()

            try:

                resultado = evaluate(

                    dataset,

                    metrics=[
                        metrica
                    ],

                    llm=self.llm,

                    embeddings=self.embeddings,

                    run_config=self.run_config,

                    raise_exceptions=True,

                    show_progress=False

                )

                fila = (
                    resultado
                    .to_pandas()
                    .iloc[0]
                )

                valor = fila[nombre]

                #
                # Convertir numpy.float64 a float
                # cuando sea un valor válido.
                #

                if valor is not None:

                    resultados[nombre] = float(
                        valor
                    )

                print(

                    f"[RAGAS] {nombre}: "
                    f"{resultados[nombre]}"

                )

            except RagasOutputParserException as e:

                print()
                print(
                    f"[RAGAS] {nombre}: "
                    "ERROR DE PARSEO"
                )

                print(
                    f"[RAGAS] {type(e).__name__}: "
                    f"{e}"
                )

                resultados[nombre] = None

            except Exception as e:

                print()
                print(
                    f"[RAGAS] {nombre}: "
                    "ERROR"
                )

                print(
                    f"[RAGAS] {type(e).__name__}: "
                    f"{e}"
                )

                resultados[nombre] = None

            finally:

                tiempo = (
                    time.perf_counter() - inicio
                )

                print(
                    f"[RAGAS TIEMPO] "
                    f"{nombre}: "
                    f"{tiempo:.2f} s"
                )

        #
        # Resultado final.
        #

        return resultados

    def evaluar_metrica(

        self,

        nombre: str,

        pregunta: str,

        respuesta: str,

        contextos: list[str],

        referencia: str

    ):

        metricas_disponibles = {

            "answer_relevancy":
                answer_relevancy,

            "faithfulness":
                self.faithfulness_batched,

            "context_precision":
                context_precision,

            "context_recall":
                context_recall

        }

        if nombre not in metricas_disponibles:

            raise ValueError(
                f"Métrica RAGAS no válida: {nombre}"
            )

        metrica = metricas_disponibles[
            nombre
        ]

        if nombre == "context_recall":
            metrica.context_recall_prompt = (
                self.context_recall_prompt
            )

        if nombre == "context_precision":
            metrica.context_precision_prompt = (
                self.context_precision_prompt
            )

        dataset = Dataset.from_dict(

            {

                "question": [
                    pregunta
                ],

                "answer": [
                    respuesta
                ],

                "contexts": [
                    contextos
                ],

                "ground_truth": [
                    referencia
                ]

            }

        )

        inicio = time.perf_counter()

        try:

            run_config = self.run_config

            if nombre in (
                "context_recall",
                "context_precision"
            ):
                run_config = RunConfig(
                    timeout=600,
                    max_retries=1,
                    max_wait=5,
                    max_workers=1
                )

            llm = self.llm

            if nombre == "context_recall":
                llm = self.context_recall_llm

            if nombre == "context_precision":
                llm = self.context_precision_llm

            resultado = evaluate(
                dataset,
                metrics=[metrica],
                llm=llm,
                embeddings=self.embeddings,
                run_config=run_config,
                raise_exceptions=True,
                show_progress=False
            )

            fila = (
                resultado
                .to_pandas()
                .iloc[0]
            )

            valor = fila[
                nombre
            ]

            if valor is None:

                raise ValueError(
                    f"RAGAS devolvió None "
                    f"para {nombre}"
                )

            valor = float(
                valor
            )

            if valor != valor:

                raise ValueError(
                    f"RAGAS devolvió NaN "
                    f"para {nombre}"
                )

            print(
                f"[RAGAS] {nombre}: {valor}"
            )

            return valor

        except RagasOutputParserException:

            print(
                f"[RAGAS] {nombre}: "
                "ERROR DE PARSEO"
            )

            raise

        except Exception:

            print(
                f"[RAGAS] {nombre}: ERROR"
            )

            raise

        finally:

            tiempo = (
                time.perf_counter()
                - inicio
            )

            print(
                f"[RAGAS TIEMPO] "
                f"{nombre}: "
                f"{tiempo:.2f} s"
            )
