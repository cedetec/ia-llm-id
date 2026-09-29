{/* frontend/src/services/ChatDatabase.jsx */}
const API_URL = import.meta.env.VITE_API_URL ?? "";


/**
 * Obtiene las estadísticas actuales
 * de la base de datos.
 */
export async function obtenerEstadisticas() {

    const response = await fetch(
        `${API_URL}/database/stats`
    );


    if (!response.ok) {

        throw new Error(
            `Error HTTP ${response.status}`
        );

    }


    return await response.json();

}


/**
 * Sube un PDF al backend.
 */
export async function subirPDF(file) {

    if (!file) {

        throw new Error(
            "No se seleccionó ningún archivo."
        );

    }


    const formData =
        new FormData();

    formData.append(
        "archivo",
        file
    );


    const response =
        await fetch(
            `${API_URL}/database/upload`,
            {
                method: "POST",
                body: formData
            }
        );


    if (!response.ok) {

        let detalle = "";

        try {

            const json =
                await response.json();

            detalle =
                json.detail ||
                json.message ||
                "";

        } catch {

            // Respuesta no JSON.
        }


        throw new Error(
            detalle ||
            `No fue posible subir ${file.name}.`
        );

    }


    return await response.json();

}


/**
 * Descarga PDFs seleccionados.
 */
export async function descargarPDFs(
    seleccionados
) {

    if (
        !Array.isArray(seleccionados) ||
        seleccionados.length === 0
    ) {

        throw new Error(
            "Seleccione al menos un PDF."
        );

    }


    const response =
        await fetch(
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

        let detalle = "";

        try {

            detalle =
                await response.text();

        } catch {

            // Sin detalle adicional.
        }


        throw new Error(
            detalle ||
            "No fue posible descargar los archivos."
        );

    }


    const blob =
        await response.blob();


    const url =
        window.URL.createObjectURL(
            blob
        );


    const enlace =
        document.createElement("a");

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

}


/**
 * Reindexa los documentos de la base.
 */
export async function reindexarBaseDatos() {

    const response =
        await fetch(
            `${API_URL}/database/reindex`,
            {
                method: "POST"
            }
        );


    if (!response.ok) {

        let detalle = "";

        try {

            const json =
                await response.json();

            detalle =
                json.detail ||
                json.message ||
                "";

        } catch {

            // Respuesta no JSON.
        }


        throw new Error(
            detalle ||
            `Error HTTP ${response.status}`
        );

    }


    return await response.json();

}


/**
 * Descarga la base de datos completa,
 * si el endpoint está habilitado.
 */
export function descargarBaseDatos() {

    window.open(
        `${API_URL}/database/download`,
        "_blank"
    );

}
