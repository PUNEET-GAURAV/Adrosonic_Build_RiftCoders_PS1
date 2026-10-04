import os
import re

path = "src/trustrag/ui/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove the broken router rendering block from where it is now
broken_block = """
      // Render Router Panel
      const routerPanel = document.getElementById('router-panel');
      const renderRes = typeof targetRes !== 'undefined' ? targetRes : (typeof res !== 'undefined' ? res : null);
      if (renderRes && renderRes.route_result && renderRes.route_result.strategy !== 'off') {
        const rr = renderRes.route_result;
        let html = `<div style="background: #1e293b; padding: 12px 16px; border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; gap: 16px;">`;
        if (rr.strategy === "fallback") {
            html += `<div><strong style="color:#fbbf24">Intent Router:</strong> Ambiguous Query. Fell back to global search.`;
            if (renderRes.needs_clarification) html += `<div style="margin-top:4px; font-size: 13px; color: #94a3b8">Did you mean: ${renderRes.clarification_options.join(', ')}?</div>`;
            html += `</div>`;
        } else {
            html += `<div>
                <strong style="color:#34d399">Intent Router:</strong> Detected Domain: <span style="background:#059669; color:#fff; padding: 2px 6px; border-radius: 4px; font-size:12px; font-family:monospace">${rr.domain}</span>
                <span style="color: #94a3b8; font-size: 13px; margin-left: 8px;">(Confidence: ${(rr.confidence*100).toFixed(0)}%)</span>
                </div>
                <div style="font-size: 13px; color: #94a3b8;">
                  Latency: <strong>${rr.router_ms} ms</strong> | Retries: ${rr.retries}
                </div>`;
        }
        html += `</div>`;
        routerPanel.innerHTML = html;
        routerPanel.style.display = 'block';
      } else {
        routerPanel.style.display = 'none';
      }

      if (compare && currentMode !== "dense") {"""

html = html.replace(broken_block, '      if (compare && currentMode !== "dense") {')

# Add it back after the if block
fixed_block = """
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

      // Render Router Panel
      const routerPanel = document.getElementById('router-panel');
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
                  Latency: <strong>${rr.router_ms} ms</strong> | Retries: ${rr.retries}
                </div>`;
        }
        phtml += `</div>`;
        routerPanel.innerHTML = phtml;
        routerPanel.style.display = 'block';
      } else {
        routerPanel.style.display = 'none';
      }
"""

old_target_block = """
      if (compare && currentMode !== "dense") {
        const densePayload = { ...payload, mode: "dense" };
        const [denseRes, targetRes] = await Promise.all([
          apiFetch("/search", {method:"POST", body: JSON.stringify(densePayload)}),
          apiFetch("/search", {method:"POST", body: JSON.stringify(payload)})
        ]);
        container.innerHTML = renderCompare(denseRes, targetRes, currentMode);
      } else {
        const res = await apiFetch("/search", {method:"POST", body: JSON.stringify(payload)});
        container.innerHTML = renderSingle(res, currentMode);
      }
"""

html = html.replace(old_target_block.strip('\n'), fixed_block.strip('\n'))

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Fixed JS!")
