# LLM/response/response_generation_service.py

import requests
from fastapi import HTTPException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from LLM.prompts.system_prompt import SYSTEM_PROMPT

def generar_respuesta(llm, pregunta, rag_name, modelo=None):
    """
    1. Pide contexto al microservicio de Retrieval (puerto 8001).
    2. Forma el prompt de LangChain y pide generación a Ollama.
    """
    
    # 1. Pedir contexto al Retrieval Service
    try:
        payload = {
            "pregunta": pregunta,
            "rag": rag_name,
            "modelo": modelo
        }
        # El retrieval service corre en backend-retrieval:8001 en Docker
        response = requests.post("http://backend-retrieval:8001/retrieve", json=payload, timeout=60)
        response.raise_for_status()
        retrieval_data = response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comunicándose con el servicio de Retrieval: {str(e)}"
        )

    context_text = retrieval_data.get("context_text", "")
    context_docs_raw = retrieval_data.get("context", [])
    
    # Reconstruir objetos Document para compatibilidad
    documentos = [
        Document(page_content=doc["page_content"], metadata=doc["metadata"])
        for doc in context_docs_raw
    ]

    # 2. Formar prompt y generar
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Pregunta:\n{input}\nResponde únicamente en español.\nNo traduzcas la pregunta al inglés.\nUtiliza solamente el contexto entregado.")
    ])
    
    mensajes = prompt.invoke({
        "context": context_text,
        "input": pregunta
    })
    
    llm_response = llm.invoke(mensajes)

    respuesta = {
        "answer": llm_response.content,
        "context": documentos,
        "context_text": context_text,
        "contextos_ragas": retrieval_data.get("contextos_ragas", [])
    }

    return respuesta
