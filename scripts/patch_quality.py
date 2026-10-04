import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Center the page by adding max-width and margin: 0 auto
html = re.sub(r'(\.page \{[^}]+?)(?=\})', r'\1 max-width: 1200px; margin: 0 auto; width: 100%;', html)

# Change "Best Context Precision" to "Quality Factor Phase 1"
html = html.replace('<div class="metric-label">Best Context Precision</div>', '<div class="metric-label">Quality Factor Phase 1 (Dense)</div>')
html = html.replace('<div class="metric-value">0.607</div>\n          <div class="metric-sub">Hybrid + ONNX Reranker</div>\n          <div class="metric-badge badge-green">↑ vs 0.597 dense</div>',
                    '<div class="metric-value">0.597</div>\n          <div class="metric-sub">Dense Baseline</div>\n          <div class="metric-badge badge-blue">Foundation</div>')

# Change "nDCG@10 (Hybrid)" to "Quality Factor Phase 2"
html = html.replace('<div class="metric-label">nDCG@10 (Hybrid)</div>', '<div class="metric-label">Quality Factor Phase 2 (Hybrid)</div>')
html = html.replace('<div class="metric-value">0.707</div>\n          <div class="metric-sub">MRR 0.638</div>\n          <div class="metric-badge badge-green">Hit@5 92%</div>',
                    '<div class="metric-value">0.707</div>\n          <div class="metric-sub">BM25 Hybrid Fusion</div>\n          <div class="metric-badge badge-green">↑ Hit@5 92%</div>')


with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated UI centering and Quality Factor metrics")
