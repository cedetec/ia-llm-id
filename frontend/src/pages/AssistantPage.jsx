{/* frontend/src/pages/AssistantPage.jsx */}

import QueryInput from "../components/QueryInput";
import ResultCard from "../components/ResultCard";
import TagList from "../components/TagList";
import ModelSelector from "../components/ModelSelector";
import RagSelector from "../components/RagSelector";


export default function AssistantPage({

    loading,
    errorMsg,
    data,

    model,
    setModel,

    rag,
    setRag,

    handleQuery,

    cancelarConsulta,

    limpiarResultado

}) {

    return (

        <div className="space-y-6">

            <h1 className="text-3xl font-bold text-primary-dark text-center">
                Asistente Conversacional IA I+D
            </h1>


            {/* Indicador de estado de la consulta */}

            <div
                className="
                    flex
                    items-center
                    justify-between
                    rounded-xl
                    border
                    bg-white
                    px-4
                    py-3
                    shadow-sm
                "
            >

                <div>

                    <p className="text-sm font-medium text-gray-700">

                        {loading
                            ? "El asistente está procesando la consulta..."
                            : data
                                ? "Consulta completada"
                                : "Listo para consultar"
                        }

                    </p>

                    <p className="text-xs text-gray-500">

                        Modelo: {model}
                        {" · "}
                        RAG: {rag}

                    </p>

                </div>


                <div className="flex gap-2">

                    {loading && (

                        <button

                            type="button"

                            onClick={
                                cancelarConsulta
                            }

                            className="
                                rounded-lg
                                border
                                border-red-300
                                px-3
                                py-2
                                text-sm
                                text-red-600
                                hover:bg-red-50
                                transition
                            "

                        >

                            Cancelar

                        </button>

                    )}


                    {data && !loading && (

                        <button

                            type="button"

                            onClick={
                                limpiarResultado
                            }

                            className="
                                rounded-lg
                                border
                                px-3
                                py-2
                                text-sm
                                text-gray-600
                                hover:bg-gray-50
                                transition
                            "

                        >

                            Nueva consulta

                        </button>

                    )}

                </div>

            </div>


            <ModelSelector
                model={model}
                setModel={setModel}
            />


            <RagSelector
                rag={rag}
                setRag={setRag}
            />


            <QueryInput
                onSubmit={handleQuery}
                loading={loading}
            />


            <TagList
                onPick={handleQuery}
            />


            <ResultCard
                respuesta={data?.respuesta}
                error={errorMsg}
                extractos={data?.extractos}
            />

        </div>

    );

}
