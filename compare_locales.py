import json

# Read both locale directories
for lang in ['zh', 'en', 'id']:
    with open(f'locales/{lang}.json') as f:
        root = json.load(f)
    with open(f'frontend/locales/{lang}.json') as f:
        front = json.load(f)
    print(f"=== {lang} ===")
    print(f"Root keys: {len(root)} top-level")
    print(f"Frontend keys: {len(front)} top-level")
    
    # Flatten nested keys
    def flatten(d, prefix=''):
        keys = set()
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys |= flatten(v, full)
            else:
                keys.add(full)
        return keys
    
    root_keys = flatten(root)
    front_keys = flatten(front)
    
    only_root = root_keys - front_keys
    only_front = front_keys - root_keys
    common = root_keys & front_keys
    
    print(f"  Total leaf keys: root={len(root_keys)}, frontend={len(front_keys)}, common={len(common)}")
    if only_root:
        print(f"  Only in root: {sorted(only_root)}")
    if only_front:
        print(f"  Only in frontend: {sorted(only_front)}")