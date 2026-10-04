"""Optional topic enrichment via k-means over embeddings (12 clusters, labelled by top
TF-IDF terms). Gracefully no-ops if scikit-learn is unavailable, leaving topic=None.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np


def assign_topics(
    texts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    n_clusters: int = 12,
    random_state: int = 42,
) -> list[str] | None:
    """Return a topic label per text (or None for all if sklearn is missing)."""
    try:
        from sklearn.cluster import KMeans  # local import
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        return None

    if len(texts) < n_clusters:
        return None
    X = np.asarray(embeddings, dtype="float32")
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10).fit(X)
    labels = kmeans.labels_

    vec = TfidfVectorizer(stop_words="english", max_features=1000)
    try:
        X_tfidf = vec.fit_transform(texts)
    except ValueError:
        return None
    terms = vec.get_feature_names_out()

    cluster_terms: list[str] = []
    for c in range(n_clusters):
        idx = np.where(labels == c)[0]
        if len(idx) == 0:
            cluster_terms.append(f"topic-{c}")
            continue
        # label each cluster by the top TF-IDF terms of its own documents
        centroid = np.asarray(X_tfidf[idx].mean(axis=0)).ravel()
        top = np.argsort(centroid)[-3:][::-1]
        cluster_terms.append(", ".join(terms[i] for i in top) if len(terms) else f"topic-{c}")

    return [cluster_terms[c] for c in labels]
