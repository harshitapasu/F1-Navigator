"""
RAG pipeline — async version for FastAPI streaming.
Extracted from f1_navigator.py, adapted for server use.
"""

import os
import re
import hashlib
from dataclasses import dataclass
from typing import AsyncGenerator

from openai import AsyncOpenAI, OpenAI
from pinecone import Pinecone
from rank_bm25 import BM25Okapi

# ── Config ────────────────────────────────────────────────────────────────────

PINECONE_INDEX  = os.getenv("PINECONE_INDEX_NAME", "edtech")
PINECONE_HOST   = os.getenv("PINECONE_HOST", "https://edtech-pfofxdz.svc.aped-4627-b74a.pinecone.io")
PINECONE_NS     = os.getenv("PINECONE_NAMESPACE", "")

EMBED_MODEL     = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
CHAT_MODEL      = os.getenv("OPENAI_CHAT_MODEL",  "gpt-4o")

TOP_K_SEMANTIC  = int(os.getenv("TOP_K_SEMANTIC", "30"))
TOP_N_TO_LLM    = int(os.getenv("TOP_N_TO_LLM",   "7"))
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "0.6"))
BM25_WEIGHT     = 1.0 - SEMANTIC_WEIGHT

# ── Singletons ────────────────────────────────────────────────────────────────

_sync_oai:  OpenAI | None      = None
_async_oai: AsyncOpenAI | None = None
_pc_index                       = None


def _sync_client() -> OpenAI:
    global _sync_oai
    if _sync_oai is None:
        _sync_oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _sync_oai


def _async_client() -> AsyncOpenAI:
    global _async_oai
    if _async_oai is None:
        _async_oai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _async_oai


def _index():
    global _pc_index
    if _pc_index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _pc_index = pc.Index(name=PINECONE_INDEX, host=PINECONE_HOST)
    return _pc_index


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    id: str
    text: str
    title: str
    section: str
    source_url: str
    category: str
    category_label: str
    score: float = 0.0


# ── Retrieval ─────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> list[float]:
    resp = _sync_client().embeddings.create(input=text, model=EMBED_MODEL)
    return resp.data[0].embedding


def semantic_search(query: str) -> list[Chunk]:
    vec    = get_embedding(query)
    kwargs = dict(vector=vec, top_k=TOP_K_SEMANTIC, include_metadata=True)
    if PINECONE_NS:
        kwargs["namespace"] = PINECONE_NS
    resp = _index().query(**kwargs)

    chunks = []
    for m in resp.matches:
        meta = m.metadata or {}
        chunks.append(Chunk(
            id             = m.id,
            text           = meta.get("text", ""),
            title          = meta.get("title", ""),
            section        = meta.get("section", ""),
            source_url     = meta.get("source_url", ""),
            category       = meta.get("category", ""),
            category_label = meta.get("category_label", ""),
            score          = float(m.score),
        ))
    return chunks


def _minmax(values: list[float]) -> list[float]:
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.0] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def deduplicate(chunks: list[Chunk]) -> list[Chunk]:
    seen_hashes:  set[str] = set()
    seen_url_sec: set[str] = set()
    unique: list[Chunk]    = []
    for c in chunks:
        h   = hashlib.md5(re.sub(r"\s+", " ", c.text).strip().lower().encode()).hexdigest()
        key = f"{c.source_url}||{c.section}"
        if h in seen_hashes or key in seen_url_sec:
            continue
        seen_hashes.add(h)
        seen_url_sec.add(key)
        unique.append(c)
    return unique


def hybrid_search(query: str) -> list[Chunk]:
    """Semantic search → BM25 rerank → deduplicate → top-N."""
    candidates = semantic_search(query)
    if not candidates:
        return []

    tokenized = [c.text.lower().split() for c in candidates]
    bm25      = BM25Okapi(tokenized)
    raw_bm25  = bm25.get_scores(query.lower().split()).tolist()

    sem_norm  = _minmax([c.score for c in candidates])
    bm25_norm = _minmax(raw_bm25)

    for i, chunk in enumerate(candidates):
        chunk.score = SEMANTIC_WEIGHT * sem_norm[i] + BM25_WEIGHT * bm25_norm[i]

    candidates.sort(key=lambda c: c.score, reverse=True)
    return deduplicate(candidates)[:TOP_N_TO_LLM]


