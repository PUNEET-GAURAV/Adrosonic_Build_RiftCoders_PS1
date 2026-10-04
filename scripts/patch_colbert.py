with open('src/trustrag/retrieval/orchestrator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# In search:
colbert_code = '''
        if request.mode == "colbert" and self.colbert_reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            results = self.colbert_reranker.rerank(request.query, pool)[: request.top_k]
            timings.rerank = round((time.perf_counter() - t) * 1000, 2)
            degraded = self._over_budget(t0, request.latency_budget_ms)
        elif request.mode == "hybrid_rerank" and self.reranker is not None:'''
code = code.replace('if request.mode == "hybrid_rerank" and self.reranker is not None:', colbert_code.strip(), 1)

# And in the retry fallback!
colbert_fallback = '''
            if request.mode == "colbert" and self.colbert_reranker is not None:
                pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
                results = self.colbert_reranker.rerank(request.query, pool)[: request.top_k]
            elif request.mode == "hybrid_rerank" and self.reranker is not None:'''
code = code.replace('if request.mode == "hybrid_rerank" and self.reranker is not None:', colbert_fallback.strip(), 1)


# In retrieve:
colbert_retrieve = '''
        if mode == "colbert" and self.colbert_reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            return self.colbert_reranker.rerank(query, pool)[:top_k]
        if mode == "hybrid_rerank" and self.reranker is not None:'''
code = code.replace('if mode == "hybrid_rerank" and self.reranker is not None:', colbert_retrieve.strip(), 1)

with open('src/trustrag/retrieval/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('ColBERT mode patched in orchestrator.')
