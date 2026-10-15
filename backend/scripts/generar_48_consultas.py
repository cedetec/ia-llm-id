import os
import sys
import json
import random
from pathlib import Path

# Agregar backend al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import PromptTemplate
from app.core.paths import CHROMA_NOMIC_DIR

def generar_consultas():
    print("Iniciando generación de 48 consultas sintéticas...")
    
    # Conectar a la base de datos de Nomic para obtener fragmentos
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://ollama:11434"
    )
    
    vectorstore = Chroma(
        persist_directory=str(CHROMA_NOMIC_DIR),
        embedding_function=embeddings,
        collection_name="anid_nomic"
    )
    
    # Obtener todos los documentos
    # Usaremos el cliente directamente para obtener muestras
    try:
        collection = vectorstore._collection
        count = collection.count()
        print(f"Total de fragmentos en la DB: {count}")
        
        # Para tener variedad, sacaremos chunks al azar
        resultados = collection.get(include=['documents', 'metadatas'])
        documentos = resultados['documents']
        metadatas = resultados['metadatas']
        
    except Exception as e:
        print(f"Error accediendo a Chroma: {e}")
        return

    if count == 0:
        print("La base de datos está vacía.")
        return

    # Seleccionar 48 fragmentos al azar
    indices = random.sample(range(count), min(48, count))
    
    # Preparar el LLM para generar preguntas y respuestas
    llm = ChatOllama(
        model="gemma4:e2b",
        base_url="http://ollama:11434",
        temperature=0.7
    )
    
    # Formato JSON estricto esperado
    prompt = PromptTemplate.from_template(
        "Eres un asistente experto en comprensión lectora. Basado en el siguiente fragmento de texto, "
        "genera una pregunta clara y concisa que pueda ser respondida usando el texto, y luego provee la "
        "respuesta de referencia exacta.\n\n"
        "Fragmento:\n{texto}\n\n"
        "Responde SOLAMENTE en formato JSON con la siguiente estructura (no agregues texto fuera del JSON):\n"
        "{{\n"
        '  "pregunta": "Tu pregunta aquí",\n'
        '  "referencia": "La respuesta de referencia aquí"\n'
        "}}\n"
    )
    
    cadena = prompt | llm
    
    consultas = []
    
    for i, idx in enumerate(indices):
        texto = documentos[idx]
        meta = metadatas[idx]
        nombre_doc = meta.get('source', 'Documento Desconocido')
        
        print(f"\nGenerando consulta {i+1}/48 desde {Path(nombre_doc).name}...")
        
        try:
            respuesta_llm = cadena.invoke({"texto": texto})
            # Extraer JSON de la respuesta
            contenido = respuesta_llm.content
            # Limpiar posible formato markdown
            if "```json" in contenido:
                contenido = contenido.split("```json")[1].split("```")[0].strip()
            elif "```" in contenido:
                contenido = contenido.split("```")[1].strip()
                
            datos = json.loads(contenido)
            
            consultas.append({
                "id": i + 1,
                "documento": Path(nombre_doc).name,
                "pregunta": datos.get("pregunta", ""),
                "referencia": datos.get("referencia", "")
            })
            print("OK.")
            
        except Exception as e:
            print(f"Error generando consulta {i+1}: {e}")
            # Agregar una de fallback
            consultas.append({
                "id": i + 1,
                "documento": Path(nombre_doc).name,
                "pregunta": f"¿De qué trata este fragmento del documento {Path(nombre_doc).name}?",
                "referencia": texto[:200] + "..."
            })
            
    # Guardar en JSON
    ruta_salida = Path("/app/evaluation/48_consultas.json")
    if not ruta_salida.parent.exists():
        try:
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            ruta_salida = Path("/home/cedetec-01/Documents/VIcho/FIU/ia-llm-id-RAG/ia-llm-id-RAG-v2-local/backend/evaluation/48_consultas.json")
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)
            
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(consultas, f, indent=4, ensure_ascii=False)
        
    print(f"\nSe han generado y guardado {len(consultas)} consultas en {ruta_salida}")

if __name__ == "__main__":
    generar_consultas()
