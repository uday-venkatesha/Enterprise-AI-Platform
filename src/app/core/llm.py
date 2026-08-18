from openai import OpenAI

from app.config import settings
from app.models.chunk import Chunk

# Reuses the same key as embeddings. (You could share one client between this
# and embeddings.py; two is fine and simpler to read while learning.)
_client = OpenAI(api_key=settings.openai_api_key)


# The SYSTEM prompt sets the rules. This is where "strict, enterprise-safe"
# lives — we tell the model, in no uncertain terms, to stay inside the context
# and to admit ignorance rather than invent. This single string is your main
# defense against hallucination.
SYSTEM_PROMPT = """You are a careful assistant for an enterprise knowledge base.
Answer the user's question using ONLY the numbered context passages provided below.

Rules:
- Use ONLY information found in the context passages. Do not use any outside knowledge.
- If the context does not contain the answer, reply exactly: "I don't know based on the available documents."
- When you use a passage, cite it with its bracketed number, like [1] or [2].
- Be concise and factual. Do not speculate."""


def build_context(chunks: list[Chunk]) -> str:
    # Number each chunk [1], [2], ... This does double duty: it lets the MODEL
    # cite passages by number, and it lets US map those numbers back to real
    # documents afterward. The numbering is the backbone of citations.
    blocks = [f"[{index}] {chunk.content}" for index, chunk in enumerate(chunks, start=1)]
    return "\n\n".join(blocks)


def generate_answer(question: str, chunks: list[Chunk]) -> str:
    context = build_context(chunks)

    # The USER message carries the retrieved context AND the question together.
    # The model sees the passages, then the question, and answers under the
    # system rules above.
    user_message = f"Context passages:\n\n{context}\n\nQuestion: {question}"

    response = _client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},   # the rules
            {"role": "user", "content": user_message},       # context + question
        ],
        # temperature omitted — reasoning models (o1/o3 etc.) only support the
        # default value of 1 and will return a 400 if you pass 0.
    )

    # The model's reply text lives here.
    return response.choices[0].message.content