import re

with open('src/trustrag/assembly.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'generator = LocalGPUGenerator("Qwen/Qwen2.5-0.5B-Instruct")',
    'generator = LocalGPUGenerator("HuggingFaceTB/SmolLM2-135M-Instruct")'
)

with open('src/trustrag/assembly.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Updated assembly.py')
