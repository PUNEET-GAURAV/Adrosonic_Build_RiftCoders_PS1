import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

checkbox_html = '''
              <label class="check-row mt" style="margin-top:20px; margin-left:15px;">
                <input type="checkbox" id="insurance-mode"> Enforce Strict Insurance Routing
              </label>'''

# 1. Inject the checkbox next to compare-toggle
pattern1 = r'(<input type="checkbox" id="compare-toggle">.*?</label>)'
if 'id="insurance-mode"' not in html:
    html, count = re.subn(pattern1, r'\1' + checkbox_html, html, flags=re.DOTALL)
    print(f'Injected checkbox: {count} matches')

# 2. Fix the JS to handle if the element is missing
pattern2 = r"const insuranceMode = document.getElementById\('insurance-mode'\)\.checked;"
replacement2 = "const _im = document.getElementById('insurance-mode');\n    const insuranceMode = _im ? _im.checked : false;"

html, count2 = re.subn(pattern2, replacement2, html)
print(f'Fixed JS handler: {count2} matches')

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
