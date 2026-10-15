# Asistente de IA Conversacional para consulta documental de I+D

Prototipo de asistente con inteligencia artificial conversacional para consultar y analizar información sobre instrumentos de financiamiento de Investigación y Desarrollo (I+D). El sistema permite formular preguntas en lenguaje natural sobre un corpus documental compuesto principalmente por convocatorias y bases concursales de la Agencia Nacional de Investigación y Desarrollo (ANID).

El proyecto fue desarrollado como tesis para optar al título de Analista en Computación Científica en la Universidad de Santiago de Chile (USACH).

 **Repositorio:** https://github.com/cedetec/ia-llm-id
 
 **Instancia de producción documentada:** https://iac-id.cedetec.cl/
 
 **Autor:** Vicente Rojas Martínez 
 
 **Profesor guía:** Óscar Rojas Diaz
 
 **Licencia indicada por el proyecto:** MIT

# Características principales

* **Consulta en lenguaje natural:** permite realizar preguntas sobre información contenida en los documentos disponibles en el corpus.
* **Procesamiento documental:** contempla la extracción y normalización de texto, la segmentación en fragmentos y la preparación de documentos para su consulta.
* **Recuperación semántica:** admite las configuraciones basadas en `nomic-embed-text` y `EmbeddingGemma` para representar consultas y fragmentos documentales.
* **Ordenamiento y construcción de contexto:** selecciona fragmentos recuperados y construye el contexto que se entrega al modelo generativo.
* **Generación de respuestas:** utiliza modelos de lenguaje servidos localmente mediante Ollama.
* **Gestión de documentos:** incluye una interfaz para consultar la colección documental, incorporar archivos y realizar operaciones relacionadas con la indexación.
* **Evaluación experimental:** permite evaluar configuraciones de recuperación y generación mediante métricas de eficacia y registrar indicadores técnicos como latencia y mejora de GPU.

# Arquitectura y tecnologías

La implementación combina una interfaz web, servicios backend, una base de datos documental y un servicio de inferencia local. Docker Compose se utiliza para coordinar los contenedores y una red Docker permite la comunicación entre los servicios.

|Componente | Tecnología / servicio | Función|
|-----------|-----------------------|---------|
|Interfaz web|React y Vite|Consulta conversacional, visualización de resultados y gestión documental.|
|API y lógica de aplicación|Python y FastAPI|Expone operaciones mediante una API REST y coordina las funciones del sistema.|
|Recuperación|Servicio backend de recuperación|Recupera y procesa fragmentos candidatos; se expone el puerto `8001` en la configuración documentada.|
|Generación|Servicio backend de generación|Construye la solicitud al modelo y gestiona la generación de respuestas; se expone el puerto `8000`.|
|Ingesta|Servicio backend de ingesta|Aloja las operaciones relacionadas con la preparación e incorporación documental.|
|Almacenamiento documental|MongoDB|Conserva información administrativa asociada a los documentos.|
|Inferencia de modelos|Ollama|Ejecute localmente los modelos de lenguaje y los modelos de representaciòn utilizados.|
|Almacenamiento vectorial|Chroma|Gestiona las estructuras de almacenamiento vectorial usadas por el flujo de recuperación.|
|Despliegue|Docker y Docker Compose|Construcción, ejecución y coordinación de las ejecuciones.|

En el despliegue documnetado, los puertos principales son:

|Servicio | Puerto publicado |
|-----------|-----------------------|
|Frontend|`5173` (puerto del host hacia el puerto`80` del contenedor)|
|Backend de generación|`8000`|
|Backend de recuperación|`8001`|
|Ollama|`11434`|
|MongoDB|`27017`|

La configuración de Docker Compose incluye también un servicio auxiliar para descargar los modelos requeridos por Ollama. Los componentes internos de recuperación, reordenamiento y generación describen responsabilidades del flujo de procesamiento; no todos representan necesariamente servicios desplegados de manera independiente.

# Modelos considerados
## Modelos de representación vectorial

* `nomic-embed-text`
* `EmbeddingGemma`

## Modelos lenguaje

* `mistral:latest`
* `qwen2.5:latest`
* `deepseek-r1-8b`
* `gemma4:e2b`

Los modelos se ejecutan mediante Ollama. La descarga inicial de sus pesos requiere conexión a Internet y puede tardar según el ancho de banda y el almacenamiento disponible.

# Evaluación experimental

La tesis considera varias configuraciones y conjunto de consultas:

* **Experimento principal:** 10 consultas, 2 configuraciones de recuperación y 4 modelos de lenguaje, con un total de 80 ejecuciones.
* **Evaluación multidocumento:** 6 consultas diseñadas para relacionar información de 2 o 3 documentos; se evaluaron 48 combinaciones de recuperación y generación.
* **Comparación global y producción:** se comparó el comportamiento del sistema en dos entornos de hardware.

Entre las métricas de eficacia utilizadas se encuentran:

* **Context Precision:** pertinencia y orden de los fragmentos recupoerados.
* **Context Recall:** cobertura de la información necesaria presente en el contexto recuperado.
* **Faithfulness:** grado en que la respuesta está respaldada por el contexto.**
* **Answer Relevance:** pertinencia de la respuesta respecto de la consulta.**

Tambien se registraron indicadores técnicos, en particular latencia y uso de memoria GPU (VRAM).

# Requisitos previos

* Git
* Docker Engine
* Docker Compose (plugin `docker compose`).
* Espacio de almacenamiento suficiente para las imágenes de contenedor, la base de datos y los modelos descargados.
* Conectividad a Internet durante la descarga inicial de las imágenes y modelos.
* Para la configuración de GPU incluida en el despliegue, un entorno Docker compatible con GPU NVIDIA. Si se utilizará CPU u otra configuración, hay que adaptar la configuración de recursos de Docker Compose.

## Primer Lanzamiento

1. Colocar los archivos PDF en `backend/data/pdfs/`.

2. Levantar contenedores:
```bash
docker compose up -d --build
# En producción: docker compose -f docker-compose.prod.yml up -d --build
```

3. Esperar la descarga de modelos:
```bash
docker compose logs -f ollama-pull-models
```

4. Indexar documentos:
```bash
./ingest.sh
# En producción: ./ingest.sh --prod
```

5. Reiniciar backend para cargar el nuevo índice:
```bash
docker compose restart backend-retrieval backend-generation
# En producción: docker compose -f docker-compose.prod.yml restart backend-retrieval backend-generation
```

## Re-indexación de Documentos

Para indexar nuevos PDFs o cambios en `backend/data/pdfs/`:

```bash
./ingest.sh
docker compose restart backend-retrieval backend-generation

# En producción:
# ./ingest.sh --prod
# docker compose -f docker-compose.prod.yml restart backend-retrieval backend-generation
```
