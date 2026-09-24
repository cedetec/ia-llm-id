# LLM/evaluation/rag_metrics.py

from LLM.evaluation.latency_metrics import (
    LatencyMetrics
)

from LLM.evaluation.memory_metrics import (
    MemoryMetrics
)

from LLM.evaluation.retrieval_metrics import (
    RetrievalMetrics
)

from LLM.evaluation.rerank_metrics import (
    RerankMetrics
)

from LLM.evaluation.answer_metrics import (
    AnswerMetrics
)


class RAGMetrics:

    def __init__(self):

        self.latency = LatencyMetrics()

        self.memory = MemoryMetrics()

        self.retrieval = RetrievalMetrics()

        self.rerank = RerankMetrics()

        self.answer = AnswerMetrics()