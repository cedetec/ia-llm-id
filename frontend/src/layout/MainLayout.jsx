{/* frontend/src/layout/MainLayout.jsx */}
import { useState } from "react";

import Sidebar from "../components/Sidebar";

export default function MainLayout({

    page,
    setPage,
    children

}) {

    const [sidebarOpen, setSidebarOpen] = useState(true);

    return (

        <div className="flex h-screen">

            {/*
             * Botón global para abrir/cerrar
             * la barra lateral.
             */}

            <button

                onClick={() =>
                    setSidebarOpen(
                        !sidebarOpen
                    )
                }

                className="
                    fixed
                    top-4
                    left-4
                    z-50
                    w-10
                    h-10
                    rounded-md
                    bg-primary-dark
                    text-white
                    text-xl
                    flex
                    items-center
                    justify-center
                    shadow-md
                    hover:bg-primary
                "

                aria-label={
                    sidebarOpen
                        ? "Cerrar menú"
                        : "Abrir menú"
                }

            >

                ☰

            </button>


            {/*
             * Sidebar
             */}

            <Sidebar

                page={page}

                setPage={setPage}

                open={sidebarOpen}

            />


            {/*
             * Área principal
             */}

            <main

                className={`
                    flex-1
                    bg-gray-50
                    p-8
                    overflow-auto
                    transition-all
                    duration-300
                `}

            >

                {children}

            </main>

        </div>

    );

}
