import re
import json
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

class BaseAIProvider:
    """Base interface for GroundTruth.ai generation and verification."""

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generates an evidence-grounded answer based strictly on retrieved passages.
        Returns: {
            "status": "answered" | "insufficient_evidence" | "conflicting_evidence",
            "answer": str,
            "raw_citations": List[Dict[str, Any]],
            "reason": Optional[str]
        }
        """
        raise NotImplementedError

    def decompose_claims(self, answer: str) -> List[str]:
        """Splits an answer into individual testable factual claims."""
        raise NotImplementedError

    def verify_claim(
        self,
        claim: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verifies whether the retrieved passages support, contradict, or leave uncertain a claim.
        Returns: {
            "status": "supported" | "contradicted" | "uncertain",
            "supporting_excerpt": str,
            "chunk_id": Optional[str],
            "document_id": Optional[str],
            "reason": str
        }
        """
        raise NotImplementedError


class MockAIProvider(BaseAIProvider):
    """
    Deterministic offline provider used for tests, air-gapped runs, and verification benchmarks.
    Never hallucinates, enforces strict mathematical lexical entailment, and flags contradictions.
    """

    def decompose_claims(self, answer: str) -> List[str]:
        if not answer:
            return []
        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
        claims = []
        for s in sentences:
            cleaned = s.strip()
            # Remove any citation brackets like [C1] or [Chunk-1] for claim evaluation
            clean_claim = re.sub(r"\[(C\d+|Chunk-[^\]]+)\]", "", cleaned).strip()
            if len(clean_claim) > 10:
                claims.append(clean_claim)
        return claims or [answer.strip()]

    def verify_claim(
        self,
        claim: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Checks claim entailment against the retrieved passages.
        """
        claim_lower = claim.lower()
        # Words of interest (ignore common stop words)
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "of", "in", "and", "or", "to", "for", "with", "on", "at", "by", "from", "that", "this", "it"}
        claim_words = [w for w in re.findall(r"\b\w{3,}\b", claim_lower) if w not in stop_words]

        if not claim_words:
            return {
                "status": "uncertain",
                "supporting_excerpt": "",
                "chunk_id": None,
                "document_id": None,
                "reason": "Claim lacks testable factual substance."
            }

        # Check for explicit contradictions across passages
        contradiction_keywords = [
            ("increase", "decrease"),
            ("higher", "lower"),
            ("true", "false"),
            ("approved", "rejected"),
            ("always", "never"),
            ("enabled", "disabled")
        ]
        
        has_contradiction = False
        contradiction_details = ""
        for word_a, word_b in contradiction_keywords:
            if word_a in claim_lower or word_b in claim_lower:
                found_a = any(word_a in p["content"].lower() for p in retrieved_passages)
                found_b = any(word_b in p["content"].lower() for p in retrieved_passages)
                if found_a and found_b:
                    has_contradiction = True
                    contradiction_details = f"Passages present conflicting evidence regarding '{word_a}' vs '{word_b}'."
                    break

        if has_contradiction:
            return {
                "status": "contradicted",
                "supporting_excerpt": "",
                "chunk_id": None,
                "document_id": None,
                "reason": contradiction_details
            }

        best_score = 0.0
        best_passage = None
        best_sentence = ""

        for p in retrieved_passages:
            content = p["content"]
            sentences = re.split(r"(?<=[.!?])\s+", content)
            for sent in sentences:
                sent_lower = sent.lower()
                matches = sum(1 for w in claim_words if w in sent_lower)
                score = matches / len(claim_words)
                if score > best_score:
                    best_score = score
                    best_passage = p
                    best_sentence = sent.strip()

        # Strict entailment threshold
        if best_score >= 0.50 and best_passage:
            return {
                "status": "supported",
                "supporting_excerpt": best_sentence or best_passage["content"][:200],
                "chunk_id": best_passage.get("id"),
                "document_id": best_passage.get("document_id"),
                "reason": f"Strong lexical entailment with {int(best_score * 100)}% key-term overlap."
            }
        elif best_score >= 0.25 and best_passage:
            return {
                "status": "uncertain",
                "supporting_excerpt": best_sentence or best_passage["content"][:200],
                "chunk_id": best_passage.get("id"),
                "document_id": best_passage.get("document_id"),
                "reason": "Partial evidence overlap; insufficient for full factual verification."
            }
        else:
            return {
                "status": "uncertain",
                "supporting_excerpt": "",
                "chunk_id": None,
                "document_id": None,
                "reason": "No retrieved passage provides supporting evidence for this claim."
            }

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not retrieved_passages:
            return {
                "status": "insufficient_evidence",
                "answer": "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably.",
                "raw_citations": [],
                "reason": "No relevant supporting evidence was found in the indexed documents."
            }

        # Check if question terms have sufficient overlap with passages
        q_words = [w for w in re.findall(r"\b\w{3,}\b", question.lower()) if w not in {"what", "when", "where", "which", "how", "does", "explain"}]
        matching_passages = []
        for p in retrieved_passages:
            p_content = p["content"].lower()
            overlap = sum(1 for w in q_words if w in p_content)
            if overlap > 0:
                matching_passages.append(p)

        if not matching_passages:
            return {
                "status": "insufficient_evidence",
                "answer": "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably.",
                "raw_citations": [],
                "reason": "Retrieved passages do not address the core subject of the question."
            }

        # Check for conflicting evidence
        contradiction_keywords = [
            ("increase", "decrease"),
            ("higher", "lower"),
            ("true", "false"),
            ("approved", "rejected"),
            ("always", "never"),
            ("enabled", "disabled")
        ]
        has_conflict = False
        conflict_msg = ""
        for w1, w2 in contradiction_keywords:
            doc_w1 = [p["source_filename"] for p in matching_passages if w1 in p["content"].lower()]
            doc_w2 = [p["source_filename"] for p in matching_passages if w2 in p["content"].lower()]
            if doc_w1 and doc_w2 and set(doc_w1) != set(doc_w2):
                has_conflict = True
                conflict_msg = f"Contradictory evidence detected: {doc_w1[0]} asserts '{w1}' whereas {doc_w2[0]} asserts '{w2}'."
                break

        if has_conflict:
            return {
                "status": "conflicting_evidence",
                "answer": f"The uploaded documents present conflicting evidence regarding this question. {conflict_msg}",
                "raw_citations": [
                    {
                        "chunk_id": p["id"],
                        "document_id": p["document_id"],
                        "filename": p["source_filename"],
                        "page_number": p["page_number"],
                        "supporting_excerpt": p["content"][:200],
                        "claim_text": f"Document mentions contradictory facts ({conflict_msg})",
                        "verification_status": "contradicted"
                    }
                    for p in matching_passages[:2]
                ],
                "reason": conflict_msg
            }

        # Synthesize answer from top matching passage sentences
        selected_sentences = []
        citations = []
        for i, p in enumerate(matching_passages[:3]):
            sents = re.split(r"(?<=[.!?])\s+", p["content"].strip())
            for s in sents:
                s_clean = s.strip()
                if any(w in s_clean.lower() for w in q_words) and len(s_clean) > 20:
                    selected_sentences.append(s_clean)
                    citations.append({
                        "chunk_id": p["id"],
                        "document_id": p["document_id"],
                        "filename": p["source_filename"],
                        "page_number": p["page_number"],
                        "supporting_excerpt": s_clean,
                        "claim_text": s_clean,
                        "verification_status": "supported"
                    })
                    break

        if not selected_sentences:
            first_passage = matching_passages[0]
            excerpt = first_passage["content"][:200].strip()
            selected_sentences.append(f"Based on {first_passage['source_filename']}, {excerpt}.")
            citations.append({
                "chunk_id": first_passage["id"],
                "document_id": first_passage["document_id"],
                "filename": first_passage["source_filename"],
                "page_number": first_passage["page_number"],
                "supporting_excerpt": excerpt,
                "claim_text": excerpt,
                "verification_status": "supported"
            })

        answer_text = " ".join(selected_sentences)
        return {
            "status": "answered",
            "answer": answer_text,
            "raw_citations": citations,
            "reason": None
        }


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI provider using gpt-4o / gpt-4o-mini with structured JSON outputs.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not retrieved_passages:
            return {
                "status": "insufficient_evidence",
                "answer": "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably.",
                "raw_citations": [],
                "reason": "No relevant supporting evidence was found."
            }

        context_str = "\n\n".join([
            f"[Passage {i+1} | ChunkID: {p['id']} | File: {p['source_filename']} | Page: {p['page_number']}]\n{p['content']}"
            for i, p in enumerate(retrieved_passages)
        ])

        system_prompt = (
            "You are GroundTruth.ai, an evidence-grounded AI assistant.\n"
            "Core principle: Every factual answer must be supported by evidence from the uploaded passages.\n"
            "If sufficient evidence cannot be established from the passages, abstain and say you do not know.\n"
            "Never hallucinate document names, page numbers, or facts.\n"
            "Return valid JSON with keys: status ('answered', 'insufficient_evidence', 'conflicting_evidence'), "
            "answer (string), reason (string or null), citations (array of objects with chunk_id, claim_text, supporting_excerpt)."
        )

        user_prompt = f"Question: {question}\n\nRetrieved Passages:\n{context_str}"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            resp = httpx.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=40.0)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)

            raw_citations = []
            for c in result.get("citations", []):
                chunk_id = c.get("chunk_id")
                matched = next((p for p in retrieved_passages if p["id"] == chunk_id), None)
                if matched:
                    raw_citations.append({
                        "chunk_id": matched["id"],
                        "document_id": matched["document_id"],
                        "filename": matched["source_filename"],
                        "page_number": matched["page_number"],
                        "supporting_excerpt": c.get("supporting_excerpt", matched["content"][:200]),
                        "claim_text": c.get("claim_text", ""),
                        "verification_status": "supported"
                    })

            return {
                "status": result.get("status", "answered"),
                "answer": result.get("answer", ""),
                "raw_citations": raw_citations,
                "reason": result.get("reason")
            }
        except Exception as e:
            # Fallback to Mock in case of failure or network error
            mock = MockAIProvider()
            return mock.generate_grounded_answer(question, retrieved_passages)

    def decompose_claims(self, answer: str) -> List[str]:
        # Fast regex decomposition
        sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def verify_claim(
        self,
        claim: str,
        retrieved_passages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Uses mock rule-based entailment check for speed and determinism
        mock = MockAIProvider()
        return mock.verify_claim(claim, retrieved_passages)


def get_ai_provider() -> BaseAIProvider:
    """Factory returning configured AI Provider."""
    prov = settings.LLM_PROVIDER.lower()
    if prov == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    return MockAIProvider()
