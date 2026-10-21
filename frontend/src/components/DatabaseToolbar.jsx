{/* frontend/src/components/DatabaseToolbar.jsx */}
export default function DatabaseToolbar({

    onUpload,
    onDownload,
    onStats

}){

    return(

        <div className="flex gap-4 mb-6">

            <button
                onClick={onUpload}
                className="bg-primary text-white px-4 py-2 rounded"
            >
                Cargar datos
            </button>

            <button
                onClick={onDownload}
                className="bg-secondary text-white px-4 py-2 rounded"
            >
                Descargar datos
            </button>

            <button
                onClick={onStats}
                className="bg-gray-700 text-white px-4 py-2 rounded"
            >
                Manejo Base de Datos
            </button>

        </div>

    );

}
