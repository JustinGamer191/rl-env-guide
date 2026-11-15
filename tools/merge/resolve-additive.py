#!/usr/bin/env python3
"""resolve-additive.py <file>... : resolve diff3 conflict hunks whose base section is empty (both sides only added lines)
by keeping ours then theirs. Leaves any other hunk untouched and exits 1 if one remains."""
import sys, re
left = 0
for f in sys.argv[1:]:
    src = open(f).read().split('\n')
    out, i, n = [], 0, 0
    while i < len(src):
        if src[i].startswith('<<<<<<< '):
            j = i + 1; ours = []
            while not src[j].startswith('||||||| '): ours.append(src[j]); j += 1
            j += 1; base = []
            while src[j] != '=======': base.append(src[j]); j += 1
            j += 1; theirs = []
            while not src[j].startswith('>>>>>>> '): theirs.append(src[j]); j += 1
            if not any(b.strip() for b in base):
                out += ours + theirs; n += 1
            else:
                out += src[i:j + 1]; left += 1
            i = j + 1
        else:
            out.append(src[i]); i += 1
    open(f, 'w').write('\n'.join(out))
    print(f'{f}: {n} additive hunks resolved')
print(f'non-additive hunks left: {left}')
sys.exit(1 if left else 0)
