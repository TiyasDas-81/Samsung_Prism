import os

path = r'C:\Users\Asus\Desktop\Full-Duplex-Bench\v3\run_tool_benchmark.py'
with open(path, 'r', encoding='utf-8') as f:
    data = f.read()

data = data.replace('if torch.cuda.is_available():\n            model = model.cuda()', 'import torch\n        if torch.cuda.is_available():\n            model = model.cuda()')

with open(path, 'w', encoding='utf-8') as f:
    f.write(data)

print('Patched run_tool_benchmark.py with import torch')
