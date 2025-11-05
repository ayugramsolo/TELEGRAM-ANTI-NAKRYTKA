import os

def load_keys(path):
    if not os.path.exists(path):
        return set()
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_key(path, key):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(key + '\n')
