with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add feedback rendering to renderSingle and renderCompare
def inject_feedback(match):
    req_var = match.group(1)
    return f"""
        <div style="margin-top:10px; font-size:12px;">
            <button onclick="submitFeedback('${{{req_var}}}', '${{r.passage_id}}', 1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer;" title="Helpful">👍</button>
            <button onclick="submitFeedback('${{{req_var}}}', '${{r.passage_id}}', -1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer; margin-left:4px;" title="Not Helpful">👎</button>
        </div>
      </div>
"""

import re
# We need to replace the end of the passage rendering loop. 
# It currently has: `</div>\n    }).join('');`
# We'll inject the feedback HTML right before the `</div>`
html = re.sub(r'(</div>\n\s*\}\)\.join\(\'\'\);)', r'        <div style="margin-top:10px; font-size:12px;"><button onclick="submitFeedback(\'${reqId}\', \'${r.passage_id}\', 1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer;" title="Helpful">👍</button> <button onclick="submitFeedback(\'${reqId}\', \'${r.passage_id}\', -1)" style="background:none; border:1px solid var(--border); border-radius:4px; padding:2px 6px; cursor:pointer; margin-left:4px;" title="Not Helpful">👎</button></div>\n      \1', html)

js_func = """
  async function submitFeedback(reqId, passageId, score) {
    try {
      await apiFetch("/feedback", {
        method: "POST",
        body: JSON.stringify({request_id: reqId, passage_id: passageId, score: score})
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
