{/* frontend/src/App.jsx */}
import { useState } from "react";

import MainLayout from "./layout/MainLayout";

import AssistantPage from "./pages/AssistantPage";
import ResultsPage from "./pages/ResultsPage";
import DatabasePage from "./pages/DatabasePage";

const API_URL = import.meta.env.VITE_API_URL;

export default function App() {

    const [page, setPage] = useState("assistant");

    //
    // Estado global de la consulta
    //

    const [loading, setLoading] = useState(false);

    const [errorMsg, setErrorMsg] = useState("");

    const [data, setData] = useState(null);

    const [model, setModel] = useState("gemma4:e2b");

    const [rag, setRag] = useState("nomic");

    //
    // Ejecutar consulta
    //

    const handleQuery = async (query) => {

        setLoading(true);

        setErrorMsg("");

        setData(null);

        try {

            const res = await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({

                        pregunta: query,

                        modelo: model,

                        rag: rag

                    })
                }
            );

            if (!res.ok) {

                throw new Error(
                    `HTTP ${res.status}`
                );

            }

            const json = await res.json();

            const respuesta = (
                json.respuesta || ""
            )
                .replace(
                    /^\*\*Respuesta:\*\*\s*/i,
                    ""
                )
                .trim();

            setData({

                respuesta,

                documento: json.documento,

                modelo: json.modelo,

                tiempo: json.tiempo,

                chunks: json.chunks,

                tokens: json.tokens,

                score: json.score

            });

        } catch (err) {

            console.error(err);

            setErrorMsg(
                "No se pudo obtener respuesta."
            );

        } finally {

            setLoading(false);

        }

    };

    return (

        <MainLayout
            page={page}
            setPage={setPage}
        >

            {/*
             * Las páginas permanecen montadas.
             * Solo ocultamos las que no están seleccionadas.
             *
             * Esto evita perder estados internos
             * al cambiar de sección.
             */}

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

                    handleQuery={handleQuery}

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