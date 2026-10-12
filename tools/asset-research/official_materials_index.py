from official_materials import *
def index():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');ocr={o['page_id']:o for o in readjl(M/'OCR_INDEX.jsonl')};path=M/'OFFICIAL_MATERIAL_PAGE_INDEX.sqlite';temp=T/'page_index.sqlite'
    if temp.exists():temp.unlink()
    db=sqlite3.connect(temp);fields=list(dict.fromkeys(k for p in pages for k in p));db.execute('CREATE TABLE pages ('+','.join('"'+k+'" '+('INTEGER' if k in ['scan_page','scan_page_index','width','height','printed_page','printed_page_number','size'] else 'TEXT')+(' PRIMARY KEY' if k=='page_id' else '') for k in fields)+')')
    def value(v):return json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else int(v) if isinstance(v,bool) else v
    db.executemany('INSERT INTO pages VALUES ('+','.join('?' for k in fields)+')',[tuple(value(p.get(k)) for k in fields) for p in pages]);db.execute('CREATE UNIQUE INDEX page_asset_id_idx ON pages(page_asset_id)');db.execute('CREATE INDEX book_scan_idx ON pages(book_id,scan_variant,scan_page)');db.execute('CREATE INDEX printed_page_idx ON pages(book_id,printed_page)')
    db.execute('CREATE TABLE ocr(page_id TEXT PRIMARY KEY,raw_text_path TEXT,normalized_text_path TEXT,status TEXT,confidence REAL,text TEXT)')
    vertical={v['page_id']:v for v in readjson(M/'VERTICAL_OCR_RESULTS.json')}
    for p in pages:
        o=ocr[p['page_id']];text=pathlib.Path(o['normalized_text_path']).read_text(encoding='utf-8');v=vertical.get(p['page_id'])
        if v:text+='\n\n[Supplemental vertical OCR, original retained separately]\n'+pathlib.Path(v['normalized_text_path']).read_text(encoding='utf-8')
        db.execute('INSERT INTO ocr VALUES (?,?,?,?,?,?)',(p['page_id'],o['raw_text_path'],o['normalized_text_path'],o['status'],o['confidence'],text))
    db.execute("CREATE VIRTUAL TABLE search_fts USING fts5(page_id UNINDEXED,asset_id,book_title,section,characters,keywords,text,tokenize='trigram')")
    db.execute('INSERT INTO search_fts SELECT pages.page_id,page_asset_id,book_title,section,characters_confirmed||characters_candidate,keywords,ocr.text FROM pages JOIN ocr USING(page_id)');db.execute('CREATE TABLE aliases(entity TEXT,alias TEXT,source TEXT,status TEXT)');db.executemany('INSERT INTO aliases VALUES(?,?,?,?)',[(a['entity'],a['alias'],a['source'],a['status']) for a in readjson(M/'ALIASES.json')]);db.commit();assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert db.execute('SELECT COUNT(*) FROM pages').fetchone()[0]==len(pages);db.close();os.replace(temp,path)
    q=M/'OFFICIAL_MATERIAL.sqlite'
    if q.exists():q.unlink()
    os.link(path,q);writejson(M/'SEARCH_INDEX_INFO.json',{'sqlite':str(path),'fts':'FTS5 trigram; 3+ character substring tokens','short_query':'For one/two-character queries, SQL LIKE against ocr.text, or browser substring search','browser_search':'NFKC substring plus entity aliases, supports all string lengths','fts_alias_expansion':'join aliases; raw original terms retained','integrity':'ok'});log('REFERENCE SQLITE',len(pages))
