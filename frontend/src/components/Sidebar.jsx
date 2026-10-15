{/* frontend/src/components/Sidebar.jsx */}
export default function Sidebar({

    page,
    setPage,
    open

}) {

    return (

        <aside

            className={`
                h-screen
                flex-shrink-0
                bg-primary-dark
                text-white
                overflow-hidden
                transition-all
                duration-300
                ${open ? "w-72 p-6" : "w-0 p-0"}
            `}

        >

            <div
                className={`
                    w-60
                    pt-14
                    transition-opacity
                    duration-200
                    ${open
                        ? "opacity-100"
                        : "opacity-0"
                    }
                `}
            >

                <h2
                    className="
                        text-2xl
                        font-bold
                        mb-8
                        text-center
                    "
                >
                    Asistente I+D
                </h2>


                <button

                    onClick={() =>
                        setPage("assistant")
                    }

                    className={`
                        w-full
                        text-left
                        mb-3
                        p-2
                        rounded-md
                        ${
                            page === "assistant"
                                ? "bg-primary"
                                : "hover:bg-primary"
                        }
                    `}

                >

                    🤖 Asistente Conversacional IA

                </button>


                <button

                    onClick={() =>
                        setPage("results")
                    }

                    className={`
                        w-full
                        text-left
                        mb-3
                        p-2
                        rounded-md
                        ${
                            page === "results"
                                ? "bg-primary"
                                : "hover:bg-primary"
                        }
                    `}

                >

                    📊 Resultados

                </button>


                <button

                    onClick={() =>
                        setPage("database")
                    }

                    className={`
                        w-full
                        text-left
                        p-2
                        rounded-md
                        ${
                            page === "database"
                                ? "bg-primary"
                                : "hover:bg-primary"
                        }
                    `}

                >

                    🗄 Base de Datos ANID

                </button>

            </div>

        </aside>

    );

}
