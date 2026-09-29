# document_repository.py

from datetime import datetime

from app.database.mongodb import documentos


def guardar_documento(
    nombre,
    tamano,
    chunks,
    estado="Indexado",
):




    resultado = documentos.update_one(
        {"nombre": nombre},
        {
            "$set": {
                "nombre": nombre,
                "tamano": tamano,
                "chunks": chunks,
                "estado": estado,
                "fecha_subida": datetime.utcnow(),
            }
        },
        upsert=True,
    )




def listar_documentos():

    return list(

        documentos.find(

            {},

            {

                "_id": 0

            }

        )

    )




def eliminar_documento(nombre):

    documentos.delete_one(

        {

            "nombre": nombre

        }

    )
