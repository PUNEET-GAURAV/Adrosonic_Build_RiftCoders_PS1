import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace padding in .page to add responsive horizontal padding
html = re.sub(
    r'\.page \{ display: none; flex: 1; padding: 28px; overflow-y: auto; \}',
    r'.page { display: none; flex: 1; padding: 40px 10%; overflow-y: auto; }',
    html
)

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated padding")
