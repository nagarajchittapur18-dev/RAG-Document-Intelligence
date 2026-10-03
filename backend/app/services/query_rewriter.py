import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("ragmate.query_rewriter")


class QueryRewriter:
    """
    Lightweight, deterministic conversational query contextualizer and title generator.
    Resolves coreferences and anaphora (e.g. 'it', 'they', 'the first paper')
    for vector retrieval without extra LLM latency, while preserving the user's original query.
    """

    COREFERENCE_PATTERNS = [
        r"\b(it|its|they|them|their|theirs)\b",
        r"\b(this|that|these|those)\b",
        r"\b(the\s+(first|second|third|former|latter)\s+(paper|document|one|study))\b",
        r"\b(the\s+(paper|document|model|architecture|method|methodology|dataset|approach|authors?))\b",
        r"^(what|how)\s+about\b",
        r"^(and\s+)(what|how|which|why)\b",
        r"^(what\s+were\s+the\s+results)\b",
    ]

    STOPWORDS_FOR_TITLE = {
        "what", "is", "the", "are", "of", "in", "on", "for", "to", "a", "an", "and",
        "can", "you", "tell", "me", "about", "please", "explain", "describe", "how",
        "does", "do", "did", "which", "give", "show", "i", "would", "like", "know",
    }

    def should_rewrite(self, question: str) -> bool:
        """Determines if the question contains coreference or elliptical indicators."""
        clean_q = question.strip().lower()
        if not clean_q:
            return False

        for pattern in self.COREFERENCE_PATTERNS:
            if re.search(pattern, clean_q, re.IGNORECASE):
                return True
        return False

    def rewrite_query_for_retrieval(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        document_names: Optional[List[str]] = None,
    ) -> str:
        """
        Synthesizes an augmented retrieval query by resolving coreferences
        from conversation turns and document names.
        """
        clean_q = question.strip()
        if not conversation_history or not self.should_rewrite(clean_q):
            return clean_q

        # Extract recent conversation context (last 2 user/assistant turns)
        recent_turns = conversation_history[-3:]
        prior_user_turns = [t["content"] for t in recent_turns if t.get("role") == "user"]
        prior_assistant_turns = [t["content"] for t in recent_turns if t.get("role") == "assistant"]

        context_clues: List[str] = []

        # 1. Resolve ordinal document references ("first paper", "second paper")
        clean_q_lower = clean_q.lower()
        rewritten = clean_q

        if document_names and len(document_names) >= 1:
            clean_names = [Path_stem(d) for d in document_names]

            if re.search(r"\bthe\s+first\s+(paper|document|study|model)\b", clean_q_lower):
                rewritten = re.sub(
                    r"\bthe\s+first\s+(paper|document|study|model)\b",
                    clean_names[0],
                    rewritten,
                    flags=re.IGNORECASE,
                )
            if len(clean_names) >= 2 and re.search(r"\bthe\s+second\s+(paper|document|study|model)\b", clean_q_lower):
                rewritten = re.sub(
                    r"\bthe\s+second\s+(paper|document|study|model)\b",
                    clean_names[1],
                    rewritten,
                    flags=re.IGNORECASE,
                )
            if len(clean_names) >= 3 and re.search(r"\bthe\s+third\s+(paper|document|study|model)\b", clean_q_lower):
                rewritten = re.sub(
                    r"\bthe\s+third\s+(paper|document|study|model)\b",
                    clean_names[2],
                    rewritten,
                    flags=re.IGNORECASE,
                )

        # 2. Extract salient topic from previous user query
        if prior_user_turns:
            last_q = prior_user_turns[-1].strip()
            # Extract key nouns/topics from previous question
            topic_match = re.search(
                r"(?:about|on|in|of|for|with)\s+([A-Za-z0-9_\-\s]{3,40})[\?\.]?$",
                last_q,
                re.IGNORECASE,
            )
            if topic_match:
                extracted_topic = topic_match.group(1).strip()
                if extracted_topic and len(extracted_topic) > 2:
                    context_clues.append(extracted_topic)

        # 3. Extract salient entity from previous assistant answer
        if prior_assistant_turns:
            last_answer = prior_assistant_turns[-1]
            # Look for named models, algorithms, or capitalized terms
            entity_matches = re.findall(
                r"\b([A-Z][a-zA-Z0-9\-_]{2,}(?:\s+[A-Z][a-zA-Z0-9\-_]+)?)\b",
                last_answer[:300],
            )
            if entity_matches:
                # Add up to 2 unique entities
                seen = set()
                for em in entity_matches:
                    em_clean = em.strip()
                    if em_clean.lower() not in {"the", "this", "based", "paper", "document", "results", "model"}:
                        if em_clean not in seen:
                            seen.add(em_clean)
                            context_clues.append(em_clean)
                            if len(seen) >= 2:
                                break

        # If we replaced ordinal references directly, return rewritten
        if rewritten != clean_q:
            return rewritten

        # If we have context clues, augment query for vector retrieval
        if context_clues:
            augmented = f"{clean_q} ({', '.join(context_clues[:3])})"
            logger.debug("Query contextualized from '%s' to '%s'", clean_q, augmented)
            return augmented

        return clean_q

    def generate_chat_title(self, first_question: str) -> str:
        """
        Generates a concise (5-8 words) title from the user's initial question.
        Avoids extra LLM calls and executes deterministically in sub-millisecond time.
        """
        clean = first_question.strip()
        # Remove trailing question marks, exclamation marks, periods
        clean = re.sub(r"[\?\!\.]+$", "", clean).strip()

        # Remove common conversational query prefixes
        prefixes = [
            r"^(can\s+you\s+(please\s+)?(tell\s+me|explain|describe))\s+(about\s+)?",
            r"^(please\s+(explain|describe|tell\s+me))\s+(about\s+)?",
            r"^(what\s+is\s+the|what\s+are\s+the)\s+",
            r"^(how\s+does\s+the|how\s+do\s+the)\s+",
            r"^(compare\s+the\s+)",
            r"^(tell\s+me\s+about\s+)",
            r"^(what\s+about\s+)",
        ]
        topic = clean
        for p in prefixes:
            topic = re.sub(p, "", topic, flags=re.IGNORECASE).strip()

        # If stripped topic is empty, fallback to clean question
        if not topic:
            topic = clean

        words = topic.split()
        if len(words) > 7:
            short_title = " ".join(w.capitalize() for w in words[:6]) + "..."
        else:
            short_title = " ".join(w.capitalize() for w in words)

        # Ensure title is not too long
        if len(short_title) > 60:
            short_title = short_title[:57].strip() + "..."

        return short_title if short_title else "New Conversation"


def Path_stem(path_or_name: str) -> str:
    """Helper extracting clean basename without file extension."""
    name = path_or_name.split("/")[-1].split("\\")[-1]
    if "." in name:
        return name.rsplit(".", 1)[0]
    return name
