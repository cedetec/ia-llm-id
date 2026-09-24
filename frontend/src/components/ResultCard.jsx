{/* frontend/src/components/ResultCard.jsx */}
export default function ResultCard({ respuesta, error }) {

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

        </div>

    );

}