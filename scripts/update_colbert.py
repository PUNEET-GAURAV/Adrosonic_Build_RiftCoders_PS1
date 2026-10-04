import re

with open('src/trustrag/assembly.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'from .adapters.ce_reranker import CrossEncoderReranker',
    'from .adapters.ce_reranker import CrossEncoderReranker\n    from .adapters.colbert_reranker import ColbertReranker'
)

text = text.replace(
    'reranker = CrossEncoderReranker(models["reranker"]) if use_rerank else None',
    'reranker = CrossEncoderReranker(models["reranker"]) if use_rerank else None\n    colbert_reranker = ColbertReranker()'
)

text = text.replace(
    'reranker=reranker,',
    'reranker=reranker,\n        colbert_reranker=colbert_reranker,'
)

with open('src/trustrag/assembly.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open('src/trustrag/retrieval/orchestrator.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add colbert_reranker to init
text = text.replace(
    'reranker: Reranker | None = None,',
    'reranker: Reranker | None = None,\n        colbert_reranker = None,'
)
text = text.replace(
    'self.reranker = reranker',
    'self.reranker = reranker\n        self.colbert_reranker = colbert_reranker'
)

# Handle mode in search
new_search = '''
        if request.mode == "hybrid_colbert" and self.colbert_reranker:
            c = max(1, min(request.top_k, 50))
            if request.cache_mode: c *= 3
            results = self._hybrid(request, c, dense_vec, sparse_vec)
            
            t2 = time.perf_counter()
            reranked = self.colbert_reranker.rerank(request.query, results)
            ms_rerank = (time.perf_counter() - t2) * 1000
            timings.rerank = round(ms_rerank, 2)
            results = reranked
'''

text = text.replace(
    'if request.mode == "hybrid_rerank" and self.reranker:',
    new_search + '\n        if request.mode == "hybrid_rerank" and self.reranker:'
)

with open('src/trustrag/retrieval/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated assembly and orchestrator')
