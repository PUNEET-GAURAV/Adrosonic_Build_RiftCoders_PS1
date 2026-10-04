with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

js_code = '''
      if (res.hybrid && document.getElementById('eval-p2-value')) {
          document.getElementById('eval-p2-value').textContent = formatScore(res.hybrid);
          let impP = ((res.hybrid.context_precision - res.dense.context_precision) * 100).toFixed(1);
          document.getElementById('eval-p2-badge').textContent = `Diff ${impP > 0 ? '+' : ''}${impP}%`;
      }
      
      if (res.hybrid_rerank && document.getElementById('eval-p4-value')) {
          document.getElementById('eval-p4-value').textContent = formatScore(res.hybrid_rerank);
          let impP2 = ((res.hybrid_rerank.context_precision - res.dense.context_precision) * 100).toFixed(1);
          document.getElementById('eval-p4-badge').textContent = `Diff ${impP2 > 0 ? '+' : ''}${impP2}%`;
      }
'''

start = html.find('if (res.hybrid && document.getElementById')
end = html.find('} catch', start)

if start != -1 and end != -1:
    html = html[:start] + js_code.strip() + '\n    ' + html[end:]
    with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Patched JS fetchEvalResults.')
