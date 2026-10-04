with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = '      <div class="result-id">${r.passage_id}</div>\n    </div>`;\n  }'
replacement = '''      <div class="result-id">${r.passage_id}</div>
      <div style="margin-top:10px; font-size:12px;">
          <button onclick="submitFeedback('${r.passage_id}', 1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer;" title="Helpful">👍</button>
          <button onclick="submitFeedback('${r.passage_id}', -1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer; margin-left:4px;" title="Not Helpful">👎</button>
      </div>
    </div>`;
  }'''

html = html.replace(target, replacement)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Injected feedback buttons.')
