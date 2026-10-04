import os

path = r'C:\Users\Asus\AppData\Roaming\Python\Python311\site-packages\nemo\utils\tar_utils.py'
with open(path, 'r', encoding='utf-8') as f:
    data = f.read()

data = data.replace('tar.extract(member, extract_to, filter="data")', 'tar.extract(member, extract_to)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(data)

print('Patched tar_utils.py')
