import base64
import re

with open('src/trustrag/ui/trustrag-logo.png', 'rb') as img_file:
    b64_string = base64.b64encode(img_file.read()).decode('utf-8')

data_uri = f'data:image/png;base64,{b64_string}'

with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the img src attribute
html = re.sub(
    r'<img src="trustrag-logo\.png"', 
    f'<img src="{data_uri}"', 
    html
)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Logo embedded as base64!')
