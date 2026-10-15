import sys
import os

# Asegurar que python encuentre el módulo LLM y app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.indexing.indexing_service import indexar_documentos

if __name__ == "__main__":
    print("Iniciando indexación de documentos...")
    indexar_documentos()
    print("Indexación finalizada exitosamente.")
