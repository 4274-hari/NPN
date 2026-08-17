"""Retrieval and LLM orchestration for Nexora replies."""

from pathlib import Path
import sys

from config import settings

RAG_ROOT = Path(__file__).resolve().parent.parent / "rag"
RAG_SRC = RAG_ROOT / "src"
if str(RAG_SRC) not in sys.path:
    sys.path.insert(0, str(RAG_SRC))

_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        from retriever import RAGRetriever
        _retriever = RAGRetriever(RAG_ROOT / "vector_db")
    return _retriever


def retrieve_context(customer_text: str) -> str:
    """Retrieve brand, policy, and safety guidance for an LLM reply."""
    sections = []
    for rag_type in ("brand", "policy", "safety"):
        results = get_retriever().retrieve(customer_text, rag_type, top_k=2)
        if results:
            sections.append(f"{rag_type.title()} guidance:\n" + "\n\n".join(item["text"] for item in results))
    return "\n\n".join(sections) or "No relevant knowledge was found."


def generate_reply(customer_text: str, labels: dict, conversation_memory: str = "") -> str:
    """Generate a customer-facing answer using classifier labels and RAG context."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in backend/.env")

    from groq import Groq

    context = retrieve_context(customer_text)
    prompt = f"""Write only a concise, professional customer-facing reply for Nexora.

Customer message:
{customer_text}

Classifier labels:
Intent: {labels.get('intent', 'unknown')}
Topic: {labels.get('topic', 'unknown')}
Sentiment: {labels.get('sentiment', 'unknown')}
Emotion: {labels.get('emotion', 'unknown')}
Urgency: {labels.get('urgency', 'unknown')}

Retrieved company guidance:
{context}

Recent conversation context (use only when it is relevant):
{conversation_memory or "No prior conversation is available."}

Do not mention classifiers, RAG, internal policies, teams, or documents. Do not invent facts, promise an outcome not supported by the guidance, request secrets, or expose sensitive information."""
    response = Groq(api_key=settings.groq_api_key).chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "system", "content": "Return only the customer-facing reply."}, {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip().strip('"')
