import pymongo

# Conectar a MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Conectar a la base de datos "asistenteID"
db = client["asistenteID"]

# Imprimir el nombre de las bases de datos disponibles
databases = client.list_database_names()
print("Bases de datos disponibles:", databases)

# Intentar acceder a una colección dentro de la base de datos
collection = db["calendarios"]
print("Colección 'calendarios' lista:", collection)

# Realizar una consulta de prueba
sample_document = collection.find_one()
print("Documento de prueba encontrado:", sample_document)
