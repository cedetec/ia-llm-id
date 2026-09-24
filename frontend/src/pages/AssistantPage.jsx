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

    handleQuery

}) {

    return (

        <div className="space-y-6">

            <h1 className="text-3xl font-bold text-primary-dark text-center">
                Asistente Conversacional IA I+D
            </h1>

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
            />

        </div>

    );

}