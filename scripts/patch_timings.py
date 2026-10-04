import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Fix renderSingle
html = html.replace('A\xa0 request_id', '&middot; request_id')
html = html.replace('A request_id', '&middot; request_id')
html = html.replace('A\u00A0 request_id', '&middot; request_id')

# We want to replace the body of renderCompare to include the timing detailed string for both sides
pattern = r'(<div class="card"><div class="card-header"><h2>Dense Baseline</h2><span class="tag">Latency: \$\{denseTime\}</span></div>\s*<div class="card-body">)(\$\(dense\.results\|\|\[\]\)\.map\(r => renderResult\(r\)\)\.join\(""\))(</div></div>\s*<div class="card"><div class="card-header"><h2>\$\{modeLabel\(mode\)\}</h2><span class="tag tag-success">Latency: \$\{targetTime\}</span></div>\s*<div class="card-body">)(\$\(target\.results\|\|\[\]\)\.map\(r => renderResult\(r\)\)\.join\(""\))(</div></div>)'

def replace_fn(m):
    # Add dense timing
    dense_timing = """${dense.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px">Retrieved in ${JSON.stringify(dense.timings_ms)} &middot; request_id ${dense.request_id}</div>` : ''}"""
    # Add target timing
    target_timing = """${target.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px">Retrieved in ${JSON.stringify(target.timings_ms)} &middot; request_id ${target.request_id}</div>` : ''}"""
    
    return m.group(1) + dense_timing + m.group(2) + m.group(3) + target_timing + m.group(4) + m.group(5)

html = re.sub(pattern, replace_fn, html)

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Patched renderCompare and renderSingle")
