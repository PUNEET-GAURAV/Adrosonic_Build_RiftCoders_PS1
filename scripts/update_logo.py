import re

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_logo = '''<div class="sidebar-logo" style="justify-content: center; padding: 12px 16px;">
      <img src="trustrag-logo.png" alt="TrustRAG" style="max-width: 100%; height: 45px; object-fit: contain;">
    </div>'''

html = re.sub(
    r'<div class="sidebar-logo">.*?</div>\s*</div>', 
    new_logo, 
    html, 
    flags=re.DOTALL
)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated logo")
