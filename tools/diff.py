"""Compare a freshly generated swatches.json with the published one.
Usage: python3 tools/diff.py OLD NEW   -> prints a change summary; exit 0 = no change, 1 = changed.
Ignores the 'updated' date and the per-item key 'k' (it is a running index)."""
import json, sys
def load(p):
    d = json.load(open(p, encoding='utf8'))
    return {(i['type'], i.get('fin') or '', i['name']): {k: v for k, v in i.items() if k != 'k'} for i in d['items']}
old, new = load(sys.argv[1]), load(sys.argv[2])
lab = lambda k: '%s %s %s' % (k[0], k[1], k[2])
added = sorted(set(new) - set(old)); removed = sorted(set(old) - set(new))
changed = []
for k in sorted(set(old) & set(new)):
    a, b = old[k], new[k]
    diffs = [f for f in sorted(set(a) | set(b)) if a.get(f) != b.get(f)]
    if diffs: changed.append((k, ['%s: %s -> %s' % (f, a.get(f), b.get(f)) for f in diffs]))
print('added %d, removed %d, changed %d' % (len(added), len(removed), len(changed)))
for k in added: print('  + ' + lab(k), '|', new[k].get('name_he', '(no Hebrew name)'), '|', new[k].get('hex'), '| colour source:', 'product data' if new[k].get('maker') else 'approximate', '|', new[k]['avail'])
for k in removed: print('  - ' + lab(k))
for k, d in changed: print('  ~ ' + lab(k) + ': ' + '; '.join(d))
sys.exit(1 if (added or removed or changed) else 0)
