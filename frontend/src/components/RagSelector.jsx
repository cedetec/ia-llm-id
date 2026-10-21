{/* frontend/src/components/RagSelector.jsx */}

export default function RagSelector({

    rag,
    setRag

}){

    return(

        <select

            value="embeddinggemma"

            disabled

            className="border rounded p-2 bg-gray-100 text-gray-500 cursor-not-allowed"

        >

            <option value="embeddinggemma">

                EmbeddingGemma (Fijo)

            </option>

        </select>

    );

}