import pathlib
import sys

for base in ['c:/AI-Project - Copia/growth', 'c:/AI-Project/growth']:
    for fn in ['fanvue_api.py', 'fanvue_dm.py', 'ledger.py', 'syndicate.py', 'ig_engage.py']:
        p = pathlib.Path(base) / fn
        if not p.exists():
            continue
        t = p.read_text(encoding='utf-8')
        if 'sys.stdout.reconfigure' not in t:
            header = 'import sys\nif hasattr(sys.stdout, "reconfigure"):\n    sys.stdout.reconfigure(encoding="utf-8", errors="replace")\nif hasattr(sys.stderr, "reconfigure"):\n    sys.stderr.reconfigure(encoding="utf-8", errors="replace")\n\n'
            p.write_text(header + t, encoding='utf-8')
            print(f'Added UTF8 to {base}/{fn}')
