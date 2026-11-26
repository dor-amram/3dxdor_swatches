import json,os,re,difflib,collections
DB='ext/SpoolmanDB/filaments/'
def norm(s): return re.sub(r'[^a-z0-9 ]','',re.sub(r'[-_/+]',' ',(s or '').lower())).split()
cands=collections.defaultdict(list)  # brandkey -> list
BMAP={'bambu lab':'bambulab','polymaker':'polymaker','flashforge':'flashforge','esun':'esun','sunlu':'sunlu','kexcelled':'kexcelled','jayo':'jayo','creality':'creality','inslogic':'inslogic','3d fuel':'3dfuel','overture':'overture','elegoo':'elegoo','snapmaker':'snapmaker','biqu':'biqu','eryone':'eryone','protopasta':'protopasta','siraya tech':None}
for f in os.listdir(DB):
    d=json.load(open(DB+f)); key=f[:-5]
    for fl in d['filaments']:
        for c in fl.get('colors',[]):
            full=fl['name'].replace('{color_name}',c['name'])
            g=lambda k: c.get(k, fl.get(k))
            cands[key].append(dict(src='SpoolmanDB',material=fl['material'],name=full,color=c['name'],hex=c.get('hex'),hexes=c.get('hexes'),
              finish=g('finish'),pattern=g('pattern'),translucent=g('translucent'),glow=g('glow'),fill=fl.get('fill'),multi=g('multi_color_direction')))
for x in json.load(open('ext/bbl_colors.json'))['data']:
    cols=[h[1:7] for h in x['fila_color']]
    cands['bambulab'].append(dict(src='BambuStudio',material=x['fila_type'],name=x['fila_type']+' '+x['fila_color_name']['en'],color=x['fila_color_name']['en'],
        hex=cols[0],hexes=cols if len(cols)>1 else None,multi={'渐变色':'gradient','多拼色':'coaxial'}.get(x['fila_color_type']),bbl=True))
def score(it,c):
    col=norm(it.get('color')); cc=norm(c['color'])
    if not col or not cc: return 0,''
    exact=col==cc
    r=difflib.SequenceMatcher(None,' '.join(col),' '.join(cc)).ratio()
    mt=set(norm((it.get('type') or '')+' '+(it.get('sub') or ''))); cm=set(norm(c['material']+' '+c['name']))-set(cc)
    mat=len(mt&cm)/max(1,len(mt))
    base=norm(it.get('type'))[:1]; fam=bool(base) and base[0] in cm
    s=(2 if exact else r)+mat
    return s,('exact' if exact else 'fuzzy'),mat,fam
out={}; stat=collections.Counter()
for kind in ('fdm','resin'):
    for f in sorted(os.listdir('live/'+kind)):
        it=json.load(open(f'live/{kind}/{f}')); iid=f[:-5]
        bk=BMAP.get((it.get('brand') or '').lower(),'__none') or '__none'
        best=None
        for c in cands.get(bk,[]):
            sc=score(it,c)
            if sc[0] and (not best or sc[0]>best[0][0]): best=(sc,c)
        res={'id':iid,'kind':kind,'brand':it.get('brand'),'type':it.get('type'),'sub':it.get('sub'),'color':it.get('color'),'hex_now':it.get('hex'),'hex_src':it.get('hex_src')}
        if best:
            (s,how,mat,fam),c=best
            if how=='exact' and fam and mat>=0.99: q='verified'
            elif how=='exact' and fam: q='close'
            elif how=='fuzzy' and difflib.SequenceMatcher(None,' '.join(norm(it.get('color'))),' '.join(norm(c['color']))).ratio()>=0.86 and fam: q='close'
            else: q=None
            if q: res.update(q=q,match=c,score=round(s,2))
        res.setdefault('q','approx'); stat[res['q']]+=1; out[iid]=res
# same brand, other material, exact colour name
for r in out.values():
    if r['q']!='approx': continue
    bk=BMAP.get((r['brand'] or '').lower())
    if not bk: continue
    hits=[c for c in cands.get(bk,[]) if norm(c['color'])==norm(r['color']) and c.get('hex')]
    if hits: r.update(q='close',match=dict(hits[0],note='same brand, other material')); stat['approx']-=1; stat['close']+=1
# generic tier: same colour name across all brands, same material family
gen=collections.defaultdict(list)
for k,L in cands.items():
    for c in L:
        if c.get('hex') and not c.get('hexes'): gen[(' '.join(norm(c['color'])), (norm(c['material'])[:1] or [''])[0][:3])].append(c['hex'].lower())
def med(hs):
    import statistics
    rgb=[tuple(int(h[i:i+2],16) for i in (0,2,4)) for h in hs if len(h)>=6]
    return '%02x%02x%02x'%tuple(int(statistics.median(ch)) for ch in zip(*rgb))
for r in out.values():
    if r['q']!='approx': continue
    key=(' '.join(norm(r['color'])), (norm(r['type'])[:1] or [''])[0][:3])
    hs=gen.get(key) or []
    if r['kind']=='fdm' and len(hs)>=3:
        r.update(q='generic',match={'src':'SpoolmanDB median of %d brands'%len(hs),'hex':med(hs),'name':r['color']}); stat['approx']-=1; stat['generic']+=1
json.dump(out,open('match.json','w'),indent=1,ensure_ascii=False)
print(stat)
