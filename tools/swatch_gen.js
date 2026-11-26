// Build customer-safe swatch data: no brand, cost, grams or links.
const fs=require('fs'), vm=require('vm');
const ctx={}; vm.createContext(ctx); vm.runInContext(fs.readFileSync(__dirname+'/calc.js','utf8')+';this.Calc=Calc;',ctx); const Calc=ctx.Calc;
const M=JSON.parse(fs.readFileSync('match.json'));
// manual maker-hex overrides from research: {itemId:{hex:'#rrggbb',hexes?:[...],src:'url'}}
const OV=fs.existsSync(__dirname+'/hex_overrides.json')?JSON.parse(fs.readFileSync(__dirname+'/hex_overrides.json')):{};
const NAMED={black:'1d1d1f',white:'f4f4f2',gray:'8a8d91',grey:'8a8d91',silver:'b8bcc2',gold:'c9a13b',red:'c8102e',blue:'1f4fbf',green:'2e8b57',yellow:'f2c500',orange:'f07d1a',purple:'6b3fa0',pink:'f19cbb',brown:'7a4a2a',beige:'d8c7a6',copper:'b87333',bronze:'a97142',teal:'1f8a8a',cyan:'00a6c8',magenta:'c2187a'};
const EXCL=/extruder cleaner|came with printer|spool 110g|spool 75g|support|^pva$|12 colors|4 types/i;
const out=[]; const drop=[];
for(const kind of ['fdm','resin']) for(const f of fs.readdirSync('live/'+kind).sort()){
  const it=JSON.parse(fs.readFileSync(`live/${kind}/${f}`)), id=f.slice(0,-5), m=M[id];
  const color=kind==='resin'?(it.sub||''):(it.color||''); const sub=kind==='resin'?'':(it.sub||'');
  const label=[it.type,sub,color].join(' ');
  if(EXCL.test(sub)||EXCL.test(color)||EXCL.test(it.type||'')||it.type==='CLN'||it.type==='PVA'||!color){ drop.push([id,label,'excluded']); continue; }
  const rolls=it.rolls||[]; const live=rolls.filter(r=>r.status==='open'||r.status==='sealed'); const aw=rolls.some(r=>r.status==='awaiting');
  let net=0; live.forEach(r=>{ const v=Calc.remN(r); if(typeof v==='number') net+=v; });
  let avail = live.length ? (net<200 && !live.some(r=>r.status==='sealed') ? 'limited':'in') : (aw?'order':null);
  if(!avail){ drop.push([id,label,'finished']); continue; }
  let hex=(it.hex||'').replace('#',''), hexes=null, q=m.q, finish=null, pattern=null, translucent=false, fill=null;
  if(m.match){ if(m.match.hex) hex=m.match.hex.replace('#','').slice(0,6); if(m.match.hexes) hexes=m.match.hexes.map(h=>h.replace('#','').slice(0,6));
    if(m.match.note!=='same brand, other material'){ // effects only from the same product family, never across materials
      finish=m.match.finish||null; pattern=m.match.pattern||null; translucent=!!m.match.translucent; fill=m.match.fill||null; } }
  if(!hexes && /\//.test(color)){ const parts=color.split('/').map(s=>s.trim().toLowerCase().split(/\s+/).pop()); if(parts.every(p=>NAMED[p])) hexes=parts.map(p=>NAMED[p]); }
  if(OV[id]){ hex=OV[id].hex.replace('#',''); if(OV[id].hexes) hexes=OV[id].hexes.map(h=>h.replace('#','')); q='verified'; }
  // The Hub is the source of truth for colour when it records where the colour came from.
  // maker / measured / third-party -> product data; manual (Dor's own pick) -> used but labelled approximate; sheet / name / none -> matcher result above.
  const HS=it.hex_src, clean=h=>String(h).replace('#','').slice(0,6);
  if(it.hex && ['maker','measured','third-party','manual'].includes(HS)){ hex=clean(it.hex); if(it.hexes&&it.hexes.length>1) hexes=it.hexes.map(clean); /* else keep multi-colour hexes found above */ q=(HS==='manual')?'approx':'verified'; }
  const t=(sub+' '+color+' '+(it.type||'')).toLowerCase();
  let fx='solid';
  if(/\bcf\b|carbon/.test(t)||fill==='carbon fiber') fx='cf';
  else if(/\bgf\b|glass fib/.test(t)||fill==='glass fiber') fx='gf';
  else if(/wood|bamboo|walnut|cherry|ebony|pine|pearwood/.test(t)||fill==='wood') fx='wood';
  else if(/marble|stone|cement|chip/.test(t)||pattern==='marble') fx='marble';
  else if(/glitter|sparkle|galaxy|star|shimmer/.test(t)||pattern==='sparkle') fx='sparkle';
  else if(/color shift|colour shift|chameleon|nebula|rose quartz/.test(t)) fx='shift';
  else if(/metal|stainless|steel|metallic|burnt titanium|heavy metal/.test(t)) fx='metal';
  else if(/gradient|rainbow/.test(t)) fx='gradient';
  else if(/silk|esilk/.test(t)) fx=(hexes&&hexes.length>1)?'silkmulti':'silk';
  else if(/translucent|transparent|clear|crystal/.test(t)||translucent) fx='clear';
  else if(/matte/.test(t)||finish==='matte') fx='matte';
  else if(/tpu|flex|peba|elastic|morphlex/.test(t)) fx='satin';
  if(kind==='resin' && fx==='solid') fx='resin';
  if(fx==='solid' && hexes && hexes.length>1) fx='dual';
  // customer-facing finish label (no brand product-line names)
  let fin=sub.replace(/\b(PolyLite|PolyTerra|Panchroma|PolyMax|Fiberon|PolySonic|PolyFlex|PolySmooth|SnapSpeed|Hyper|LikeSilk|MorPhlex)\b™?/gi,'').replace(/\be(ASA|PLA|PETG|TPU|ABS)(\+?)/g,'$1$2').replace(/\(.*?\)/g,'').replace(/\beSilk\b/i,'Silk').replace(/\s+/g,' ').trim();
  fin=fin.replace(/^PLA-CF$/,'CF').replace(/^[-–]$/,'').replace(/^F$/,'');
  if(kind==='resin') fin=(it.type||'').replace(/\s+/g,' ').trim();
  const type=kind==='resin'?'Resin':(it.type||'');
  let cname=color.replace(/\(.*?\)/g,'').replace(/^\d\.\d\s+/,'').trim();
  out.push({k:'s'+out.length.toString(36).padStart(2,'0'),g:kind,type,fin,name:cname,hex:hex?('#'+hex.toLowerCase()):null,hexes:hexes?hexes.map(h=>'#'+h.toLowerCase()):null,e:fx,avail,maker:(q==='verified'||q==='close')});
}
// merge duplicates (same type+finish+name)
const seen={}, final=[];
for(const s of out){ const key=[s.type,s.fin,s.name].join('|').toLowerCase(); if(seen[key]){ const a=seen[key]; if(s.avail==='in'||(s.avail==='limited'&&a.avail==='order')) a.avail=s.avail; continue; } seen[key]=s; final.push(s); }
// Hebrew labels (he.json beside this script). Missing entries fall back to English and are reported.
const HE=fs.existsSync(__dirname+'/he.json')?JSON.parse(fs.readFileSync(__dirname+'/he.json','utf8')):{names:{},fins:{},types:{}};
const miss=new Set();
for(const s of final){ const n=HE.names[s.name], f=s.fin?HE.fins[s.fin]:'', t=HE.types[s.type];
  if(n) s.name_he=n; else miss.add('name: '+s.name);
  if(s.fin){ if(f) s.fin_he=f; else miss.add('fin: '+s.fin); }
  if(t) s.type_he=t; }
console.log('hebrew missing:',[...miss]);
fs.writeFileSync('swatches.json',JSON.stringify({updated:new Date().toISOString().slice(0,10),items:final}));
console.log('items',final.length,'dropped',drop.length);
const c=(f)=>final.reduce((a,s)=>(a[s[f]]=(a[s[f]]||0)+1,a),{});
console.log(c('e'),c('avail'),c('type'),'maker',final.filter(s=>s.maker).length);
console.log(drop.filter(d=>d[2]==='excluded'));
// privacy scan
const txt=fs.readFileSync('swatches.json','utf8').toLowerCase();
const brands=[...new Set(Object.values(M).map(m=>(m.brand||'').toLowerCase()).filter(b=>b&&b!=='unknown'))];
console.log('brand leaks:',brands.filter(b=>txt.includes(b)), 'cost-ish keys:',/"(cost|price|fx|cur|ship|vat|nis|rem|net|links?|brand|source)"/.test(txt));
