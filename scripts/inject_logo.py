import base64

image_path = r'C:/Users/puneet/.gemini/antigravity/brain/66fc9460-273e-4f3f-90e1-647ca0623590/.user_uploaded/media_1791090808291.png'
with open(image_path, 'rb') as f:
    encoded = base64.b64encode(f.read()).decode('utf-8')

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = '''<div class="logo-icon">
          <svg fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/></svg>
        </div>
        <div class="logo-text">
          <strong>TrustRAG</strong>
          <span>Adrosonic</span>
        </div>'''

replacement = f'''<img src="data:image/png;base64,{encoded}" alt="TrustRAG Logo" style="height: 44px; width: auto; object-fit: contain; margin-left: -10px;">'''

if target in html:
    html = html.replace(target, replacement)
    with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Replaced logo with image.')
else:
    print('Target not found in HTML. Check exactly how the logo is structured.')
