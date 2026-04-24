#!/usr/bin/env python3
"""
regen_bootstrap.py
Run this from your repo root to regenerate bootstrap.py from your local files.

Usage:
    cd ai-data-quality-accelerator
    source .venv/bin/activate
    python regen_bootstrap.py
"""
import os, base64
from pathlib import Path

ROOT = Path(__file__).parent
files = {}

for root, dirs, filenames in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'node_modules')]
    for fname in filenames:
        fpath = Path(root) / fname
        # Skip the regen script itself and any existing bootstrap
        if fname in ('regen_bootstrap.py',):
            continue
        try:
            rel = str(fpath.resolve().relative_to(ROOT.resolve()))
        except ValueError:
            continue  # skip files outside repo root (e.g. symlinked Python executables)
        try:
            files[rel] = base64.b64encode(fpath.read_bytes()).decode()
        except Exception as e:
            print(f"  skipped: {rel} ({e})")

lines = [
    '#!/usr/bin/env python3',
    '"""bootstrap.py — python bootstrap.py --force"""',
    'import base64, sys',
    'from pathlib import Path',
    'ROOT=Path(__file__).parent',
    'FORCE="--force" in sys.argv',
    'FILES={',
]

for rel_path, b64 in sorted(files.items()):
    chunks = [b64[i:i+80] for i in range(0, len(b64), 80)]
    lines.append(f'    {repr(rel_path)}:({"".join(repr(c) for c in chunks)}),')

lines += [
    '}',
    'def main():',
    '    c=u=s=0',
    '    for p,b in FILES.items():',
    '        dest=ROOT/p; dest.parent.mkdir(parents=True,exist_ok=True)',
    '        if dest.exists() and not FORCE: s+=1; continue',
    '        ex=dest.exists(); dest.write_bytes(base64.b64decode(b))',
    '        if ex: u+=1; print(f"  updated   {p}")',
    '        else: c+=1; print(f"  created   {p}")',
    '    print(f"\\nDone: {c} created, {u} updated, {s} skipped")',
    'if __name__=="__main__": main()',
]

out = ROOT / 'bootstrap.py'
out.write_text('\n'.join(lines))
size_kb = out.stat().st_size / 1024
print(f"✅ bootstrap.py regenerated: {size_kb:.1f} KB, {len(files)} files")
print(f"   Output: {out}")
