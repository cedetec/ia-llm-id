# Asistente de Inteligencia Artificial para Consulta y Análisis de Información de I+D

## Descripción del Proyecto

Este proyecto corresponde al desarrollo de un **asistente de inteligencia artificial basado en técnicas de procesamiento de lenguaje natural (NLP)** para la **consulta y análisis de documentos asociados a investigación y desarrollo (I+D)**.

El sistema permite realizar **preguntas en lenguaje natural** sobre documentos institucionales como bases concursales, resoluciones y documentos administrativos, recuperando información relevante desde documentos no estructurados.

Para ello se utiliza una arquitectura basada en **Retrieval-Augmented Generation (RAG)** que combina recuperación de información semántica con modelos de lenguaje.

El sistema está diseñado principalmente para trabajar con documentos públicos asociados a concursos de financiamiento de investigación, como los publicados por **ANID (Agencia Nacional de Investigación y Desarrollo)**.

---

# Objetivo del Proyecto

Desarrollar un asistente basado en inteligencia artificial que permita **consultar y analizar documentos de I+D de forma automática**, facilitando el acceso a información relevante contenida en documentos no estructurados.

El sistema busca apoyar procesos de:

* análisis de bases concursales
* identificación de requisitos de postulación
* identificación de objetivos de programas de financiamiento
* exploración de resoluciones administrativas
* recuperación de citas textuales desde documentos oficiales

---

# Arquitectura del Sistema

El sistema utiliza una arquitectura **RAG (Retrieval-Augmented Generation)** compuesta por varias etapas.

## Flujo general

```
Usuario
   │
   ▼
Consulta en lenguaje natural
   │
   ▼
Detección de intención
   │
   ▼
Recuperación de documentos relevantes (Retrieval)
   │
   ▼
Ranking semántico de fragmentos
   │
   ▼
Construcción de contexto
   │
   ▼
Modelo de lenguaje
   │
   ▼
Respuesta generada
```

---

# Procesamiento de Documentos

Los documentos PDF pasan por un pipeline de procesamiento compuesto por las siguientes etapas:

1. **Carga del documento**
2. **Extracción de texto desde PDF**
3. **Limpieza y normalización de texto**
4. **Detección de secciones jurídicas**
5. **Segmentación del texto en fragmentos**
6. **Generación de embeddings**
7. **Indexación en base de datos**

Cada fragmento se almacena con metadatos que incluyen:

* nombre del documento
* sección detectada
* contenido textual
* embedding semántico

---

# Arquitectura Técnica

El sistema está compuesto por los siguientes componentes.

## Backend

El backend está desarrollado utilizando:

* **Python**
* **FastAPI**
* **MongoDB**

Sus funciones principales son:

* ingestión de documentos
* extracción de texto
* preprocesamiento
* generación de embeddings
* recuperación semántica
* ranking de fragmentos
* generación de respuestas

---

## Sistema de Recuperación (Retrieval)

El sistema de recuperación utiliza un enfoque híbrido que combina:

* **búsqueda semántica mediante embeddings**
* **búsqueda léxica basada en tokens**
* **heurísticas jurídicas específicas**

El ranking de fragmentos considera:

* similitud semántica
* coincidencia de palabras clave
* detección de secciones relevantes
* heurísticas específicas de documentos jurídicos

---

# Dataset Utilizado

El sistema utiliza documentos públicos disponibles en:

* concursos de investigación
* bases concursales
* resoluciones administrativas
* documentos técnicos

Principalmente provenientes de:

**Agencia Nacional de Investigación y Desarrollo (ANID)**

Los documentos incluyen:

* bases concursales
* resoluciones exentas
* documentos institucionales

---

# Estructura del Proyecto

```
backend
│
├── api
│   └── routes
│
├── services
│   ├── retrieval
│   ├── preprocessing
│   ├── consulta
│   └── embedding
│
├── archived_scripts
│
└── main.py
```

---

# Ejemplos de Consultas

El sistema permite responder preguntas como:

* ¿Cuál es el objetivo del concurso InES Género?
* ¿Quiénes pueden postular al concurso FONDECYT Regular?
* ¿Cuáles son los requisitos de postulación?
* ¿Cuál es el financiamiento del concurso?
* ¿En qué resolución se aprueban las bases?
* Extrae una frase textual donde aparezca "RESOLUCIÓN".

---

# Uso del Sistema

## Iniciar el servidor

```
uvicorn backend.main:app --reload
```

---

## Indexar documentos

```
POST /documentos/indexar
```

---

## Realizar consultas

```
POST /consulta
```

Ejemplo:

```
¿Cuál es el objetivo del concurso FONDECYT Regular?
```

---

# Contribución Académica

Este proyecto contribuye al desarrollo de herramientas basadas en inteligencia artificial para la **gestión de información en sistemas de investigación y desarrollo (I+D)**.

La solución propuesta permite transformar grandes volúmenes de documentos no estructurados en **conocimiento accesible mediante consultas en lenguaje natural**.

Esto facilita:

* el acceso a información institucional
* el análisis de programas de financiamiento
* el apoyo a procesos de investigación

---

# Autor

Vicente Rojas Martínez

Proyecto de Tesis
Asistente de Inteligencia Artificial para Gestión y Seguimiento de Información de I+D
