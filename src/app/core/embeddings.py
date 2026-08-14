from openai import OpenAI

from app.config import settings

# One client for the app, authenticated with our key. Same OpenAI SDK you used
# for chat — embeddings just use a different endpoint on the same client.
_client = OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    # Guard: embedding an empty list would be a wasted API call.
    if not texts:
        return []

    # KEY EFFICIENCY POINT: we send ALL chunk texts in ONE request (input=a list)
    # rather than one call per chunk. OpenAI embeds them in a batch and returns
    # results in the SAME ORDER as the input — cheaper and far faster.
    response = _client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )

    # Each result carries its vector in .embedding; order matches `texts`.
    return [item.embedding for item in response.data]