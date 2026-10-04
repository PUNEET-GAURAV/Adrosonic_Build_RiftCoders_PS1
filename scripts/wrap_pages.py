import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Fix CSS for .page
html = re.sub(
    r'\.page \{ display: none; flex: 1; padding: 40px 10%; overflow-y: auto; \}',
    r'.page { display: none; flex: 1; overflow-y: auto; }\n.page.active { display: flex; justify-content: center; }\n.page-inner { width: 100%; max-width: 1200px; padding: 28px; }',
    html
)
# Just in case my previous replace was slightly different
html = re.sub(
    r'\.page \{ display: none; flex: 1; padding: 28px; overflow-y: auto; \}',
    r'.page { display: none; flex: 1; overflow-y: auto; }\n.page.active { display: flex; justify-content: center; }\n.page-inner { width: 100%; max-width: 1200px; padding: 28px; }',
    html
)
html = html.replace('.page.active { display: block; }', '')

# Wrap contents of page-search
html = re.sub(
    r'(<div class="page(?: active)?" id="page-search"[^>]*>)\s*(<!-- Metric strip -->)',
    r'\1\n      <div class="page-inner">\n        \2',
    html
)
# Note: we need to add a closing </div> before the next page.
html = re.sub(
    r'(</div>\s*<!-- \S+ Page: Chat)',
    r'</div>\n      \1',
    html
)

# Wrap contents of page-chat
html = re.sub(
    r'(<div class="page" id="page-chat"[^>]*>)\s*(<div class="chat-wrap">)',
    r'\1\n      <div class="page-inner">\n        \2',
    html
)
html = re.sub(
    r'(</div>\s*<!-- \S+ Page: Upsert)',
    r'</div>\n      \1',
    html
)

# Wrap contents of page-upsert
html = re.sub(
    r'(<div class="page" id="page-upsert"[^>]*>)\s*(<div style="max-width:800px">)',
    r'\1\n      <div class="page-inner">\n        \2',
    html
)
html = re.sub(
    r'(</div>\s*<!-- \S+ Page: Benchmarks)',
    r'</div>\n      \1',
    html
)

# Wrap contents of page-benchmark
html = re.sub(
    r'(<div class="page" id="page-benchmark"[^>]*>)\s*(<h1>Evaluation &amp; Benchmarks</h1>)',
    r'\1\n      <div class="page-inner">\n        \2',
    html
)
html = re.sub(
    r'(</div>\s*<!-- \S+ Page: System)',
    r'</div>\n      \1',
    html
)

# Wrap contents of page-system
html = re.sub(
    r'(<div class="page" id="page-system"[^>]*>)\s*(<h1>System Overview</h1>)',
    r'\1\n      <div class="page-inner">\n        \2',
    html
)
html = re.sub(
    r'(</div>\s*</div><!-- /main -->)',
    r'</div>\n      \1',
    html
)

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Wrapped pages in page-inner")
