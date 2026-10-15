{/* frontend/src/components/DatabaseView.jsx */}
export default function DatabaseView({

    documentos,
    chunks,
    coleccion,
    embedding,
    modelo,
    ultimaIndexacion,
    concursos=[],
    seleccionados=[],
    onToggleSeleccion

}){

    return(

        <div className="space-y-8">

            <h1 className="text-3xl font-bold text-primary-dark">

                Base de Datos ANID

            </h1>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Documentos

                    </h3>

                    <p className="text-3xl">

                        {documentos}

                    </p>

                </div>

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Chunks

                    </h3>

                    <p className="text-3xl">

                        {chunks}

                    </p>

                </div>

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Colección

                    </h3>

                    <p>

                        {coleccion}

                    </p>

                </div>

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Embedding

                    </h3>

                    <p>

                        {embedding}

                    </p>

                </div>

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Modelo IA

                    </h3>

                    <p>

                        {modelo}

                    </p>

                </div>

                <div className="bg-white shadow rounded-lg p-4">

                    <h3 className="font-semibold">

                        Última indexación

                    </h3>

                    <p>

                        {ultimaIndexacion}

                    </p>

                </div>

            </div>

            <div className="bg-white rounded-lg shadow p-5">

                <h2 className="text-xl font-bold mb-4">

                    Concursos Indexados

                </h2>

                <table className="w-full border">

                    <thead>

                        <tr className="bg-gray-100">

                            <th className="p-2">
                                Seleccionar
                            </th>

                            <th className="p-2">

                                Concurso

                            </th>

                            <th className="p-2">

                                Año

                            </th>

                            <th className="p-2">

                                Estado

                            </th>

                            <th className="p-2">

                                Chunks

                            </th>

                        </tr>

                    </thead>

                    <tbody>

                        {

                            concursos.map(

                                (c,index)=>(

                                    <tr key={index}>

                                        <td className="p-2 text-center">

                                            <input
                                                type="checkbox"
                                                checked={seleccionados.includes(c.nombre)}
                                                onChange={() =>
                                                    onToggleSeleccion(c.nombre)
                                                }
                                            />

                                        </td>

                                        <td className="p-2">

                                            {c.nombre}

                                        </td>

                                        <td className="p-2">

                                            {c.anio}

                                        </td>

                                        <td className="p-2">

                                            {c.estado}

                                        </td>

                                        <td className="p-2">

                                            {c.chunks}

                                        </td>

                                    </tr>

                                )

                            )

                        }

                    </tbody>

                </table>

            </div>

        </div>

    );

}
