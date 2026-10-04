import re
with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

html = re.sub(r'max-width: 1200px; margin: 0 auto; width: 100%;', '', html)
html = html.replace('.page { display: none; flex: 1; padding: 28px; overflow-y: auto;  }', '.page { display: none; flex: 1; padding: 28px; overflow-y: auto; }')

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Reverted max-width")
