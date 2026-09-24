{/* frontend/src/pages/DatabasePage.jsx */}
import { useEffect, useRef, useState } from "react";

import DatabaseToolbar from "../components/DatabaseToolbar";
import DatabaseView from "../components/DatabaseView";

const API_URL = import.meta.env.VITE_API_URL;

export default function DatabasePage(){

    const fileInputRef = useRef(null);

    const [database,setDatabase] = useState({

        documentos:0,
        chunks:0,
        coleccion:"",
        embedding:"",
        modelo:"",
        ultimaIndexacion:"",
        concursos:[]

    });

    const [seleccionados, setSeleccionados] = useState([]);

    console.log("DATABASE", database);

    useEffect(() => {

        obtenerEstadisticas();

    }, []);

    const cargarDatos = ()=>{

        fileInputRef.current.click();

    };

    const subirArchivo = async (event) => {

        console.log("subirArchivo ejecutado");

        const file = event.target.files[0];

        if (!file) {
            console.log("No hay archivo");
            return;
        }

        console.log(file.name);

        const formData = new FormData();

        formData.append("archivo", file);

        try {

            const response = await fetch(
                `${API_URL}/database/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );

            console.log("Status:", response.status);

            const texto = await response.text();

            console.log(texto);

        } catch (e) {

            console.error(e);

        }
    };

    const cambiarSeleccion = (nombre) => {

        setSeleccionados((actuales) => {

            if (actuales.includes(nombre)) {

                return actuales.filter(
                    (archivo) => archivo !== nombre
                );

            }

            return [
                ...actuales,
                nombre
            ];

        });

    };

    const descargarDatos = async () => {

        if (seleccionados.length === 0) {

            alert(
                "Seleccione al menos un PDF para descargar."
            );

            return;
        }

        try {

            const response = await fetch(
                `${API_URL}/database/download-selected`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(
                        seleccionados
                    )
                }
            );

            if (!response.ok) {

                const texto = await response.text();

                throw new Error(
                    texto ||
                    "No fue posible descargar los archivos."
                );

            }

            const blob = await response.blob();

            const url = window.URL.createObjectURL(
                blob
            );

            const enlace = document.createElement("a");

            enlace.href = url;

            enlace.download =
                "anid_pdfs_seleccionados.zip";

            document.body.appendChild(
                enlace
            );

            enlace.click();

            enlace.remove();

            window.URL.revokeObjectURL(
                url
            );

        } catch (error) {

            console.error(
                "Error al descargar PDFs:",
                error
            );

            alert(
                "No fue posible descargar los archivos seleccionados."
            );

        }

    };

    const obtenerEstadisticas = async()=>{

        console.log("LLAMANDO A /database/stats");

        const response = await fetch(
            `${API_URL}/database/stats`
        );

        const json = await response.json();

        console.log(json);

        setDatabase(json);

    };

    const entrenar = async () => {

        const response = await fetch(
            `${API_URL}/database/reindex`,
            {
                method: "POST"
            }
        );

        const json = await response.json();

        console.log(json);

        await obtenerEstadisticas();

    };

    return(

        <>

            <input

                type="file"

                accept=".pdf"

                ref={fileInputRef}

                hidden

                onChange={subirArchivo}

            />

            <DatabaseToolbar

                onUpload={cargarDatos}

                onDownload={descargarDatos}

                onStats={obtenerEstadisticas}

                onTrain={entrenar}

            />

            <DatabaseView

                {...database}

                seleccionados={seleccionados}

                onToggleSeleccion={cambiarSeleccion}

            />

        </>

    );

}
