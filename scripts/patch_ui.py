import os

path = "src/trustrag/ui/index.html"
with open(path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    '<input type="checkbox" id="compare-toggle"> Compare dense vs selected mode\n            </label>',
    '<input type="checkbox" id="compare-toggle"> Compare dense vs selected mode\n            </label>\n            <label class="check-row mt" style="margin-top:20px; margin-left:20px;">\n              <input type="checkbox" id="router-toggle" checked> Intent Router\n            </label>'
)

html = html.replace(
    '<!-- Results -->\n      <div id="search-results"></div>',
    '<!-- Router -->\n      <div id="router-panel" style="margin: 0 20px 10px; display: none;"></div>\n      <!-- Results -->\n      <div id="search-results"></div>'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("Patched!")
