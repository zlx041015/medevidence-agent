import hashlib
import math


EMBED_DIM = 64


def embed_text(text: str, dim: int = EMBED_DIM) -> list[float]:
    tokens = [token.strip(".,;:!?()[]{}\"'").lower() for token in text.split() if token.strip()]
    vector = [0.0] * dim

    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for idx in range(dim):
            byte = digest[idx % len(digest)]
            vector[idx] += (byte / 255.0) - 0.5

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))
