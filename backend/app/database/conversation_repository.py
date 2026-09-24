from datetime import datetime

from bson import ObjectId

from app.database.mongodb import conversaciones

def crear_conversacion():

    ahora = datetime.utcnow()

    resultado = conversaciones.insert_one(

        {

            "fecha_inicio": ahora,

            "fecha_ultima_actualizacion": ahora,

            "mensajes": []

        }

    )

    return str(resultado.inserted_id)


def agregar_mensaje(

    conversation_id,

    rol,

    contenido

):

    conversaciones.update_one(

        {

            "_id": ObjectId(conversation_id)

        },

        {

            "$push": {

                "mensajes": {

                    "rol": rol,

                    "contenido": contenido,

                    "fecha": datetime.utcnow()

                }

            },

            "$set": {

                "fecha_ultima_actualizacion": datetime.utcnow()

            }

        }

    )