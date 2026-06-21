"""Embedding helpers for the closeout corpus.

Two embedders live here, with very different lifecycles:

* :func:`build_embeddings` — the *production* embedder (sentence-transformers,
  ``all-MiniLM-L6-v2``). It is **imported lazily inside the function** and is used
  **only at seed-build time** (or a future live-ingest). **The runtime never calls
  this** — the shipped DB carries baked vectors, so DEMO_MODE loads no model and
  opens no socket. It is opt-in at seed time via ``SITESOURCE_USE_MINILM=1``.

* :func:`deterministic_embedding` — a tiny, dependency-free hashed bag-of-words
  embedder (pure Python + stdlib ``hashlib``, stable across processes). It is the
  **default** baked into the offline demo seed and is what :mod:`db.store` uses to
  embed a query at runtime, so the whole semantic path runs offline and
  reproduces identically on every run. It is *not* an ML model; it imports nothing
  heavy.

Both return plain ``list[float]`` vectors, L2-normalised, so cosine similarity is
just a dot product.
"""

from __future__ import annotations

import hashlib
import math
import re

# Dimension of the deterministic embedding. (MiniLM is 384; the store reads the
# baked dimension from the DB ``meta`` table, so the two need not match.)
DETERMINISTIC_DIM = 256

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _bucket(token: str, dim: int) -> int:
    """A stable, process-independent hash of a token into ``[0, dim)``."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dim


def _l2_normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def deterministic_embedding(text: str, dim: int = DETERMINISTIC_DIM) -> list[float]:
    """Hashed bag-of-words embedding — deterministic, offline, no model load.

    Shared closeout/scope vocabulary (e.g. "lv", "distribution", "lighting",
    "containment") lands in the same buckets, so cosine rewards real overlap. Used
    to bake the demo seed and to embed runtime queries in DEMO_MODE.
    """
    vec = [0.0] * dim
    for token in _tokens(text):
        vec[_bucket(token, dim)] += 1.0
    return _l2_normalise(vec)


def build_embeddings(texts: list[str]) -> list[list[float]]:
    """MiniLM embeddings for ``texts`` — **seed-build time only, never the runtime**.

    sentence-transformers is imported lazily here so that importing this module (or
    running DEMO_MODE) never pulls in Torch or downloads a model.
    """
    from sentence_transformers import SentenceTransformer  # lazy: heavy, optional

    model = SentenceTransformer("all-MiniLM-L6-v2")
    raw = model.encode(list(texts), normalize_embeddings=True)
    return [[float(x) for x in row] for row in raw]
