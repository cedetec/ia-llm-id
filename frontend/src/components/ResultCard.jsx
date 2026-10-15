{/* frontend/src/components/ResultCard.jsx */}
export default function ResultCard({ respuesta, error, extractos }) {

    if (error) {

        return (
            <div className="border border-danger/30 bg-red-50 text-danger rounded-lg p-4">

                <p className="font-semibold">
                    ⚠️ Error
                </p>

                <p className="text-sm">
                    {error}
                </p>

            </div>
        );

    }

    if (!respuesta) return null;

    return (

        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm space-y-3">

            <h2 className="font-semibold text-lg text-neutral-dark">
                Respuesta
            </h2>

            <p className="text-gray-800 whitespace-pre-line">
                {respuesta}
            </p>

            {extractos && extractos.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                    <details className="group">
                        <summary className="text-sm font-medium text-primary-dark cursor-pointer select-none">
                            Ver {extractos.length} extractos de contexto recuperados
                        </summary>
                        <div className="mt-3 space-y-3">
                            {extractos.map((ext, idx) => (
                                <div key={idx} className="bg-gray-50 p-3 rounded text-sm text-gray-700 border border-gray-200">
                                    <span className="font-semibold text-xs text-gray-500 block mb-1">Extracto {idx + 1}</span>
                                    {ext}
                                </div>
                            ))}
                        </div>
                    </details>
                </div>
            )}

        </div>

    );

}