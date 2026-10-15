import os
import sys
import json
import time
from pathlib import Path

# Agregar backend al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.rag.rag_service import RAGService
from RAG.startup.startup_service import crear_rag_service
from RAG.evaluation.ragas_metrics import RagasMetrics
from app.core.paths import CHROMA_NOMIC_DIR, CHROMA_GEMMA_DIR

# ============================================================
# CONFIGURACIÓN
# ============================================================

MODELOS_LLM = [
    "mistral:latest",
    "qwen2.5:latest",
    "deepseek-r1:8b",
    "gemma4:e2b"
]

RAGS = [
    {
        "nombre": "NOMIC",
        "embedding_model": "nomic-embed-text",
        "persist_directory": CHROMA_NOMIC_DIR,
        "collection_name": "anid_nomic"
    },
    {
        "nombre": "EMBEDDINGGEMMA",
        "embedding_model": "embeddinggemma",
        "persist_directory": CHROMA_GEMMA_DIR,
        "collection_name": "anid_gemma"
    }
]

# Rutas de Checkpoint
RUTA_CONSULTAS = Path("/app/evaluation/48_consultas.json")
RUTA_CHECKPOINT = Path("/app/evaluation/results/evaluacion_secuencial_48.json")

# ============================================================
# UTILIDADES DE CHECKPOINT
# ============================================================

def cargar_json(ruta):
    if not ruta.exists():
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_json(ruta, datos):
    if not ruta.parent.exists():
        ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def obtener_registro_contexto(resultados, consulta_id, rag_nombre):
    for r in resultados:
        if r.get("tipo") == "context" and r["consulta_id"] == consulta_id and r["rag"] == rag_nombre:
            return r
    return None

def obtener_registro_llm(resultados, consulta_id, rag_nombre, modelo_llm):
    for r in resultados:
        if r.get("tipo") == "llm" and r["consulta_id"] == consulta_id and r["rag"] == rag_nombre and r["modelo_llm"] == modelo_llm:
            return r
    return None

def warm_up_modelos(rag_service, modelo_llm):
    print(f"\n[WARM-UP] Cargando modelo LLM '{modelo_llm}' en memoria...")
    rag_service.cambiar_modelo(modelo_llm)
    try:
        _ = rag_service.invoke(
            pregunta="Hola, esto es un mensaje de prueba para cargar en memoria.",
            documento=None,
            documentos_relevantes=None
        )
        print("[WARM-UP] Modelos cargados exitosamente.")
    except Exception as e:
        print(f"[WARM-UP] Advertencia: {e}")

# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    print("=" * 80)
    print(" BENCHMARK SECUENCIAL CON CHECKPOINTING")
    print("=" * 80)
    
    if not RUTA_CONSULTAS.exists():
        print(f"[ERROR] No se encontró el archivo de consultas: {RUTA_CONSULTAS}")
        return
        
    consultas = cargar_json(RUTA_CONSULTAS)
    print(f"Consultas cargadas: {len(consultas)}")
    
    resultados = cargar_json(RUTA_CHECKPOINT)
    if resultados:
        print(f"[RESUME] Checkpoint encontrado con {len(resultados)} registros procesados.")
    else:
        print("[INIT] Iniciando nuevo benchmark.")

    evaluador = RagasMetrics()
    
    # Cache temporal para no hacer retrieval múltiples veces por la misma query+RAG
    cache_contextos = {}

    for configuracion_rag in RAGS:
        nombre_rag = configuracion_rag["nombre"]
        print("\n" + "=" * 80)
        print(f" RAG: {nombre_rag}")
        print("=" * 80)
        
        rag_service = crear_rag_service(
            embedding_model=configuracion_rag["embedding_model"],
            persist_directory=configuracion_rag["persist_directory"],
            collection_name=configuracion_rag["collection_name"]
        )
        
        # -------------------------------------------------------------
        # FASE 1: EVALUAR CONTEXTO (Métricas de Embeddings puras)
        # -------------------------------------------------------------
        print(f"\n--- FASE 1: Evaluación de Contexto ({nombre_rag}) ---")
        rag_service.cambiar_modelo(MODELOS_LLM[0]) # Dummy model for retrieval
        
        for c in consultas:
            c_id = c["id"]
            registro = obtener_registro_contexto(resultados, c_id, nombre_rag)
            
            if registro is not None and registro.get("completado", False):
                # Ya fue procesado
                cache_contextos[f"{nombre_rag}_{c_id}"] = registro["contextos_ragas"]
                continue
                
            print(f"\n[RAG: {nombre_rag}] Recuperando contexto para consulta {c_id}...")
            res = rag_service.invoke(
                pregunta=c["pregunta"],
                documento=c["documento"],
                documentos_relevantes=None
            )
            
            contextos = res["contextos_ragas"]
            cache_contextos[f"{nombre_rag}_{c_id}"] = contextos
            
            try:
                print(f"Evaluando Context Recall...")
                ctx_recall = evaluador.evaluar_metrica("context_recall", c["pregunta"], "N/A", contextos, c["referencia"])
                print(f"Evaluando Context Precision...")
                ctx_prec = evaluador.evaluar_metrica("context_precision", c["pregunta"], "N/A", contextos, c["referencia"])
            except Exception as e:
                print(f"[ERROR] RAGAS Context: {e}")
                ctx_recall, ctx_prec = None, None
                
            nuevo_registro = {
                "tipo": "context",
                "consulta_id": c_id,
                "rag": nombre_rag,
                "pregunta": c["pregunta"],
                "contextos_ragas": contextos,
                "metricas": {
                    "context_recall": ctx_recall,
                    "context_precision": ctx_prec
                },
                "completado": True
            }
            
            # Remover si existía uno incompleto y guardar
            resultados = [r for r in resultados if not (r.get("tipo") == "context" and r["consulta_id"] == c_id and r["rag"] == nombre_rag)]
            resultados.append(nuevo_registro)
            guardar_json(RUTA_CHECKPOINT, resultados)
            print(f"[CHECKPOINT] Contexto para consulta {c_id} guardado.")

        # -------------------------------------------------------------
        # FASE 2: EVALUAR LLMs (Generación y Latencia)
        # -------------------------------------------------------------
        for modelo_llm in MODELOS_LLM:
            print("\n" + "-" * 80)
            print(f" FASE 2A: GENERACIÓN LLM [{modelo_llm}] con RAG [{nombre_rag}]")
            print("-" * 80)
            
            # Verificar si todas las respuestas ya fueron generadas
            generados = sum(1 for c in consultas if obtener_registro_llm(resultados, c["id"], nombre_rag, modelo_llm) is not None and obtener_registro_llm(resultados, c["id"], nombre_rag, modelo_llm).get("respuesta"))
            if generados < len(consultas):
                warm_up_modelos(rag_service, modelo_llm)
            
            for c in consultas:
                c_id = c["id"]
                registro = obtener_registro_llm(resultados, c_id, nombre_rag, modelo_llm)
                
                # Si ya tenemos la respuesta (incluso si completado es False), saltamos la generación
                if registro is not None and registro.get("respuesta"):
                    continue
                    
                print(f"\n[Generación pura] Consulta {c_id}/{len(consultas)}...")
                
                # Inferencia cronometrada en memoria SIN interrupciones de Ragas
                start = time.perf_counter()
                res = rag_service.invoke(
                    pregunta=c["pregunta"],
                    documento=c["documento"],
                    documentos_relevantes=None
                )
                latencia = time.perf_counter() - start
                print(f"Latencia (Inferencia pura): {latencia:.4f} s")
                
                respuesta_llm = res["answer"]
                
                nuevo_registro = {
                    "tipo": "llm",
                    "consulta_id": c_id,
                    "rag": nombre_rag,
                    "modelo_llm": modelo_llm,
                    "pregunta": c["pregunta"],
                    "respuesta": respuesta_llm,
                    "latencia_s": round(latencia, 4),
                    "metricas": {},
                    "completado": False
                }
                
                resultados = [r for r in resultados if not (r.get("tipo") == "llm" and r["consulta_id"] == c_id and r["rag"] == nombre_rag and r["modelo_llm"] == modelo_llm)]
                resultados.append(nuevo_registro)
                guardar_json(RUTA_CHECKPOINT, resultados)
            
            print("\n" + "-" * 80)
            print(f" FASE 2B: EVALUACIÓN RAGAS [{modelo_llm}] con RAG [{nombre_rag}]")
            print("-" * 80)
            
            for c in consultas:
                c_id = c["id"]
                registro = obtener_registro_llm(resultados, c_id, nombre_rag, modelo_llm)
                
                if registro is not None and registro.get("completado", False):
                    continue
                    
                print(f"\n[Evaluación Ragas] Consulta {c_id}/{len(consultas)}...")
                respuesta_llm = registro["respuesta"]
                contextos = cache_contextos.get(f"{nombre_rag}_{c_id}")
                
                try:
                    print("Evaluando Faithfulness...")
                    faith = evaluador.evaluar_metrica("faithfulness", c["pregunta"], respuesta_llm, contextos, c["referencia"])
                    print("Evaluando Answer Relevancy...")
                    ans_rel = evaluador.evaluar_metrica("answer_relevancy", c["pregunta"], respuesta_llm, contextos, c["referencia"])
                except Exception as e:
                    print(f"[ERROR] RAGAS Gen: {e}")
                    faith, ans_rel = None, None
                
                registro["metricas"]["faithfulness"] = faith
                registro["metricas"]["answer_relevancy"] = ans_rel
                registro["completado"] = True
                
                resultados = [r for r in resultados if not (r.get("tipo") == "llm" and r["consulta_id"] == c_id and r["rag"] == nombre_rag and r["modelo_llm"] == modelo_llm)]
                resultados.append(registro)
                guardar_json(RUTA_CHECKPOINT, resultados)
                print(f"[CHECKPOINT] Evaluación LLM completada y guardada para consulta {c_id}.")

    print("\n" + "=" * 80)
    print(" BENCHMARK TOTALMENTE COMPLETADO")
    print("=" * 80)
    print(f"Resultados finales guardados en: {RUTA_CHECKPOINT}")

if __name__ == "__main__":
    main()
