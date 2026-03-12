// frontend/src/services/api.js
const API_URL = "http://127.0.0.1:8000"; // <--- asegúrate que diga localhost, no IP local

export async function hacerConsulta(pregunta) {
  try {
    const response = await fetch(`${API_URL}/consulta`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ pregunta }),
    });

    if (!response.ok) {
      throw new Error(`Error del servidor: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error al consultar el backend:", error);
    return {
      respuesta: "⚠️ No se pudo obtener respuesta del servidor.",
      justificacion: "",
      contexto_usado: "",
    };
  }
}