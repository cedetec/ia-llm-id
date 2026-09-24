# document_repository.py

from datetime import datetime

from app.database.mongodb import documentos


def guardar_documento(
    nombre,
    tamano,
    chunks,
    estado="Indexado",
):

    print("=" * 80)
    print("ENTRÓ A guardar_documento")
    print("=" * 80)

    print({
        "nombre": nombre,
        "tamano": tamano,
        "chunks": chunks,
        "estado": estado,
    })

    print("Base:", documentos.database.name)
    print("Colección:", documentos.name)

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

    print("matched:", resultado.matched_count)
    print("modified:", resultado.modified_count)
    print("upserted:", resultado.upserted_id)
    print("total:", documentos.count_documents({}))

    print("=" * 80)
    print("SALIÓ DE guardar_documento")
    print("=" * 80)


def listar_documentos():

    return list(

        documentos.find(

            {},

            {

                "_id": 0

            }

        )

    )


def contar_documentos():

    return documentos.count_documents({})


def eliminar_documento(nombre):

    documentos.delete_one(

        {

            "nombre": nombre

        }

    )