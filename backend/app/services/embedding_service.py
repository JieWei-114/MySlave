from typing import Iterable, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # set to "cuda" if available

def embed(texts: Iterable[str], normalize: bool = True) -> list[list[float]]:
    embeddings = _model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    return embeddings.tolist()

def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)

# from sentence_transformers import SentenceTransformer
# import numpy as np

# _model = SentenceTransformer("all-MiniLM-L6-v2")

# def embed(text: str) -> list[float]:
#     vec = _model.encode(text)
#     return vec.tolist()

# def cosine_similarity(a: list[float], b: list[float]) -> float:
#     a = np.array(a)
#     b = np.array(b)
#     return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))