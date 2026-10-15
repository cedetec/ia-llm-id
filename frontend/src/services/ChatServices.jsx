{/* frontend/src/services/ChatServices.jsx */}
const API_URL = import.meta.env.VITE_API_URL ?? "";


/**
 * Limpia prefijos que pueda devolver el LLM.
 */
function limpiarTexto(texto = "") {

    return texto
        .replace(/^\\*\\*Respuesta:\\*\\*\\s*/i, "")
        .replace(/^\\*\\*Justificación:\\*\\*\\s*/i, "")
        .trim();

}


/**
 * Ejecuta una consulta contra el servicio de chat.
 *
 * Este es el único lugar del frontend
 * donde se realiza la llamada POST /chat.
 */
export async function enviarChat({
    pregunta,
    modelo,
    rag,
    signal
}) {

    const response = await fetch(
        `${API_URL}/chat`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                pregunta,
                modelo,
                rag
            }),

            signal
        }
    );


    if (!response.ok) {

        let detalle = "";

        try {

            const errorJson =
                await response.json();

            detalle =
                errorJson.detail ||
                errorJson.message ||
                "";

        } catch {

            // El backend puede responder
            // con un cuerpo no JSON.
        }


        throw new Error(
            detalle ||
            `Error HTTP ${response.status}`
        );

    }


    const json =
        await response.json();


    return {

        ...json,

        respuesta:
            limpiarTexto(json.respuesta),

        justificacion:
            limpiarTexto(json.justificacion)

    };

}
