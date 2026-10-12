"""Publish a reviewed FHA-only semantic correction, retaining all pre-FHA rows."""
from fha_integrate import *
def run():
    stage=FW/'tag_revision';stage.mkdir(exist_ok=True)
    rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')]
    fields=list(json.loads(next((BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8'))))+EXTRA
    shutil.copy2(BACK/'Metadata/ASSET_CATALOG.jsonl',stage/'ASSET_CATALOG.jsonl')
    with (stage/'ASSET_CATALOG.jsonl').open('a',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps({k:r.get(k,'') for k in fields},ensure_ascii=False)+'\n')
    with (BACK/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as src,(stage/'ASSET_CATALOG.csv').open('w',encoding='utf-8-sig',newline='') as dst:
        wr=csv.DictWriter(dst,fieldnames=fields,extrasaction='ignore');wr.writeheader()
        for r in csv.DictReader(src):wr.writerow(r)
        for r in rows:wr.writerow(r)
    shutil.copy2(L/'Metadata/ASSET_CATALOG.sqlite',stage/'ASSET_CATALOG.sqlite');db=sqlite3.connect(stage/'ASSET_CATALOG.sqlite')
    db.execute('CREATE INDEX IF NOT EXISTS fha_revision_lookup ON assets(asset_id)')
    db.executemany('UPDATE assets SET '+','.join('"'+k+'"=?' for k in fields)+' WHERE asset_id=? AND source_version=\'HollowAtaraxia\'', [tuple(int(r.get(k,'')) if isinstance(r.get(k,''),bool) else r.get(k,'') for k in fields)+(r['asset_id'],) for r in rows]);db.commit()
    db.execute('DROP INDEX fha_revision_lookup');db.commit()
    db.execute('ATTACH DATABASE ? AS pre',(str(BACK/'Metadata/ASSET_CATALOG.sqlite'),))
    assert db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in fields if k not in EXTRA)).fetchone()[0]==0;db.close()
    outputs=['ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite']
    for dest,source in {'SCRIPT_INDEX.csv':'SCRIPT_INDEX.csv','VOICE_INDEX.csv':'VOICE_INDEX.csv','VOICE_DIALOGUE_MAPPING.csv':'VOICE_DIALOGUE_RELATIONS.csv'}.items():
        append_csv(stage/dest,BACK/'Metadata'/dest,readcsv(FHA/'Metadata'/source));outputs.append(dest)
    shutil.copy2(stage/'VOICE_DIALOGUE_MAPPING.csv',stage/'VOICE_DIALOGUE_RELATIONS.csv');outputs.append('VOICE_DIALOGUE_RELATIONS.csv')
    # Preserve every pre-FHA Gallery array and every enumeration position.
    lines=(L/'Gallery/catalog.js').read_text('utf-8').splitlines();meta=json.loads(lines[0].removeprefix('window.FSN_META=').removesuffix(';'));byid={r['asset_id']:r for r in rows};changed=0
    for i,s in enumerate(lines):
        if not s.startswith('["FSN'):continue
        trailing=',' if s.endswith(',') else '';a=json.loads(s.rstrip(','))
        if a[0] in byid:
            idx=meta['characters'].index(byid[a[0]]['character'])
            if a[15]!=idx:a[15]=idx;lines[i]=json.dumps(a,ensure_ascii=False,separators=(',',':'))+trailing;changed+=1
    oldarrays=[s.rstrip(',') for s in (BACK/'Gallery/catalog.js').read_text('utf-8').splitlines() if s.startswith('["FSN')]
    assert [s.rstrip(',') for s in lines if s.startswith('["FSN')][:len(oldarrays)]==oldarrays
    (stage/'catalog.js').write_text('\n'.join(lines),encoding='utf-8')
    page=(L/'Gallery/index.html').read_text('utf-8').replace("items.forEach((s,i)=>select.add(new Option(s,i)));","items.forEach((s,i)=>{if(id!=='character'||!['**','？？？','???'].includes(s))select.add(new Option(s,i));});")
    (stage/'index.html').write_text(page,encoding='utf-8')
    for name in outputs:os.replace(stage/name,L/'Metadata'/name)
    for name in ['catalog.js','index.html']:os.replace(stage/name,L/'Gallery'/name)
    jsonwrite(FHA/'Metadata/TAG_REVISION.json',dict(completed_at=now(),reason='Ambiguous speaker placeholders become unknown/blank, never identities',new_gallery_arrays_changed=changed,old_gallery_arrays_changed=0))
    print('FHA TAG CORRECTION',changed,flush=True)
if __name__=='__main__':run()
