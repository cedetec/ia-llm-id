{/* frontend/src/components/ResultsView.jsx */}
export default function ResultsView({

    respuesta,

    documento,

    modelo,

    tiempo,

    chunks,

    tokens,

    score,

    extractos

}){

    return(

        <div className="space-y-6">

            <h1 className="text-3xl font-bold text-primary-dark">

                Resultados de la Consulta

            </h1>

            <div className="bg-white rounded-lg shadow p-6">

                <h2 className="font-bold text-xl">

                    Respuesta

                </h2>

                <p className="mt-3 whitespace-pre-line">

                    {respuesta || "Sin respuesta"}

                </p>

            </div>

            <div className="bg-white rounded-lg shadow p-6">

                <h2 className="font-bold text-xl mb-4">

                    Información Técnica

                </h2>

                <table className="w-full">

                    <tbody>

                        <tr>

                            <td className="font-semibold">

                                Documento

                            </td>

                            <td>{documento}</td>

                        </tr>

                        <tr>

                            <td className="font-semibold">

                                Modelo IA

                            </td>

                            <td>{modelo}</td>

                        </tr>

                        <tr>

                            <td className="font-semibold">

                                Tiempo

                            </td>

                            <td>{tiempo}</td>

                        </tr>

                        <tr>

                            <td className="font-semibold">

                                Chunks recuperados

                            </td>

                            <td>{chunks}</td>

                        </tr>

                        <tr>

                            <td className="font-semibold">

                                Tokens

                            </td>

                            <td>{tokens}</td>

                        </tr>

                        <tr>

                            <td className="font-semibold">

                                Score

                            </td>

                            <td>{score}</td>

                        </tr>

                    </tbody>

                </table>

            </div>

            {extractos && extractos.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="font-bold text-xl mb-4">
                        Contextos Recuperados
                    </h2>
                    <div className="space-y-4">
                        {extractos.map((ext, idx) => (
                            <div key={idx} className="bg-gray-50 border border-gray-200 p-4 rounded-lg">
                                <h3 className="font-semibold text-gray-500 mb-2">Extracto {idx + 1}</h3>
                                <p className="text-gray-800 whitespace-pre-line text-sm">{ext}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

        </div>

    );

}
