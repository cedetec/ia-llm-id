import { useState } from "react";

export default function ResultCard({ respuesta, justificacion, error }) {
  const [open, setOpen] = useState(false);

  if (error) {
    return (
      <div className="border border-danger/30 bg-red-50 text-danger rounded-lg p-4">
        <p className="font-semibold">⚠️ Error</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (!respuesta) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm space-y-3">
      <h2 className="font-semibold text-lg text-neutral-dark">Respuesta</h2>
      <p className="text-gray-800 whitespace-pre-line">{respuesta}</p>

      {justificacion?.trim() && (
        <div className="pt-2 border-t">
          <button
            onClick={() => setOpen(!open)}
            className="text-primary hover:underline text-sm"
          >
            {open ? "Ocultar justificación" : "Ver justificación"}
          </button>
          {open && (
            <p className="mt-2 text-gray-600 text-sm whitespace-pre-line">
              {justificacion}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
