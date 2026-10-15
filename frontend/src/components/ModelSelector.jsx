{/* frontend/src/components/ModelSelector.jsx */}
export default function ModelSelector({

    model,
    setModel

}){

    return(

        <select

            value={model}

            onChange={(e)=>setModel(e.target.value)}

            className="border rounded p-2"

        >

            <option value="gemma4:e2b">

                gemma4:e2b

            </option>

            <option value="deepseek-r1:8b">

                deepseek-r1:8b

            </option>

            <option value="qwen2.5:latest">

                qwen2.5:latest

            </option>

            <option value="mistral:latest">

                mistral:latest

            </option>

        </select>

    );

}
