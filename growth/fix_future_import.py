import pathlib

for base in ['c:/AI-Project - Copia/growth', 'c:/AI-Project/growth']:
    for fn in ['fanvue_api.py', 'fanvue_dm.py']:
        p = pathlib.Path(base) / fn
        if not p.exists():
            continue
        lines = p.read_text(encoding='utf-8').splitlines()
        # Remove any misplaced header
        clean = [l for l in lines if not l.startswith('import sys') and not l.startswith('if hasattr(sys.stdout') and not l.startswith('    sys.stdout.reconfigure') and not l.startswith('    sys.stderr.reconfigure')]
        # Find future annotations
        future_idx = -1
        for i, l in enumerate(clean):
            if 'from __future__ import annotations' in l:
                future_idx = i
                break
        if future_idx != -1:
            clean.insert(future_idx + 1, 'import sys\nif hasattr(sys.stdout, "reconfigure"):\n    sys.stdout.reconfigure(encoding="utf-8", errors="replace")\nif hasattr(sys.stderr, "reconfigure"):\n    sys.stderr.reconfigure(encoding="utf-8", errors="replace")')
        else:
            clean.insert(0, 'import sys\nif hasattr(sys.stdout, "reconfigure"):\n    sys.stdout.reconfigure(encoding="utf-8", errors="replace")\nif hasattr(sys.stderr, "reconfigure"):\n    sys.stderr.reconfigure(encoding="utf-8", errors="replace")')
        p.write_text('\n'.join(clean) + '\n', encoding='utf-8')
        print(f'Fixed future import in {base}/{fn}')
