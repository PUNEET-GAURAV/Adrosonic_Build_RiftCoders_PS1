import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_dropdown = '''<select id="mode-select" onchange="currentMode = this.value" style="width:300px">
                  <option value="dense">Phase 1: Dense Only</option>
                  <option value="hybrid">Phase 2: BM25 Hybrid</option>
                  <option value="hybrid_rerank" selected>Phase 3: Hybrid + ONNX Reranker</option>
                  <option value="hybrid_colbert">Phase 4: Hybrid + ColBERT Reranker</option>
                </select>'''

html = re.sub(
    r'<select id="mode-select".*?</select>', 
    new_dropdown, 
    html, 
    flags=re.DOTALL
)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated UI modes')
