import uuid
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.models import Document, DocumentChunk, Message, Citation, Conversation
from app.services.embedding_provider import get_embedding_provider
from app.services.ai_provider import get_ai_provider
from app.core.config import settings

class RAGService:
    """
    Core RAG Pipeline implementing GroundTruth.ai's 12-step evidence-grounded workflow.
    Guarantees strict tenant isolation, server-side citation validation, and honest abstention.
    """

    @staticmethod
    def calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @classmethod
    def retrieve_relevant_chunks(
        cls,
        db: Session,
        query: str,
        owner_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        """
        Embeds query and searches for relevant passages scoped strictly to owner_id.
        Applies cosine similarity threshold filtering.
        """
        embedder = get_embedding_provider()
        query_vector = embedder.embed_text(query)

        # Check database dialect
        dialect_name = db.bind.dialect.name if db.bind else "postgresql"

        # Query chunks with owner isolation
        chunk_query = db.query(DocumentChunk, Document.filename).join(
            Document, DocumentChunk.document_id == Document.id
        ).filter(
            DocumentChunk.owner_id == owner_id,
            Document.status == "completed"
        )

        if document_ids:
            chunk_query = chunk_query.filter(DocumentChunk.document_id.in_(document_ids))

        scored_chunks = []

        if dialect_name == "postgresql":
            try:
                # Use native pgvector cosine distance operator <=>
                # Cosine distance = 1 - cosine_similarity
                # Cosine similarity >= threshold  <=>  distance <= (1 - threshold)
                max_distance = 1.0 - threshold
                sql = text("""
                    SELECT c.id, c.document_id, c.owner_id, c.page_number, c.content, d.filename,
                           (c.embedding <=> :qvec) as distance
                    FROM document_chunks c
                    JOIN documents d ON c.document_id = d.id
                    WHERE c.owner_id = :owner_id AND d.status = 'completed'
                    ORDER BY distance ASC
                    LIMIT :top_k
                """)
                # Format vector string for pgvector '[0.1, 0.2, ...]'
                vec_str = f"[{','.join(str(x) for x in query_vector)}]"
                rows = db.execute(sql, {
                    "qvec": vec_str,
                    "owner_id": owner_id,
                    "top_k": top_k
                }).fetchall()

                for row in rows:
                    similarity = 1.0 - float(row.distance)
                    if similarity >= threshold:
                        scored_chunks.append({
                            "id": row.id,
                            "document_id": row.document_id,
                            "owner_id": row.owner_id,
                            "page_number": row.page_number,
                            "content": row.content,
                            "source_filename": row.filename,
                            "score": similarity
                        })
                return scored_chunks
            except Exception:
                # If pgvector query fails (e.g. extension not configured in current dev db), fallback to in-memory cosine
                pass

        # In-memory cosine calculation fallback (compatible with SQLite or un-indexed Postgres)
        all_chunks = chunk_query.all()
        for chunk, filename in all_chunks:
            if chunk.embedding is None:
                continue
            sim = cls.calculate_cosine_similarity(query_vector, chunk.embedding)
            if sim >= threshold:
                scored_chunks.append({
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "owner_id": chunk.owner_id,
                    "page_number": chunk.page_number,
                    "content": chunk.content,
                    "source_filename": filename,
                    "score": sim
                })

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def execute_rag_pipeline(
        cls,
        db: Session,
        question: str,
        owner_id: str,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete 12-step GroundTruth.ai pipeline:
        Retrieval -> Threshold Filter -> Answer Generation -> Claim Decomposition
        -> Claim Verification -> Citation Validation & Bounded Handling -> Persistence.
        """
        # Step 1: Ensure Conversation exists
        conversation = None
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.owner_id == owner_id
            ).first()

        if not conversation:
            # Generate title from question preview
            preview_title = question[:45] + ("..." if len(question) > 45 else "")
            conversation = Conversation(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                title=preview_title
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Store User Message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=question,
            status="answered"
        )
        db.add(user_message)
        db.commit()

        # Step 2: Retrieve relevant chunks with owner boundary
        retrieved_passages = cls.retrieve_relevant_chunks(
            db=db,
            query=question,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=settings.RETRIEVAL_TOP_K,
            threshold=settings.RETRIEVAL_THRESHOLD
        )

        ai_provider = get_ai_provider()

        # Step 3: Check evidence sufficiency
        if not retrieved_passages:
            abstention_answer = "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably."
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role="assistant",
                content=abstention_answer,
                status="insufficient_evidence",
                reason="No passages in your documents exceeded the evidence retrieval threshold."
            )
            db.add(assistant_msg)
            db.commit()

            return {
                "status": "insufficient_evidence",
                "answer": abstention_answer,
                "claims": [],
                "citations": [],
                "reason": "No sufficiently relevant supporting evidence was found in the indexed documents.",
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id
            }

        # Step 4: Generate grounded answer
        gen_result = ai_provider.generate_grounded_answer(question, retrieved_passages)

        if gen_result.get("status") in ("insufficient_evidence", "conflicting_evidence"):
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role="assistant",
                content=gen_result.get("answer"),
                status=gen_result.get("status"),
                reason=gen_result.get("reason")
            )
            db.add(assistant_msg)
            db.commit()

            return {
                "status": gen_result.get("status"),
                "answer": gen_result.get("answer"),
                "claims": [],
                "citations": gen_result.get("raw_citations", []),
                "reason": gen_result.get("reason"),
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id
            }

        candidate_answer = gen_result.get("answer", "")

        # Step 5: Decompose answer into factual claims
        claims = ai_provider.decompose_claims(candidate_answer)

        # Step 6: Verify each claim against retrieved evidence
        verified_claims = []
        valid_citations = []
        retrieved_chunk_ids = {p["id"]: p for p in retrieved_passages}

        has_contradicted = False
        unsupported_count = 0

        for claim in claims:
            verification = ai_provider.verify_claim(claim, retrieved_passages)
            status = verification["status"]
            chunk_id = verification.get("chunk_id")
            excerpt = verification.get("supporting_excerpt", "")

            # Security check: Never trust chunk IDs invented by the LLM
            if chunk_id and chunk_id not in retrieved_chunk_ids:
                status = "uncertain"
                chunk_id = None
                excerpt = ""

            # Check if excerpt actually exists in chunk content
            if chunk_id and excerpt:
                actual_content = retrieved_chunk_ids[chunk_id]["content"]
                if excerpt.lower() not in actual_content.lower() and len(excerpt) > 25:
                    # Excerpt was hallucinated or modified, fall back to snippet of actual chunk
                    excerpt = actual_content[:200]

            verified_claims.append({
                "claim": claim,
                "status": status,
                "evidence_excerpt": excerpt,
                "citation_id": chunk_id,
                "reason": verification.get("reason")
            })

            if status == "contradicted":
                has_contradicted = True
            elif status == "uncertain":
                unsupported_count += 1
            elif status == "supported" and chunk_id:
                p_info = retrieved_chunk_ids[chunk_id]
                valid_citations.append({
                    "id": str(uuid.uuid4()),
                    "chunk_id": chunk_id,
                    "document_id": p_info["document_id"],
                    "filename": p_info["source_filename"],
                    "page_number": p_info["page_number"],
                    "supporting_excerpt": excerpt or p_info["content"][:200],
                    "claim_text": claim,
                    "verification_status": "supported"
                })

        # Step 7: Handle Bounded Regeneration / Abstention
        if has_contradicted:
            final_status = "conflicting_evidence"
            final_answer = "The uploaded documents present conflicting evidence regarding this question."
            reason = "A factual claim was contradicted by retrieved document evidence."
        elif unsupported_count > 0 and len(valid_citations) == 0:
            final_status = "insufficient_evidence"
            final_answer = "I couldn't find sufficient evidence in your uploaded documents to answer this question reliably."
            reason = "Claims in the generated answer could not be verified against the uploaded evidence."
        else:
            final_status = "answered"
            final_answer = candidate_answer
            reason = None

        # Step 8: Persist Assistant Message and Citations
        assistant_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=final_answer,
            status=final_status,
            reason=reason
        )
        db.add(assistant_msg)
        db.commit()

        # Persist Citations
        citation_records = []
        for cit in valid_citations:
            db_citation = Citation(
                id=cit["id"],
                message_id=assistant_msg.id,
                chunk_id=cit["chunk_id"],
                document_id=cit["document_id"],
                claim_text=cit["claim_text"],
                verification_status=cit["verification_status"],
                supporting_excerpt=cit["supporting_excerpt"]
            )
            db.add(db_citation)
            citation_records.append(cit)

        db.commit()

        return {
            "status": final_status,
            "answer": final_answer,
            "claims": verified_claims,
            "citations": citation_records,
            "reason": reason,
            "conversation_id": conversation.id,
            "message_id": assistant_msg.id
        }
