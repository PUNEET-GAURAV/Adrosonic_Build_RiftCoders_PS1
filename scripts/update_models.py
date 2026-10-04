import re

with open('src/trustrag/core/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'Literal["dense", "sparse", "hybrid", "hybrid_rerank"]',
    'Literal["dense", "sparse", "hybrid", "hybrid_rerank", "hybrid_colbert"]'
)

with open('src/trustrag/core/models.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated models.py')
