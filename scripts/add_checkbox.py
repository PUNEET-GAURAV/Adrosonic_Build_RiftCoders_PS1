with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

checkbox_html = '''
              <label class="check-row mt" style="margin-top:20px; margin-left:15px;">
                <input type="checkbox" id="insurance-mode"> Enforce Strict Insurance Routing
              </label>
'''

if 'id="insurance-mode"' not in html:
    html = html.replace('<input type="checkbox" id="compare-toggle"> Compare dense vs selected mode\n              </label>',
                        '<input type="checkbox" id="compare-toggle"> Compare dense vs selected mode\n              </label>' + checkbox_html)
    with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Added insurance checkbox.')
else:
    print('Checkbox already exists.')
