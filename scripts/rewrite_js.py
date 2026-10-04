import re

path = "src/trustrag/ui/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

new_runSearch = """async function runSearch() {
  const query = document.getElementById('search-query').value.trim();
  if (!query) return;
  const topK = parseInt(document.getElementById('topk-select').value);
  const compare = document.getElementById('compare-toggle').checked;
  const routerOn = document.getElementById('router-toggle').checked;
  const btn = document.getElementById('search-btn');
  const container = document.getElementById('search-results');
  const routerPanel = document.getElementById('router-panel');

  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Searching...';
  container.innerHTML = renderSkeletons();
  routerPanel.style.display = 'none';

  try {
    const filterValue = document.getElementById("metadata-filter") ? document.getElementById("metadata-filter").value : "";
    const payload = { query: query, mode: currentMode, top_k: topK, route: routerOn ? 'auto' : 'off' };
    if (filterValue !== "") {
      payload.filters = { category: [filterValue] };
    }

    let renderRes = null;
    if (compare && currentMode !== "dense") {
      const densePayload = { ...payload, mode: "dense" };
      const [denseRes, targetRes] = await Promise.all([
        apiFetch("/search", {method:"POST", body: JSON.stringify(densePayload)}),
        apiFetch("/search", {method:"POST", body: JSON.stringify(payload)})
      ]);
      container.innerHTML = renderCompare(denseRes, targetRes, currentMode);
      renderRes = targetRes;
    } else {
      const res = await apiFetch("/search", {method:"POST", body: JSON.stringify(payload)});
      container.innerHTML = renderSingle(res, currentMode);
      renderRes = res;
    }

    if (renderRes && renderRes.route_result && renderRes.route_result.strategy !== 'off') {
      const rr = renderRes.route_result;
      let phtml = `<div style="background: #1e293b; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; gap: 16px;">`;
      if (rr.strategy === "fallback") {
          phtml += `<div><strong style="color:#fbbf24">Intent Router:</strong> Ambiguous Query. Fell back to global search.`;
          if (renderRes.needs_clarification) phtml += `<div style="margin-top:4px; font-size: 13px; color: #94a3b8">Did you mean: ${renderRes.clarification_options.join(', ')}?</div>`;
          phtml += `</div>`;
      } else {
          phtml += `<div>
              <strong style="color:#34d399">Intent Router:</strong> Detected Domain: <span style="background:#059669; color:#fff; padding: 2px 6px; border-radius: 4px; font-size:12px; font-family:monospace">${rr.domain}</span>
              <span style="color: #94a3b8; font-size: 13px; margin-left: 8px;">(Confidence: ${(rr.confidence*100).toFixed(0)}%)</span>
              </div>
              <div style="font-size: 13px; color: #94a3b8;">
                Latency: <strong>${rr.router_ms.toFixed(2)} ms</strong> | Retries: ${rr.retries}
              </div>`;
      }
      phtml += `</div>`;
      routerPanel.innerHTML = phtml;
      routerPanel.style.display = 'block';
    }

  } catch(e) {
    container.innerHTML = `<div class="alert alert-danger">Request failed: ${e.message}</div>`;
  }

  btn.disabled = false;
  btn.innerHTML = `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="14" height="14"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35" stroke-linecap="round"/></svg> Search`;
}
"""

html = re.sub(r"async function runSearch\(\) \{.*?\n\}\n", new_runSearch, html, flags=re.DOTALL)

# Cleanup the leftover broken block I injected earlier
html = re.sub(r"      // Render Router Panel.*?if \(compare && currentMode !== \"dense\"\) \{", '      if (compare && currentMode !== "dense") {', html, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Rewrote runSearch completely!")