def similarity():
    pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');sim=[];game=[]
    eligible=[p for p in pages if p.get('std_luminance',0)>10 and p.get('width',0)>500 and p.get('height',0)>500];buckets=collections.defaultdict(list)
    for p in eligible:
        h=int(p['phash'],16)
        candidates=set(i for shift in [0,16,32,48] for i in buckets[(shift,(h>>shift)&65535)])
        for i in candidates:
            q=eligible[i]
            if q['page_id']==p['page_id']:continue
            distance=(h^int(q['phash'],16)).bit_count();dd=(int(p['dhash'],16)^int(q['dhash'],16)).bit_count();ratio=abs(p['width']/p['height']-q['width']/q['height'])
            if p['sha256']==q['sha256'] or distance<=4 and dd<=6 and ratio<.05:
                sim.append({'page_a':q['page_id'],'page_b':p['page_id'],'book_a':q['book_id'],'book_b':p['book_id'],'match_type':'exact_payload' if p['sha256']==q['sha256'] else 'whole_page_visual_similarity','phash_distance':distance,'dhash_distance':dd,'visual_similarity':1-distance/64,'status':'confirmed_exact_payload' if p['sha256']==q['sha256'] else 'visual_candidate','evidence':'whole-page SHA256 + pHash/dHash/dimensions; similarity is not asset identity'})
        i=eligible.index(p)
        for shift in [0,16,32,48]:buckets[(shift,(h>>shift)&65535)].append(i)
    csvout(M/'OFFICIAL_MATERIAL_VISUAL_SIMILARITY.csv',sim,['page_a','page_b','book_a','book_b','match_type','phash_distance','dhash_distance','visual_similarity','status','evidence'])
    db=sqlite3.connect('file:'+str(B/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);games=[dict(zip(['asset_id','sha256','phash','dhash','width','height'],r)) for r in db.execute("SELECT asset_id,sha256,phash,dhash,width,height FROM assets WHERE source_version IN ('Original','Remastered','HollowAtaraxia') AND width>500 AND height>500 AND length(phash)=16 AND length(dhash)=16")];db.close();gb=collections.defaultdict(set);hashidx=collections.defaultdict(list)
    for i,g in enumerate(games):
        hashidx[g['sha256']].append(i)
        for shift in [0,16,32,48]:gb[(shift,(int(g['phash'],16)>>shift)&65535)].add(i)
    for p in eligible:
        h=int(p['phash'],16);candidates=set(hashidx.get(p['sha256'],[]))
        for shift in [0,16,32,48]:candidates.update(gb[(shift,(h>>shift)&65535)])
        for i in candidates:
            g=games[i];dist=(h^int(g['phash'],16)).bit_count();dd=(int(p['dhash'],16)^int(g['dhash'],16)).bit_count();ratio=abs(p['width']/p['height']-float(g['width'])/float(g['height']))
            if p['sha256']==g['sha256'] or dist<=3 and dd<=4 and ratio<.03:
                game.append({'page_asset_id':p['page_asset_id'],'game_asset_id':g['asset_id'],'match_type':'exact_payload' if p['sha256']==g['sha256'] else 'whole_page_hash_candidate','visual_similarity':1-dist/64,'phash_distance':dist,'dhash_distance':dd,'status':'confirmed' if p['sha256']==g['sha256'] else 'visual_candidate'})
    csvout(M/'OFFICIAL_MATERIAL_GAME_ASSET_LINKS.csv',game,['page_asset_id','game_asset_id','match_type','visual_similarity','phash_distance','dhash_distance','status']);writejson(M/'SIMILARITY_SUMMARY.json',{'book_candidates':len(sim),'cross_book_candidates':sum(s['book_a']!=s['book_b'] for s in sim),'game_candidates':len(game),'game_images_screened':len(games),'method':'Four 16-bit pHash chunk buckets; conservative pHash/dHash/aspect thresholds; full pages only, no illustration crops','scope_limit':'Printed CG embedded within page layouts will usually not match; no claim of comprehensive crop-level linking','similarity_definition':'1 - native 64-bit pHash Hamming distance / 64; not confidence','deletion':False});log('SIMILARITY',len(sim),len(game))
def integrate():
    marker=M/'INTEGRATION_COMMIT.json'
    if marker.exists():log('Already committed; identities remain stable');return
    baseline=readjson(B/'BASELINE.json');pages=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');stage=T/'integration-stage';stage.mkdir(exist_ok=True)
    for ext in ['csv','jsonl','sqlite']:assert sha(L/('Metadata/ASSET_CATALOG.'+ext))==baseline['catalogs'][ext]['sha256'],'Existing catalog changed during work; refusing commit'
    with (B/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
    new=[]
    for i,p in enumerate(pages):
        assert p['page_asset_id']==f'FSN{268505+i:06d}'
        row={k:'' for k in fields};row.update(asset_id=p['page_asset_id'],source_version=BOOKS[p['book_id']][0],source_container=pathlib.Path(p['source_file']).name,source_logical_path=p['page_id']+'/'+p['source_member'],extracted_path=p['preservation_path'],converted_path=p['page_path'],filename=pathlib.Path(p['page_path']).name,extension=pathlib.Path(p['page_path']).suffix,detected_format=p.get('format',''),category='ReferencePage',route='Unknown',locale='Japanese',character='unknown',width=p.get('width',''),height=p.get('height',''),alpha=p.get('alpha',False),size=p['size'],sha256=p['sha256'],conversion_status='native_scan_working_reference',notes='OfficialMaterial; reference_only=true; book_id='+p['book_id']+'; scan_page='+str(p['scan_page'])+'; rich evidence in sidecar',thumbnail_path=p['thumbnail'],phash=p.get('phash',''),dhash=p.get('dhash',''),working_sha256=p['sha256'],canonical_path=p['preservation_path'],metadata_path=str(M/'Pages'/(p['page_id']+'.json')));new.append(row)
    for ext in ['csv','jsonl']:shutil.copy2(B/('Metadata/ASSET_CATALOG.'+ext),stage/('ASSET_CATALOG.'+ext))
    with (stage/'ASSET_CATALOG.csv').open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields,extrasaction='ignore').writerows(new)
    with (stage/'ASSET_CATALOG.jsonl').open('a',encoding='utf-8') as f:
        for row in new:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    path=stage/'ASSET_CATALOG.sqlite';shutil.copy2(B/'Metadata/ASSET_CATALOG.sqlite',path);db=sqlite3.connect(path);db.executemany('INSERT INTO assets ('+','.join('"'+k+'"' for k in fields)+') VALUES ('+','.join('?' for k in fields)+')',[tuple(int(r[k]) if isinstance(r[k],bool) else r[k] for k in fields) for r in new]);db.commit();db.execute('ATTACH DATABASE ? AS pre',(str(B/'Metadata/ASSET_CATALOG.sqlite'),));missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0];changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in fields)).fetchone()[0];count=db.execute('SELECT COUNT(*) FROM main.assets').fetchone()[0];integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close();assert missing==changed==0 and count==268504+len(new) and integrity=='ok'
    for ext in ['csv','jsonl']:
        with (B/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as old,(stage/('ASSET_CATALOG.'+ext)).open('rb') as cur:
            while chunk:=old.read(4*1024*1024):assert chunk==cur.read(len(chunk)),ext+' old bytes changed'
    journal={'created_at':now(),'status':'STAGED_VALIDATED','before':268504,'added':len(new),'after':count,'first_new_id':new[0]['asset_id'],'max_asset_id':new[-1]['asset_id'],'missing_old_ids':missing,'changed_old_rows':changed,'old_csv_jsonl_bytes_preserved':True,'schema_changed':False,'rich_metadata':'ReferenceBooks/Metadata sidecars','sqlite_integrity':integrity};writejson(M/'INTEGRATION_JOURNAL.json',journal)
    for ext in ['csv','jsonl','sqlite']:os.replace(stage/('ASSET_CATALOG.'+ext),L/('Metadata/ASSET_CATALOG.'+ext))
    writejl(M/'CATALOG_ADDED_ROWS.jsonl',new);journal.update(status='COMMITTED',completed_at=now());writejson(marker,journal);log('INTEGRATION',journal)
if __name__=='__main__':
    {'Index':index,'Similarity':similarity,'Integrate':integrate}[sys.argv[1] if len(sys.argv)>1 else 'Index']()
