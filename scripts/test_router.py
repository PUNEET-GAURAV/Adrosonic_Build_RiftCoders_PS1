import json
from trustrag.retrieval.orchestrator import RetrievalOrchestrator
from trustrag.adapters.st_embedder import SentenceTransformerEmbedder
from trustrag.adapters.bm25_sparse import BM25SparseEncoder
from trustrag.adapters.qdrant_store import QdrantStore
from trustrag.core.models import SearchRequest, Filters

def main():
    store = QdrantStore("http://localhost:6333", collection="verity_banking")
    embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5", query_prefix="Represent this sentence for searching relevant passages: ")
    sparse = BM25SparseEncoder(hash_bits=32)
    
    orch = RetrievalOrchestrator(embedder, sparse, store)
    
    # Query 1: Hard Route expected (kyc documents)
    req1 = SearchRequest(query="What documents are required for KYC?", top_k=2)
    res1 = orch.search(req1)
    
    print("=== Query 1: KYC Documents ===")
    print(f"Router Result: {json.dumps(res1.route_result, indent=2)}")
    print(f"Needs Clarification: {res1.needs_clarification}")
    print(f"Results Count: {len(res1.results)}")
    
    # Query 2: Ambiguous/Generic (what documents are needed) -> Should fallback or soft route
    req2 = SearchRequest(query="what documents are needed", top_k=2)
    res2 = orch.search(req2)
    
    print("\n=== Query 2: Ambiguous ===")
    print(f"Router Result: {json.dumps(res2.route_result, indent=2)}")
    print(f"Needs Clarification: {res2.needs_clarification}")

if __name__ == "__main__":
    main()
