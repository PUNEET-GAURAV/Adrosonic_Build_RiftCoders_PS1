with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# For Dense
search_dense = """<div class="card-body">${(dense.results||[]).map"""
rep_dense = """<div class="card-body">${dense.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px; font-family:monospace">Retrieved in ${JSON.stringify(dense.timings_ms)} &middot; request_id ${dense.request_id}</div>` : ''}${(dense.results||[]).map"""
html = html.replace(search_dense, rep_dense)

# For Target
search_target = """<div class="card-body">${(target.results||[]).map"""
rep_target = """<div class="card-body">${target.timings_ms ? `<div class="text-sm text-muted" style="margin-bottom:10px; font-family:monospace">Retrieved in ${JSON.stringify(target.timings_ms)} &middot; request_id ${target.request_id}</div>` : ''}${(target.results||[]).map"""
html = html.replace(search_target, rep_target)

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated via simple substring replace")
