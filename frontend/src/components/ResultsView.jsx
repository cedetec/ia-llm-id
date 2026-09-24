{/* frontend/src/components/ResultsView.jsx */}
export default function ResultsView({

    respuesta,

    documento,

    modelo,

    tiempo,

    chunks,

    tokens,

    score

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

        </div>

    );

}