# ── Prompt builders ───────────────────────────────────────────────────────────

def build_system_prompt(profile: dict) -> str:
    from datetime import date, datetime
    today = date.today()
    today_str = today.strftime("%B %d, %Y")

    grad_date_raw = profile.get("graduation_date") or ""
    try:
        grad_date = datetime.strptime(grad_date_raw, "%Y-%m-%d").date()
        already_graduated = today > grad_date
        grad_str = grad_date.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        grad_date = None
        already_graduated = None
        grad_str = "unknown"

    if already_graduated is True:
        grad_status = f"GRADUATED — program ended {grad_str} ({(today - grad_date).days} days ago)"
    elif already_graduated is False:
        grad_status = f"ACTIVE — {(grad_date - today).days} days until graduation on {grad_str}"
    else:
        grad_status = "unknown — student should set their graduation date in their profile"

    return f"""You are F1 Navigator, a highly knowledgeable and personalised expert on F-1 student visas, OPT, CPT, STEM OPT, H-1B, and US immigration law.

Today's date: {today_str}

## Student Profile (use this to personalise EVERY answer)
- Name: {profile.get("name") or "Student"}
- Visa status: {profile.get("visa_status") or "F-1"}
- Major: {profile.get("major") or "unknown"} ({profile.get("degree_level") or "unknown"})
- University: {profile.get("university") or "unknown"}
- Graduation date: {grad_str}
- Graduation status: {grad_status}

## Core Rules
1. BASE EVERY ANSWER on the retrieved documents provided in the user message. Never invent rules, deadlines, fees, or procedures.
2. PERSONALISE every answer using the student profile above. Any time a deadline, timeline, eligibility window, or requirement is mentioned, apply it to this specific student's dates and situation. For example, if a rule says "90 days before graduation", calculate and state the actual date for this student.
3. DETAILED RESPONSES — give thorough, complete explanations. Do not truncate. Cover all relevant aspects from the documents.
4. ELIGIBILITY QUESTIONS — always apply the document rules to today's date ({today_str}) and the student's graduation date ({grad_str}). State your date reasoning explicitly so the student can follow the logic.
5. If the retrieved documents do not contain enough information to fully answer the question, say so clearly and direct the student to uscis.gov or their DSO. Do not guess or fill gaps with invented information.
6. Use ⚠️ only for warnings that could jeopardise the student's visa status or cause serious legal consequences.

## History Rule (CRITICAL)
The conversation history is provided ONLY so you understand the context of the current question (e.g. what topic was being discussed, what the student's follow-up refers to).
- NEVER use a previous answer from history as the basis for your current answer.
- NEVER repeat or paraphrase a previous answer.
- The RAG pipeline runs fresh for every query — always answer from the newly retrieved documents, not from memory or history.
- Treat every question as a fresh query grounded in the current retrieved documents.

## Format
- For eligibility questions: start with a clear YES or NO, then explain in full detail.
- Use bullet points for lists of 3+ items.
- Bold all critical deadlines, dollar amounts, and day/month counts.
- Do NOT add a Sources section — sources are shown separately.
"""


def build_user_message(query: str, chunks: list[Chunk]) -> str:
    docs = []
    for i, c in enumerate(chunks, 1):
        docs.append(
            f"### [Doc {i}] {c.title}\n"
            f"- **Category:** {c.category_label}\n"
            f"- **Section:** {c.section}\n"
            f"- **URL:** {c.source_url}\n\n"
            f"{c.text}"
        )
    return (
        "## Official F-1 Documentation (retrieved)\n\n"
        + "\n\n---\n\n".join(docs)
        + "\n\n---\n\n"
        "## Student Question\n\n"
        + query
        + "\n\n⚠️ MANDATORY INSTRUCTION: Your answer must be derived EXCLUSIVELY from the retrieved documents above. "
        "The conversation history may be outdated — do NOT use any previous answer as a source. "
        "Read the documents above right now and construct a fresh, detailed, personalised answer for this student. "
        "If the documents do not cover the question, say so and refer to uscis.gov or the student's DSO."
    )


