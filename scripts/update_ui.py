import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace the metrics row
pattern = re.compile(r'<div class="metrics-row" id="metric-strip">.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>', re.DOTALL)
replacement = '''<div class="metrics-row" id="metric-strip">
          <div class="metric-card">
            <div class="metric-label">Passages Indexed</div>
            <div class="metric-value" id="m-docs">—</div>
            <div class="metric-sub">MS MARCO + custom</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">RAGAS Phase 1 (Dense)</div>
            <div class="metric-value" id="eval-p1-value">Loading...</div>
            <div class="metric-sub">Precision & Recall</div>
            <div class="metric-badge badge-blue">Foundation Baseline</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">RAGAS Phase 2 (Hybrid)</div>
            <div class="metric-value" id="eval-p2-value">Loading...</div>
            <div class="metric-sub">Precision & Recall</div>
            <div class="metric-badge badge-green" id="eval-p2-badge">Loading...</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">RAGAS Phase 4 (ColBERT)</div>
            <div class="metric-value" id="eval-p4-value">Loading...</div>
            <div class="metric-sub">Precision & Recall</div>
            <div class="metric-badge badge-green" id="eval-p4-badge">Loading...</div>
          </div>
        </div>'''

html = pattern.sub(replacement, html)

# 2. Add javascript to fetch and populate `/eval-results`
js_to_add = '''
async function fetchEvalResults() {
  try {
    const res = await apiFetch('/eval-results');
    
    // Format helper
    const formatScore = (obj) => {
        if (!obj || obj.context_precision === undefined) return "N/A";
        const cp = (obj.context_precision).toFixed(2);
        const cr = Math.min(1.0, obj.context_recall).toFixed(2); // Fix bounds if any
        return `P: ${cp} | R: ${cr}`;
    };

    if (res.dense) {
        document.getElementById('eval-p1-value').textContent = formatScore(res.dense);
    }
    
    if (res.hybrid) {
        document.getElementById('eval-p2-value').textContent = formatScore(res.hybrid);
        let impP = ((res.hybrid.context_precision - res.dense.context_precision) * 100).toFixed(1);
        let impR = ((Math.min(1.0, res.hybrid.context_recall) - Math.min(1.0, res.dense.context_recall)) * 100).toFixed(1);
        document.getElementById('eval-p2-badge').textContent = `Δ Precision +${impP}%`;
    }
    
    if (res.hybrid_rerank) {
        document.getElementById('eval-p4-value').textContent = formatScore(res.hybrid_rerank);
        let impP = ((res.hybrid_rerank.context_precision - res.dense.context_precision) * 100).toFixed(1);
        document.getElementById('eval-p4-badge').textContent = `Δ Precision ${impP > 0 ? '+' : ''}${impP}%`;
    }
  } catch(e) {
    console.error("Failed to load eval results", e);
  }
}
// Call it on load
fetchEvalResults();
'''

if "fetchEvalResults()" not in html:
    html = html.replace('updateHealth();', 'updateHealth();\n' + js_to_add)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated UI successfully")
