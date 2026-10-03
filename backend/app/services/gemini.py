import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.config import settings
from app.services.vector_store import SearchResult

logger = logging.getLogger("ragmate.gemini")

SAFE_FALLBACK_ANSWER = (
    "I could not find sufficient information in the uploaded documents to answer this question."
)

SYSTEM_PROMPT_TEMPLATE = """You are an intelligent document assistant.
Your task is to answer the user's question using exclusively the provided document context excerpts.

Strict Grounding Guidelines:
1. Use ONLY information directly supported by the retrieved context snippets.
2. Do NOT extrapolate, speculate, or invent facts not stated in the context.
3. If the retrieved context does not contain enough information to formulate an accurate answer, state exactly:
   "I could not find sufficient information in the uploaded documents to answer this question."
4. When formulating the answer, reference the source document names and page numbers where applicable.
5. Maintain a professional, concise, academic tone.
"""


class CitationSource(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_id: str
    similarity_score: float
    snippet: str


class RAGResponse(BaseModel):
    question: str
    answer: str
    is_grounded: bool
    sources: List[CitationSource] = Field(default_factory=list)
    retrieval_count: int = 0
    latency_ms: float = 0.0
    model_used: str = ""


class GeminiService:
    """
    RAG generation service interfacing with Google Gemini.
    Enforces factual grounding, citation generation, and hallucination defense.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client = None
        self._use_legacy_sdk = False

        if self.api_key:
            self._init_client()
        else:
            logger.warning(
                "GEMINI_API_KEY is not configured. Live LLM generation will be unavailable."
            )

    def _init_client(self):
        """Initializes the official Google GenAI client with fallback to legacy SDK."""
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._use_legacy_sdk = False
            logger.info("Google GenAI client initialized with model: %s", self.model_name)
        except Exception as e:
            logger.warning("Could not initialize google.genai (%s). Trying legacy google.generativeai...", e)
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self._client = legacy_genai
                self._use_legacy_sdk = True
                logger.info("Legacy google.generativeai client configured.")
            except Exception as legacy_err:
                logger.error("Failed to initialize any Gemini SDK: %s", legacy_err)
                self._client = None

    def construct_context_block(self, contexts: List[SearchResult]) -> str:
        """Constructs an indexed, provenance-tracked context block for prompting."""
        if not contexts:
            return "No relevant document excerpts were retrieved."

        blocks: List[str] = []
        for i, ctx in enumerate(contexts, 1):
            source_header = f"[Source {i}: {ctx.document_name} | Page {ctx.page_number} | Chunk {ctx.chunk_id}]"
            blocks.append(f"{source_header}\n{ctx.text.strip()}")

        return "\n\n---\n\n".join(blocks)

    def generate_grounded_answer(
        self,
        question: str,
        contexts: List[SearchResult],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """
        Synthesizes a grounded answer from retrieved contexts using Google Gemini.
        If context is empty or uninformative, returns the safe fallback without calling the API.
        """
        t_start = time.perf_counter()
        clean_question = question.strip()

        # Build citation objects from retrieved contexts
        sources = [
            CitationSource(
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                chunk_id=c.chunk_id,
                similarity_score=c.similarity_score,
                snippet=c.text[:200].strip() + ("..." if len(c.text) > 200 else ""),
            )
            for c in contexts
        ]

        # Hallucination Guard: If no contexts retrieved, return safe fallback immediately
        if not contexts:
            logger.info("No context provided for question: '%s'. Returning safe fallback.", clean_question)
            return RAGResponse(
                question=clean_question,
                answer=SAFE_FALLBACK_ANSWER,
                is_grounded=False,
                sources=[],
                retrieval_count=0,
                latency_ms=(time.perf_counter() - t_start) * 1000,
                model_used="hallucination_guard",
            )

        if not self.api_key:
            logger.warning("GEMINI_API_KEY missing. Returning configuration advisory.")
            return RAGResponse(
                question=clean_question,
                answer="GEMINI_API_KEY is not configured on the server. Please provide a valid Gemini API key in your configuration.",
                is_grounded=False,
                sources=sources,
                retrieval_count=len(contexts),
                latency_ms=(time.perf_counter() - t_start) * 1000,
                model_used="config_error",
            )

        context_text = self.construct_context_block(contexts)

        # Assemble prompt
        history_text = ""
        if conversation_history:
            formatted_turns = [
                f"{turn.get('role', 'user').capitalize()}: {turn.get('content', '')}"
                for turn in conversation_history[-4:]  # Last 4 turns
            ]
            history_text = "Recent Conversation History:\n" + "\n".join(formatted_turns) + "\n\n"

        prompt = (
            f"{history_text}"
            f"Retrieved Document Context Excerpts:\n"
            f"{context_text}\n\n"
            f"User Question: {clean_question}\n\n"
            f"Provide a grounded, factual answer based strictly on the excerpts above. "
            f"If the excerpts do not contain the answer, reply with the exact phrase: "
            f"\"{SAFE_FALLBACK_ANSWER}\""
        )

        try:
            raw_answer = self._call_gemini_api(prompt)
            clean_answer = raw_answer.strip()

            # Determine whether answer is grounded or fallback
            is_grounded = SAFE_FALLBACK_ANSWER.lower() not in clean_answer.lower()

            elapsed_ms = (time.perf_counter() - t_start) * 1000
            logger.info(
                "Gemini answer generated in %.2f ms (grounded=%s, sources=%d)",
                elapsed_ms,
                is_grounded,
                len(sources),
            )

            return RAGResponse(
                question=clean_question,
                answer=clean_answer,
                is_grounded=is_grounded,
                sources=sources if is_grounded else [],
                retrieval_count=len(contexts),
                latency_ms=elapsed_ms,
                model_used=self.model_name,
            )

        except Exception as e:
            logger.error("Error generating answer from Gemini API: %s", str(e), exc_info=True)
            elapsed_ms = (time.perf_counter() - t_start) * 1000
            return RAGResponse(
                question=clean_question,
                answer=f"Error communicating with AI service: {str(e)}",
                is_grounded=False,
                sources=sources,
                retrieval_count=len(contexts),
                latency_ms=elapsed_ms,
                model_used=self.model_name,
            )

    def _call_gemini_api(self, prompt: str) -> str:
        """Dispatches request to Gemini using available SDK with resilient fallback across models."""
        candidate_models = [self.model_name]
        for fallback in ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for model_to_try in candidate_models:
            try:
                if not self._use_legacy_sdk:
                    from google.genai import types
                    config = types.GenerateContentConfig(
                        temperature=0.1,
                        system_instruction=SYSTEM_PROMPT_TEMPLATE,
                    )
                    response = self._client.models.generate_content(
                        model=model_to_try,
                        contents=prompt,
                        config=config,
                    )
                    self.model_name = model_to_try
                    return response.text or ""
                else:
                    model = self._client.GenerativeModel(
                        model_name=model_to_try,
                        system_instruction=SYSTEM_PROMPT_TEMPLATE,
                    )
                    response = model.generate_content(
                        prompt,
                        generation_config={"temperature": 0.1},
                    )
                    self.model_name = model_to_try
                    return response.text or ""
            except Exception as e:
                logger.warning("Model attempt '%s' failed: %s. Trying fallback candidate...", model_to_try, e)
                last_error = e

        if last_error:
            raise last_error
        return ""
