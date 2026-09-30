# LLM/evaluation/rag_metrics.py

from RAG.evaluation.latency_metrics import (
    LatencyMetrics
)

from RAG.evaluation.memory_metrics import (
    MemoryMetrics
)

from RAG.evaluation.retrieval_metrics import (
    RetrievalMetrics
)

from RAG.evaluation.rerank_metrics import (
    RerankMetrics
)

from RAG.evaluation.answer_metrics import (
    AnswerMetrics
)


class RAGMetrics:

    def __init__(self):

        self.latency = LatencyMetrics()

        self.memory = MemoryMetrics()

        self.retrieval = RetrievalMetrics()

        self.rerank = RerankMetrics()

        self.answer = AnswerMetrics()