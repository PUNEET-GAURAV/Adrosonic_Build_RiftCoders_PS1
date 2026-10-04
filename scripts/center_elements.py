import re

with open("src/trustrag/ui/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Add text-align center to metric cards
html = re.sub(r'(\.metric-card \{[^}]+?)(?=\})', r'\1 text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;', html)

# Add text-align center to the search area elements if needed
# We'll just center the content in the metric cards and the table headers
html = html.replace('th {', 'th { text-align: center;')
html = html.replace('td {', 'td { text-align: center;')

# Make the cards in compare grid even and centered
html = html.replace('.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }', 
                    '.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; justify-items: stretch; }')

# For the page overall, to make elements "even", we can make the main layout constrained but perfectly centered without breaking flex.
# We'll wrap the inner content of each page in a container to constrain width if it's too wide, but let's stick to full width first, or wait, if I add a max-width to `.main` instead of `.page`?
# No, `.main` is fine.

with open("src/trustrag/ui/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Updated centering logic")
