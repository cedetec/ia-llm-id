{/* frontend/src/pages/DatabasePage.jsx */}

import {
    useEffect,
    useRef,
    useState
} from "react";

import DatabaseToolbar from "../components/DatabaseToolbar";
import DatabaseView from "../components/DatabaseView";

import {
    obtenerEstadisticas,
    subirPDF,
    descargarPDFs
} from "../services/ChatDatabase";


export default function DatabasePage(){

    const fileInputRef =
        useRef(null);


    const [database, setDatabase] =
        useState({

            documentos: 0,
            chunks: 0,
            coleccion: "",
            embedding: "",
            modelo: "",
            ultimaIndexacion: "",
            concursos: []

        });


    const [seleccionados, setSeleccionados] =
        useState([]);


    /*
     * Estados de interacción
     */

    const [cargando, setCargando] =
        useState(false);


    const [subiendo, setSubiendo] =
        useState(false);


    const [mensaje, setMensaje] =
        useState("");


    const [errorMsg, setErrorMsg] =
        useState("");


    /*
     * Cargar estadísticas al entrar
     * a la página.
     */

    useEffect(() => {

        cargarEstadisticas();

    }, []);


    /*
     * Abrir selector de archivos.
     */

    const cargarDatos = () => {

        fileInputRef.current?.click();

    };


    /*
     * Obtener estadísticas.
     */

    const cargarEstadisticas =
        async () => {

            setCargando(true);

            setErrorMsg("");

            try {

                const json =
                    await obtenerEstadisticas();

                setDatabase(json);

            } catch (error) {

                console.error(error);

                setErrorMsg(
                    error.message ||
                    "No se pudieron cargar las estadísticas."
                );

            } finally {

                setCargando(false);

            }

        };


    /*
     * Subir PDF.
     */

    const subirArchivo =
        async (event) => {

            const file =
                event.target.files?.[0];


            if (!file) {

                return;

            }


            /*
             * Validación básica del tipo.
             */

            if (
                file.type !==
                "application/pdf"
            ) {

                setErrorMsg(
                    "Solo se permiten archivos PDF."
                );

                event.target.value = "";

                return;

            }


            setSubiendo(true);

            setMensaje("");

            setErrorMsg("");


            try {

                await subirPDF(file);


                setMensaje(
                    `Archivo "${file.name}" subido correctamente.`
                );


                /*
                 * Actualizar estadísticas
                 * después de subir el archivo.
                 */

                await cargarEstadisticas();


            } catch (error) {

                console.error(error);

                setErrorMsg(
                    error.message ||
                    "No se pudo subir el archivo."
                );

            } finally {

                setSubiendo(false);

                /*
                 * Permite volver a seleccionar
                 * el mismo archivo posteriormente.
                 */

                event.target.value = "";

            }

        };


    /*
     * Cambiar selección de PDF.
     */

    const cambiarSeleccion =
        (nombre) => {

            setSeleccionados(
                (actuales) => {

                    if (
                        actuales.includes(nombre)
                    ) {

                        return actuales.filter(
                            (archivo) =>
                                archivo !== nombre
                        );

                    }


                    return [
                        ...actuales,
                        nombre
                    ];

                }
            );

        };


    /*
     * Descargar PDFs seleccionados.
     */

    const descargarDatos =
        async () => {

            setErrorMsg("");

            setMensaje("");


            try {

                await descargarPDFs(
                    seleccionados
                );


                setMensaje(
                    "Descarga iniciada correctamente."
                );


            } catch (error) {

                console.error(
                    "Error al descargar PDFs:",
                    error
                );


                setErrorMsg(
                    error.message ||
                    "No fue posible descargar los archivos."
                );

            }

        };


    return (

        <div className="space-y-4">

            {/* =============================== */}
            {/* MENSAJES DE ESTADO              */}
            {/* =============================== */}

            {mensaje && (

                <div
                    className="
                        rounded-lg
                        border
                        border-green-200
                        bg-green-50
                        px-4
                        py-3
                        text-sm
                        text-green-700
                    "
                >

                    ✅ {mensaje}

                </div>

            )}


            {errorMsg && (

                <div
                    className="
                        rounded-lg
                        border
                        border-red-200
                        bg-red-50
                        px-4
                        py-3
                        text-sm
                        text-red-700
                    "
                >

                    ⚠️ {errorMsg}

                </div>

            )}


            {cargando && (

                <div
                    className="
                        rounded-lg
                        bg-blue-50
                        px-4
                        py-3
                        text-sm
                        text-blue-700
                    "
                >

                    🔄 Actualizando información
                    de la base de datos...

                </div>

            )}


            {subiendo && (

                <div
                    className="
                        rounded-lg
                        bg-purple-50
                        px-4
                        py-3
                        text-sm
                        text-purple-700
                    "
                >

                    📤 Subiendo documento...

                </div>

            )}


            {/* =============================== */}
            {/* ARCHIVOS SELECCIONADOS          */}
            {/* =============================== */}

            {seleccionados.length > 0 && (

                <div
                    className="
                        rounded-lg
                        border
                        bg-white
                        px-4
                        py-3
                        text-sm
                        text-gray-700
                    "
                >

                    📄 {seleccionados.length}
                    {" "}
                    archivo(s) seleccionado(s)

                </div>

            )}


            {/* =============================== */}
            {/* INPUT DE ARCHIVO                 */}
            {/* =============================== */}

            <input

                type="file"

                accept=".pdf,application/pdf"

                ref={fileInputRef}

                hidden

                onChange={subirArchivo}

            />


            {/* =============================== */}
            {/* BARRA DE HERRAMIENTAS            */}
            {/* =============================== */}

            <DatabaseToolbar

                onUpload={cargarDatos}

                onDownload={descargarDatos}

                onStats={cargarEstadisticas}

            />


            {/* =============================== */}
            {/* INFORMACIÓN DE LA BASE           */}
            {/* =============================== */}

            <DatabaseView

                {...database}

                seleccionados={
                    seleccionados
                }

                onToggleSeleccion={
                    cambiarSeleccion
                }

            />

        </div>

    );

}
