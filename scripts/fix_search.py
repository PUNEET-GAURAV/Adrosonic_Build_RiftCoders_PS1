import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

pattern = r'if \(insuranceMode\) \{.*?\}'

replacement = '''if (insuranceMode) {
        payload.filters = payload.filters || {};
        payload.filters.category = payload.filters.category || [];
        payload.filters.category.push('insurance');
      }'''

html = re.sub(pattern, replacement, html, flags=re.DOTALL)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed search payload bug.')
