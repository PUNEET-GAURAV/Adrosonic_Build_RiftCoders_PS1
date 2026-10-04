with open('src/trustrag/retrieval/orchestrator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add LexicalRouter import
import_patch = '''
from .explain import matched_terms

try:
    from ..routing.router import LexicalRouter
except ImportError:
    LexicalRouter = None
'''
code = code.replace('from .explain import matched_terms', import_patch.strip())

# Add colbert_reranker to __init__
init_patch = '''
    def __init__(
        self,
        embedder: Embedder,
        sparse_encoder: SparseEncoder,
        store: VectorStore,
        reranker: Reranker | None = None,
        colbert_reranker = None,
        cache: Cache | None = None,
        generator: Generator | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.embedder = embedder
        self.sparse = sparse_encoder
        self.store = store
        self.reranker = reranker
        self.colbert_reranker = colbert_reranker
        self.cache = cache
        self.generator = generator
        self.cfg = config or {}
        self._config_hash = ""
        self.router = LexicalRouter() if LexicalRouter else None
'''

old_init = '''
    def __init__(
        self,
        embedder: Embedder,
        sparse_encoder: SparseEncoder,
        store: VectorStore,
        reranker: Reranker | None = None,
        cache: Cache | None = None,
        generator: Generator | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.embedder = embedder
        self.sparse = sparse_encoder
        self.store = store
        self.reranker = reranker
        self.cache = cache
        self.generator = generator
        self.cfg = config or {}
        self._config_hash = ""
'''
code = code.replace(old_init.strip('\n'), init_patch.strip('\n'))

with open('src/trustrag/retrieval/orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Restored router and colbert to init.')
