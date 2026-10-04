import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update metadata filter options using regex for robustness
html = re.sub(
    r'<select id="metadata-filter"[^>]*>.*?</select>',
    r'<select id="metadata-filter" style="width: 100%; padding: 8px; border-radius: 4px; background: var(--bg); border: 1px solid #333; color: #fff;">\n'
    r'  <option value="">All passages (No Filter)</option>\n'
    r'  <option value="banking">Category: Banking (Custom Data)</option>\n'
    r'  <option value="NUMERIC">Category: Numeric (MS MARCO)</option>\n'
    r'  <option value="DESCRIPTION">Category: Description (MS MARCO)</option>\n'
    r'</select>',
    html,
    flags=re.DOTALL
)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated options in UI')
