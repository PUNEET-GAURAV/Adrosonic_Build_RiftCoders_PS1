import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace for Dense
html = re.sub(
    r'(<div class="card"><div class="card-header"><h2>Dense Baseline</h2><span class="tag">Latency: \$\{denseTime\}</span></div>\s*<div class="card-body">)(\$\(dense\.results\|\|\[\]\)\.map\(r => renderResult\(r\)\)\.join\(""\))',
    r'\1${dense.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px">Retrieved in ${JSON.stringify(dense.timings_ms)} &middot; request_id ${dense.request_id}</div>` : \'\'}\2',
    html
)

# Replace for Target
html = re.sub(
    r'(<div class="card"><div class="card-header"><h2>\$\{modeLabel\(mode\)\}</h2><span class="tag tag-success">Latency: \$\{targetTime\}</span></div>\s*<div class="card-body">)(\$\(target\.results\|\|\[\]\)\.map\(r => renderResult\(r\)\)\.join\(""\))',
    r'\1${target.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px">Retrieved in ${JSON.stringify(target.timings_ms)} &middot; request_id ${target.request_id}</div>` : \'\'}\2',
    html
)

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated via flexible regex")
