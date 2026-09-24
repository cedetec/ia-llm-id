{/* frontend/src/components/QueryInput.jsx */}
import { useState } from "react";

export default function QueryInput({

    onSubmit,
    loading

}) {

    const [query, setQuery] = useState("");

    const handleSubmit = (e) => {

        e.preventDefault();

        const q = query.trim();

        if (q && !loading) {

            onSubmit(q);

        }

    };

    return (

        <form

            onSubmit={handleSubmit}

            className="flex gap-2"

        >

            <input

                type="text"

                value={query}

                onChange={(e) =>
                    setQuery(e.target.value)
                }

                className="
                    flex-1
                    border
                    border-gray-300
                    rounded-md
                    p-2
                "

                placeholder="Escribe tu pregunta..."

                disabled={false}

            />


            <button

                type="submit"

                disabled={loading}

                className={`
                    px-4
                    py-2
                    rounded-md
                    text-white
                    ${
                        loading
                            ? "bg-primary/50 cursor-not-allowed"
                            : "bg-primary hover:bg-primary-dark"
                    }
                `}

            >

                {loading
                    ? "Consultando..."
                    : "Consultar"
                }

            </button>

        </form>

    );

}
