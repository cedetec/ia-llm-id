{/* frontend/src/components/RagSelector.jsx */}

export default function RagSelector({

    rag,
    setRag

}){

    return(

        <select

            value={rag}

            onChange={(e)=>setRag(e.target.value)}

            className="border rounded p-2"

        >

            <option value="nomic">

                Nomic

            </option>

            <option value="embeddinggemma">

                EmbeddingGemma

            </option>

        </select>

    );

}