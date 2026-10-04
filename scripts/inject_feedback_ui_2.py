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

js_func = """
  async function submitFeedback(passageId, score) {
    try {
      await apiFetch("/feedback", {
        method: "POST",
        body: JSON.stringify({request_id: "ui-req-" + Date.now(), passage_id: passageId, score: score})
      });
      alert(score === 1 ? 'Thanks for the positive feedback!' : 'Thanks, we will improve this result.');
    } catch(e) {
      console.error(e);
    }
  }
"""

if 'submitFeedback' not in html:
    html = html.replace('</script>', js_func + '\n  </script>')
    with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Added feedback JS.')
else:
    print('Feedback JS already exists.')