HISTORY_EXTRACTOR_PROMPT = """You are extracting durable conversation state from prior chat messages for use in a RAG pipeline.

Your output must contain only metadata that is safe to carry forward into future answer-generation.

SOURCE TRUST RULES:
- User messages are authoritative for intent, constraints, corrections, and preferences.
- Assistant messages are NOT authoritative for facts unless they explicitly include document references, citations, URLs, doc IDs, or quoted retrieved evidence.
- Assistant messages may be used only to recover: doc references, explicit task framing, change events.
- Never copy assistant answer wording into the output.

EXTRACT ONLY: intent, topic, constraints, known_entities, doc_references, change_log
EXCLUDE: prior answers, prose summaries, explanations, recommendations, interpretations not explicitly supported by user instructions or cited evidence

NORMALIZATION RULES:
- Deduplicate semantically equivalent constraints and entities
- Prefer the latest user-stated constraint if multiple versions conflict
- Preserve exact doc IDs / URLs / citation labels when present
- Keep each field concise and non-generative

Return JSON only using this schema:
{
  "intent": "",
  "topic": "",
  "constraints": [],
  "known_entities": [],
  "doc_references": [{"type": "", "id": "", "title": "", "source": "", "url": "", "citation": ""}],
  "change_log": [{"turn_ref": "", "change_type": "", "details": ""}]
}"""


async def extract_history_context(history: list[dict]) -> str | None:
    """Summarise raw history into safe metadata JSON using a fast LLM call."""
    if not history:
        return None
    role_tagged = "\n".join(f"[{m['role'].upper()}]: {m['content']}" for m in history[-6:])
    prompt = HISTORY_EXTRACTOR_PROMPT.replace("{{ROLE_TAGGED_MESSAGES}}", role_tagged)
    resp = await _async_client().chat.completions.create(
        model       = "gpt-4o-mini",
        messages    = [{"role": "user", "content": prompt}],
        temperature = 0.0,
        max_tokens  = 512,
    )
    return resp.choices[0].message.content.strip()


# ── Streaming chat ────────────────────────────────────────────────────────────

async def stream_chat(
    query: str,
    chunks: list[Chunk],
    profile: dict,
    history: list[dict],
) -> AsyncGenerator[str, None]:
    """Yield text tokens from GPT-4o, grounded in retrieved chunks."""
    context_json = await extract_history_context(history)

    history_block = []
    if context_json:
        history_block = [
            {
                "role": "system",
                "content": (
                    "## Conversation Context (extracted metadata only — NOT factual answers)\n"
                    "The following is a structured summary of what the student has been asking about. "
                    "Use it ONLY to understand their intent and avoid them repeating themselves. "
                    "All factual answers must come from the retrieved documents below, not from this context.\n\n"
                    + context_json
                )
            }
        ]

    messages = (
        [{"role": "system", "content": build_system_prompt(profile)}]
        + history_block
        + [{"role": "user", "content": build_user_message(query, chunks)}]
    )

    print("\n" + "="*80)
    print("FULL PROMPT SENT TO GPT")
    print("="*80)
    for i, m in enumerate(messages):
        print(f"\n[{i}] role={m['role']}")
        print("-" * 40)
        print(m["content"])
    print("="*80 + "\n")

    stream = await _async_client().chat.completions.create(
        model       = CHAT_MODEL,
        messages    = messages,
        stream      = True,
        max_tokens  = 2048,
        temperature = 0.2,
    )

    async for event in stream:
        delta = event.choices[0].delta.content
        if delta:
            yield delta
