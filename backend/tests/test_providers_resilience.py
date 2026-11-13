import pytest
from app.services.embedding_provider import MockEmbeddingProvider
from app.services.ai_provider import OpenAIProvider
from app.services.document_processor import DocumentProcessor
from app.services.evaluator import EvaluationEngine

def test_mock_embedding_provider_consistency():
    embedder = MockEmbeddingProvider(dimension=1536)
    vec1 = embedder.embed_text("GroundTruth.ai provides evidence verification.")
    vec2 = embedder.embed_text("GroundTruth.ai provides evidence verification.")
    assert len(vec1) == 1536
    assert vec1 == vec2

def test_openai_provider_timeout_fallback():
    provider = OpenAIProvider(api_key="invalid-key-for-test", model="gpt-4o-mini")
    passages = [
        {"id": "p1", "document_id": "d1", "source_filename": "info.txt", "page_number": 1, "content": "Database retention period is 90 days."}
    ]
    out = provider.generate_grounded_answer("What is the retention period?", passages)
    assert out["status"] == "answered"
    assert "90 days" in out["answer"]

def test_text_cleaner_resilience():
    dirty_text = "Line 1\r\n\r\n\r\nLine 2 \xa0\xa0 with   excessive \t spaces.\x00\x01"
    cleaned = DocumentProcessor.clean_text(dirty_text)
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned
    assert "\x00" not in cleaned
    assert "\x01" not in cleaned

def test_evaluation_benchmark_execution(db_session):
    benchmark_out = EvaluationEngine.run_benchmark(db=db_session, sample_size=4)
    metrics = benchmark_out["metrics"]
    results = benchmark_out["results"]

    assert metrics["total_cases"] == 4
    assert metrics["retrieval_recall_at_k"] >= 0.0
    assert metrics["citation_support_rate"] >= 0.0
    assert metrics["mean_latency_ms"] > 0.0
    assert len(results) == 4
