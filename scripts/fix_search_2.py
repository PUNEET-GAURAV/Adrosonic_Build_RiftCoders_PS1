with open('src/trustrag/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = '''if (insuranceMode) {
        payload.filters = payload.filters || {};
        payload.filters.category = payload.filters.category || [];
        payload.filters.category.push('insurance');
      };
        payload.filters.tenant = 'adrosonic';
        payload.filters.audience = 'agents';
    }'''

replacement = '''if (insuranceMode) {
        payload.filters = payload.filters || {};
        payload.filters.category = payload.filters.category || [];
        payload.filters.category.push('insurance');
      }'''

html = html.replace(target, replacement)

with open('src/trustrag/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Fixed search payload bug correctly.')
