import base64
import re

image_path = r'C:/Users/puneet/.gemini/antigravity/brain/66fc9460-273e-4f3f-90e1-647ca0623590/.user_uploaded/media_1791090808291.png'
with open(image_path, 'rb') as f:
    encoded = base64.b64encode(f.read()).decode('utf-8')

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace everything inside <div class="sidebar-logo"> ... </div>
pattern = r'(<div class="sidebar-logo">\s*)<div class="logo-mark">.*?(</div>\s*<nav)'

replacement = f'\\1<img src="data:image/png;base64,{encoded}" alt="TrustRAG Logo" style="height: 48px; width: auto; object-fit: contain; margin-left: 5px; max-width: 100%;">\\2'

html, count = re.subn(pattern, replacement, html, flags=re.DOTALL)
print(f'Replaced {count} occurrences.')

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
