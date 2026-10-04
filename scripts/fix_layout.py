import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix .page and .page-inner
html = re.sub(
    r'\.page\.active \{ display: flex; justify-content: center; \}',
    r'.page.active { display: block; }',
    html
)
html = re.sub(
    r'\.page-inner \{ width: 100%; max-width: 1200px; padding: 28px; \}',
    r'.page-inner { width: min(100% - 48px, 1500px); margin: 0 auto; padding: 32px 0; }',
    html
)

# Fix table and table-wrap
html = re.sub(
    r'\.table-wrap \{ overflow-x: auto; \}',
    r'.table-wrap { overflow-x: auto; width: 100%; }',
    html
)
html = re.sub(
    r'table \{ width: 100%; border-collapse: collapse; font-size: 13px; \}',
    r'table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: auto; }',
    html
)

# Fix wrapping for the mode tags in the table so it doesn't artificially stretch it
html = html.replace('<span class="tag tag-success">Hybrid + ONNX Reranker</span>', '<span class="tag tag-success" style="white-space: normal; text-align: center; display: inline-block;">Hybrid + ONNX Reranker</span>')

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Layout updated')
