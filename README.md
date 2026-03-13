Instrucciones para probar el sistema (Docker)
1. Clonar el repositorio
git clone https://github.com/cedetec/ia-llm-id.git
cd ia-llm-id

2. Construir los contenedores
docker compose build

3. Iniciar los servicios
docker compose up -d

Esto iniciará:

Backend FastAPI

MongoDB

Ollama

4. Verificar contenedores
docker ps

Deberían aparecer:

asistente_backend
mongo_db
ollama_service

5. Descargar el modelo DeepSeek
docker exec -it ollama_service ollama pull deepseek-r1

Verificar:

docker exec -it ollama_service ollama list

6. Verificar backend

Abrir en el navegador:

http://localhost:8090/docs

También puedes probar:

curl http://127.0.0.1:8090/health/ping

7. Cargar documentos por primera vez

El sistema incluye un script para subir y procesar automáticamente los documentos PDF.

Primero asegúrate de que el script tenga permisos de ejecución:

chmod +x indexar_todos_los_concursos2.sh

Luego ejecútalo:

./indexar_todos_los_concursos2.sh

Este script realiza automáticamente las siguientes operaciones para cada documento PDF:

Subir el documento al backend

Extraer el texto del PDF

Preprocesar el contenido

Generar embeddings

Indexar el documento en MongoDB

El flujo ejecutado por el script es:

PDF → subida → extracción de texto → preprocesamiento → indexación

Durante la ejecución verás algo como:

🚀 Indexación masiva ANID
📤 Subiendo: documento.pdf
🧾 Extrayendo texto
🧹 Preprocesando
🧠 Indexando

8. Reconstruir índice (opcional)

Si necesitas reconstruir completamente el índice:

curl -X POST "http://127.0.0.1:8090/documentos/indexar?mode=rebuild" \
-H "x-admin-token: super-secret-token"

9. Probar el asistente

Ejemplo de consulta:

curl -X POST "http://127.0.0.1:8090/consulta" \
-H "Content-Type: application/json" \
-d '{"pregunta":"¿Cuál es el objetivo del concurso?"}'

10. Ejemplos de preguntas

Puedes probar consultas como:

¿Cuál es el objetivo del concurso FONDECYT?
¿Quiénes pueden postular?
¿Cuáles son los requisitos de postulación?
¿Cuál es el financiamiento del concurso?
Extrae una frase donde aparezca "RESOLUCIÓN".
Flujo completo del sistema
PDF
 ↓
Subida de documento
 ↓
Extracción de texto
 ↓
Preprocesamiento
 ↓
Segmentación en chunks
 ↓
Embeddings
 ↓
MongoDB
 ↓
Retrieval (RAG)
 ↓
DeepSeek
 ↓
Respuesta generada
