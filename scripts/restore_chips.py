import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

chips_html = '''
              <!-- Quick Domain Search Chips -->
              <div style="margin-bottom: 20px;">
                  <label style="display:block; margin-bottom:8px; font-size:12px; color:var(--text-muted)">Quick Domain Queries:</label>
                  <div style="display:flex; gap:8px; flex-wrap:wrap;">
                      <button class="btn" style="background:rgba(59,130,246,0.1); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:4px 12px; border-radius:12px; font-size:12px;" onclick="document.getElementById('search-query').value='What documents are required for KYC when opening a bank account?'; runSearch()">🏦 KYC / Onboarding</button>
                      <button class="btn" style="background:rgba(16,185,129,0.1); color:#34d399; border:1px solid rgba(16,185,129,0.3); padding:4px 12px; border-radius:12px; font-size:12px;" onclick="document.getElementById('search-query').value='What is the interest rate for a fixed deposit?'; runSearch()">💰 Finance / Interest</button>
                      <button class="btn" style="background:rgba(245,158,11,0.1); color:#fbbf24; border:1px solid rgba(245,158,11,0.3); padding:4px 12px; border-radius:12px; font-size:12px;" onclick="document.getElementById('search-query').value='What does the comprehensive car insurance cover?'; runSearch()">🚗 Auto Insurance</button>
                      <button class="btn" style="background:rgba(139,92,246,0.1); color:#a78bfa; border:1px solid rgba(139,92,246,0.3); padding:4px 12px; border-radius:12px; font-size:12px;" onclick="document.getElementById('search-query').value='How to file a health insurance claim?'; runSearch()">🏥 Health Claims</button>
                  </div>
              </div>
'''

target_search = '<input type="text" id="search-query" value="How does a vector database improve retrieval augmented generation?" />\n              </div>\n            </div>'

if 'Quick Domain Queries' not in html:
    html = html.replace(target_search, target_search + '\n' + chips_html)
    with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Restored Quick Domain Queries.')
else:
    print('Already exists.')
