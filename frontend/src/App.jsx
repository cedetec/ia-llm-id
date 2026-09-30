import { useRef, useState } from "react";

import MainLayout from "./layout/MainLayout";

import AssistantPage from "./pages/AssistantPage";
import ResultsPage from "./pages/ResultsPage";
import DatabasePage from "./pages/DatabasePage";

import { enviarChat } from "./services/ChatServices";


export default function App() {

    const [page, setPage] =
        useState("assistant");


    const [loading, setLoading] =
        useState(false);


    const [errorMsg, setErrorMsg] =
        useState("");


    const [data, setData] =
        useState(null);


    const [model, setModel] =
        useState("gemma4:e2b");


    const [rag, setRag] =
        useState("nomic");


    /*
     * Permite cancelar una consulta
     * que todavía está ejecutándose.
     */
    const controllerRef =
        useRef(null);


    const handleQuery =
        async (query) => {

            if (
                !query ||
                !query.trim()
            ) {

                setErrorMsg(
                    "Escriba una consulta."
                );

                return;

            }


            /*
             * Cancela automáticamente
             * una consulta anterior.
             */
            if (controllerRef.current) {

                controllerRef
                    .current
                    .abort();

            }


            const controller =
                new AbortController();

            controllerRef.current =
                controller;


            setLoading(true);

            setErrorMsg("");

            setData(null);


            try {

                const json =
                    await enviarChat({
                        pregunta:
                            query.trim(),

                        modelo:
                            model,

                        rag,

                        signal:
                            controller.signal
                    });


                setData({

                    respuesta:
                        json.respuesta || "",

                    justificacion:
                        json.justificacion || "",

                    documento:
                        json.documento,

                    modelo:
                        json.modelo,

                    tiempo:
                        json.tiempo,

                    chunks:
                        json.chunks,

                    tokens:
                        json.tokens,

                    score:
                        json.score

                });


            } catch (err) {

                if (
                    err.name ===
                    "AbortError"
                ) {

                    setErrorMsg(
                        "Consulta cancelada."
                    );

                } else {

                    console.error(err);

                    setErrorMsg(
                        err.message ||
                        "No se pudo obtener respuesta."
                    );

                }

            } finally {

                setLoading(false);

                controllerRef.current =
                    null;

            }

        };


    const cancelarConsulta =
        () => {

            if (
                controllerRef.current
            ) {

                controllerRef
                    .current
                    .abort();

            }

        };


    const limpiarResultado =
        () => {

            setData(null);

            setErrorMsg("");

        };


    return (

        <MainLayout
            page={page}
            setPage={setPage}
        >

            <div
                className={
                    page === "assistant"
                        ? "block"
                        : "hidden"
                }
            >

                <AssistantPage

                    loading={loading}

                    errorMsg={errorMsg}

                    data={data}

                    model={model}

                    setModel={setModel}

                    rag={rag}

                    setRag={setRag}

                    handleQuery={
                        handleQuery
                    }

                    cancelarConsulta={
                        cancelarConsulta
                    }

                    limpiarResultado={
                        limpiarResultado
                    }

                />

            </div>


            <div
                className={
                    page === "results"
                        ? "block"
                        : "hidden"
                }
            >

                <ResultsPage
                    data={data}
                />

            </div>


            <div
                className={
                    page === "database"
                        ? "block"
                        : "hidden"
                }
            >

                <DatabasePage />

            </div>

        </MainLayout>

    );

}