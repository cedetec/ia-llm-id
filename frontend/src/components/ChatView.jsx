{/* frontend/src/components/ChatView.jsx */}
import QueryInput from "./QueryInput";
import TagList from "./TagList";
import ResultCard from "./ResultCard";
import ModelSelector from "./ModelSelector";

export default function ChatView({

    model,
    setModel,

    loading,

    onQuery,

    respuesta,

    error

}){

    return(

        <div className="space-y-6">

            <div>

                <h1 className="text-3xl font-bold text-primary-dark">

                    Asistente Conversacional IA I+D

                </h1>

                <p className="text-gray-500 mt-2">

                    Consulta bases concursables ANID utilizando distintos modelos de IA.

                </p>

            </div>

            <div className="bg-white rounded-lg shadow p-5">

                <label className="font-semibold">

                    Modelo de IA

                </label>

                <div className="mt-2">

                    <ModelSelector

                        model={model}
                        setModel={setModel}

                    />

                </div>

            </div>

            <QueryInput

                onSubmit={onQuery}

                loading={loading}

            />

            <TagList

                onPick={onQuery}

            />

            <ResultCard

                respuesta={respuesta}

                error={error}

            />

        </div>

    );

}