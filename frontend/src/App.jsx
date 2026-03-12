import { useState } from "react";
import QueryInput from "./components/QueryInput";
import ResultCard from "./components/ResultCard";
import TagList from "./components/TagList";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8090";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [data, setData] = useState(null);

  const handleQuery = async (query) => {
    setLoading(true);
    setErrorMsg("");
    setData(null);
    try {
      const res = await fetch(`${API_URL}/consulta`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta: query }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();

      // Normalizar campos
      const respuesta = (json.respuesta || "").replace(/^\*\*Respuesta:\*\*\s*/i, "").trim();
      const justificacion = (json.justificacion || "")
        .replace(/^\*\*Justificación:\*\*\s*/i, "")
        .trim();

      setData({ respuesta, justificacion });
    } catch (err) {
      setErrorMsg("No se pudo obtener respuesta del servidor. Intenta nuevamente.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-start min-h-screen bg-neutral-light text-gray-800 p-6">
      <h1 className="text-3xl font-bold mb-6 text-primary-dark">
        Asistente I+D — Fondos Concursables
      </h1>

      {/* Campo de entrada principal */}
      <QueryInput onSubmit={handleQuery} loading={loading} />

      {/* 👇 Nueva sección de etiquetas */}
      <div className="my-4">
        <TagList onPick={(q) => handleQuery(q)} />
      </div>

      {/* Contenedor de resultados */}
      <div className="mt-8 w-full max-w-2xl">
        {errorMsg ? (
          <ResultCard error={errorMsg} />
        ) : (
          <ResultCard
            respuesta={data?.respuesta}
            justificacion={data?.justificacion}
          />
        )}
      </div>
    </div>
  );
}
