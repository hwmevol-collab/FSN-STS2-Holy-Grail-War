from animation_common import *
import bisect, math, numpy as np
from PIL import Image
def normalize(s):
    out=[];latin=False
    for c in unicodedata.normalize('NFKD',unicodedata.normalize('NFKC',s)).casefold():
        if unicodedata.combining(c):
            if not latin:out.append(c)
        else:out.append(c);latin='LATIN' in unicodedata.name(c,'')
    return unicodedata.normalize('NFC',''.join(out))
def vocabulary():
    bm=L/'ReferenceBooks/Metadata';aliases=read(bm/'ALIASES.json');characters={r['tag'] for r in csv.DictReader((bm/'OFFICIAL_MATERIAL_CHARACTER_INDEX.csv').open(encoding='utf-8-sig',newline=''))};v={}
    for a in aliases:
        alias=a['alias'];entity=a['entity']
        if entity.startswith('CM_') or entity=='SIDE' or len(normalize(alias))<2:continue
        v[(entity,normalize(alias))]={'canonical_alias':entity,'matched_term':alias,'tag_type':'character_mentioned' if entity in characters else 'term_mentioned','evidence_type':'official_vocabulary_match','vocabulary_source':str(bm/'ALIASES.json'),'official_pages':a.get('source_pages',[]),'vocabulary_status':a['status']}
    additions={'Lancer':['Lancer','ランサー','枪兵','槍兵'],'Rin':['Rin','遠坂凛','遠坂凜','远坂凛'],'Saber':['Saber','セイバー','剑士','劍士'],'Gae Bolg':['Gae Bolg','Gáe Bolg','ゲイ・ボルク','ゲイボルク','穿刺死棘之枪','穿刺死棘之槍'],'Avalon':['Avalon','アヴァロン','阿瓦隆'],'Projection':['Projection','投影'],'Jewel':['Jewel','宝石','寶石'],'Command Spell':['Command Spell','Command Seal','令呪','令咒'],'UBW':['UBW','Unlimited Blade Works','無限の剣製','无限剑制','無限劍製'],'Magecraft':['Magic','魔術','魔术'],'Excalibur':['Excalibur','エクスカリバー','誓约胜利之剑','誓約勝利之劍']}
    for entity,als in additions.items():
        for alias in als:v.setdefault((entity,normalize(alias)),{'canonical_alias':entity,'matched_term':alias,'tag_type':'character_mentioned' if entity in ['Lancer','Rin','Saber'] else 'term_mentioned','evidence_type':'subtitle_alias','vocabulary_source':'user requested search topics / explicit search alias only','official_pages':[],'vocabulary_status':'search_alias_only'})
    for alias in ['Battle','战斗','戰鬥','戦闘','戦い']:
        v.setdefault(('Battle',normalize(alias)),{'canonical_alias':'Battle','matched_term':alias,'tag_type':'term_mentioned','evidence_type':'subtitle_alias','vocabulary_source':'user action/search vocabulary; textual mention only, not a confirmed action','official_pages':[],'vocabulary_status':'search_alias_only'})
    for alias in ['凛','凜']:
        v.setdefault(('Rin',normalize(alias)),{'canonical_alias':'Rin','matched_term':alias,'tag_type':'search_expansion_only','evidence_type':'subtitle_alias','vocabulary_source':'single-character search aid; ambiguous matches do not create character tags','official_pages':[],'vocabulary_status':'search_alias_only','search_only':True})
    # Locally observed spelling/translation variants are separate from the frozen official vocabulary.
    local_aliases=M/'ANIMATION_LOCAL_SEARCH_ALIASES.json'
    if local_aliases.exists():
        for a in read(local_aliases):v.setdefault((a['canonical_alias'],normalize(a['matched_term'])),a)
    # Index vocabulary links are textual references, with original OCR uncertainty.
    links=[]
    specs=[('CHARACTER',['tag','alias_matched'],'character_mentioned'),('WEAPON',['weapon_name','original_name'],'term_mentioned'),('NOBLE_PHANTASM',['name','original_name'],'term_mentioned'),('MAGIC',['name','original_name'],'term_mentioned'),('TERM',['term','original_term'],'term_mentioned')]
    for kind,keys,tagtype in specs:
        src=bm/f'OFFICIAL_MATERIAL_{kind}_INDEX.csv'
        for r in csv.DictReader(src.open(encoding='utf-8-sig',newline='')):
            canonical=r.get(keys[0],'').strip()
            if not canonical:continue
            page=r.get('page_id',r.get('page',''));status=r.get('status','unknown')
            for alias in dict.fromkeys(r.get(k,'').strip() for k in keys):
                if len(normalize(alias))<2:continue
                entities={a['canonical_alias'] for a in v.values() if normalize(a['matched_term'])==normalize(alias)}
                entity=next(iter(entities)) if len(entities)==1 else canonical
                key=(entity,normalize(alias))
                if key not in v:v[key]={'canonical_alias':entity,'matched_term':alias,'tag_type':tagtype,'evidence_type':'official_vocabulary_match','vocabulary_source':str(src),'official_pages':[],'vocabulary_status':status}
                a=v[key]
                if page and page not in a['official_pages']:a['official_pages'].append(page)
                if str(src) not in a['vocabulary_source']:a['vocabulary_source']+='; '+str(src)
                links.append({'canonical_alias':entity,'alias':alias,'official_index':kind,'page_id':page,'page_asset_id':r.get('page_asset_id',''),'vocabulary_status':status,'source_index':str(src),'link_type':'textual_vocabulary_reference_only'})
    canonical_by_norm={}
    for a in v.values():canonical_by_norm.setdefault(normalize(a['canonical_alias']),a['canonical_alias'])
    merged={}
    for a in v.values():
        a['canonical_alias']=canonical_by_norm[normalize(a['canonical_alias'])];key=(a['canonical_alias'],normalize(a['matched_term']))
        if key not in merged:merged[key]=a
        else:
            m=merged[key];m['official_pages']=list(dict.fromkeys(m['official_pages']+a['official_pages']));m['vocabulary_source']='; '.join(dict.fromkeys((m['vocabulary_source']+'; '+a['vocabulary_source']).split('; ')));m['vocabulary_statuses']=list(dict.fromkeys(m.get('vocabulary_statuses',[m['vocabulary_status']])+[a['vocabulary_status']]))
    v=merged
    for l in links:l['canonical_alias']=canonical_by_norm[normalize(l['canonical_alias'])]
    csvout(M/'ANIMATION_OFFICIAL_MATERIAL_TERM_LINKS.csv',links);jl(M/'ANIMATION_OFFICIAL_MATERIAL_TERM_LINKS.jsonl',links)
    rows=list(v.values());csvout(M/'ANIMATION_SEARCH_VOCABULARY.csv',rows);save(M/'ANIMATION_SEARCH_VOCABULARY.json',rows);save(M/'ANIMATION_ACTION_VOCABULARY.json',{'labels':['Battle','Slash','Thrust','Projectile','Magic','Explosion','Guard','Damage','Run','Jump','Transformation','NoblePhantasm','Dialogue','Expression','DailyLife','Comedy','Cooking','Landscape'],'confirmed_requires_visual_or_stronger_evidence':True});return rows
def match(alias,text):
    a=normalize(alias);t=normalize(text)
    return bool(re.search(r'(?<![a-z0-9])'+re.escape(a)+r'(?![a-z0-9])',t)) if a.isascii() and any(c.isalpha() for c in a) else a in t
def index():
    from animation_precise_times import repair
    repair()
    shots=readjl(M/'ANIMATION_SHOT_INDEX.jsonl');media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');lines=readjl(M/'ANIMATION_SUBTITLE_LINES.jsonl');chapters=readjl(M/'ANIMATION_CHAPTER_INDEX.jsonl');aliases=vocabulary();by_media=collections.defaultdict(list);line_media=collections.defaultdict(list)
    for s in shots:by_media[s['media_asset_id']].append(s)
    for l in lines:line_media[l['media_asset_id']].append(l)
    relations=[];hits=[];evidence=[];sequences=[];queue=[];browser=[];line_hits={};searchrows=[];char_tags={a['canonical_alias'] for a in aliases if a['tag_type']=='character_mentioned'}
    patterns=[]
    for a in aliases:
        if a.get('search_only'):continue
        term=normalize(a['matched_term']);pattern=re.compile(r'(?<![a-z0-9])'+re.escape(term)+r'(?![a-z0-9])') if term.isascii() and any(c.isalpha() for c in term) else None;patterns.append((a,term,pattern))
    match_cache={}
    for l in lines:
        text=normalize(l['plain_text'])
        if text not in match_cache:match_cache[text]=[a for a,term,p in patterns if (bool(p.search(text)) if p else term in text)]
        line_hits[l['line_id']]=match_cache[text]
    for r in media:
        ss=by_media[r['media_asset_id']];ll=sorted(line_media[r['media_asset_id']],key=lambda x:x['start_ms']);ends=[s['end_ms'] for s in ss];starts=[s['start_ms'] for s in ss];overlaps=collections.defaultdict(list)
        sh_hits=collections.defaultdict(list)
        for l in ll:
            a=bisect.bisect_right(ends,l['start_ms']);b=bisect.bisect_left(starts,l['end_ms'])
            for s in ss[a:b]:
                relations.append({'shot_id':s['shot_id'],'subtitle_line_id':l['line_id'],'media_asset_id':r['media_asset_id'],'overlap_ms':min(s['end_ms'],l['end_ms'])-max(s['start_ms'],l['start_ms'])});overlaps[s['shot_id']].append(l)
                seen=set()
                for v in line_hits[l['line_id']]:
                    key=(v['canonical_alias'],v['matched_term'])
                    if key in seen:continue
                    seen.add(key);hid=f'TH-{len(hits)+1:09d}';hit={'hit_id':hid,'media_asset_id':r['media_asset_id'],'shot_id':s['shot_id'],'sequence_id':'','subtitle_line_id':l['line_id'],'track_id':l['track_id'],'matched_term':v['matched_term'],'canonical_alias':v['canonical_alias'],'raw_subtitle':l['raw_text'],'plain_subtitle':l['plain_text'],'language':l['language'],'start_ms':l['start_ms'],'end_ms':l['end_ms'],'timecode':l['start_time'],'evidence_type':v['evidence_type'],'tag_type':v['tag_type'],'status':'confirmed_text_mention','source':v['vocabulary_source'],'official_pages':v['official_pages'],'vocabulary_status':v['vocabulary_status'],'notes':'Text mention only. Depicted character or action not asserted.'};hits.append(hit);sh_hits[s['shot_id']].append(hit)
                    evidence.append({'reference_id':s['shot_id'],'tag_type':v['tag_type'],'tag':v['canonical_alias'],'evidence_type':v['evidence_type'],'source':l['line_id'],'confidence':1.0,'status':'confirmed_text_mention','notes':'Literal alias match; official vocabulary provenance retains its own uncertainty.','hit_id':hid})
        seqgroups=[]
        for s in ss:
            if not seqgroups or s['chapter_id']!=seqgroups[-1][0]['chapter_id'] or s['start_ms']//180000!=seqgroups[-1][0]['start_ms']//180000:seqgroups.append([])
            seqgroups[-1].append(s)
        for g in seqgroups:
            sid=f"SEQ-{r['media_asset_id']}-V1-P{g[0]['start_pts']:012d}"
            for s in g:s['auto_sequence_id']=sid
            sequences.append({'sequence_id':sid,'media_asset_id':r['media_asset_id'],'start':g[0]['start_ms']/1000,'end':g[-1]['end_ms']/1000,'shot_count':len(g),'chapter':g[0]['chapter_id'],'subtitle_count':len(set(l['line_id'] for s in g for l in overlaps[s['shot_id']])),'motion_summary':round(float(np.mean([s['motion_score'] for s in g])),5),'grouping_method':'source chapter transition or 180-second timeline bucket; shot-aligned boundaries','confidence':1.0,'semantic_status':'automatic_structure_only'})
        high=float(np.percentile([s['motion_score'] for s in ss],90)) if ss else float('inf')
        for s in ss:
            sl=overlaps[s['shot_id']];hs=sh_hits[s['shot_id']];entities=list(dict.fromkeys(h['canonical_alias'] for h in hs));s['characters_mentioned']=[e for e in entities if e in char_tags];s['terms_mentioned']=[e for e in entities if e not in char_tags];s['subtitle_line_count']=len(sl);s['subtitle_char_count']=sum(len(l['plain_text']) for l in sl);s['subtitle_excerpt']=' / '.join(dict.fromkeys(l['plain_text'] for l in sl))[:220]
            reasons=[]
            if entities:reasons.append('subtitle_term_mention')
            if s['motion_score']>=max(high,1.0):reasons.append('high_visual_motion_candidate')
            if not any(l['plain_text'] for l in sl) and s['motion_score']>=max(high,1.0):reasons.append('high_motion_without_text_subtitles')
            if any(normalize(e) in {'gae bolg','excalibur','avalon','ubw','noble phantasm'} for e in entities):reasons.append('named_technique_text_mention')
            if s['characters_mentioned'] and s['terms_mentioned']:reasons.append('character_and_term_text_proximity')
            if reasons:queue.append({'reference_id':s['shot_id'],'media_asset_id':r['media_asset_id'],'work_id':r['work_id'],'start_time':s['start_time'],'priority':len(reasons),'reasons':reasons,'characters_mentioned':s['characters_mentioned'],'terms_mentioned':s['terms_mentioned'],'motion_score':s['motion_score'],'status':'review_candidate','confirmed_action':''})
            keys=['shot_id','media_asset_id','work_id','start_time','end_time','duration','representative_frame','representative_pts','pts_time_base','motion_score','subtitle_line_count','subtitle_char_count','subtitle_excerpt','chapter_id','semantic_status','characters_mentioned','characters_present_confirmed','actions_confirmed','thumbnail']
            b={k:s[k] for k in keys};b.update(languages=list(dict.fromkeys(r['subtitle_languages']+[l['language'] for l in sl])),subtitles=[l['line_id'] for l in sl],term_hits=entities,review_reasons=reasons)
            b['thumbnail']='./'+pathlib.Path(s['thumbnail']).relative_to(A).as_posix();b['search']=normalize(' '.join([s['shot_id'],s['start_time'],s['end_time'],r['media_asset_id'],r['work_id'],r['episode_label'],r['filename'],' '.join(entities),' '.join(l['plain_text'] for l in sl)]));searchrows.append((s['shot_id'],b['search']));browser.append(b)
        log('Index',r['media_asset_id'],len(ss),'shots')
    seqmap={s['shot_id']:s['auto_sequence_id'] for s in shots}
    for h in hits:h['sequence_id']=seqmap[h['shot_id']]
    for name,rows in [('ANIMATION_SHOT_INDEX',shots),('ANIMATION_SEQUENCE_INDEX',sequences),('ANIMATION_SHOT_SUBTITLE_RELATIONS',relations),('ANIMATION_TERM_HITS',hits),('ANIMATION_TAG_EVIDENCE',evidence),('ANIMATION_REVIEW_QUEUE',queue)]:
        jl(M/(name+'.jsonl'),rows);csvout(M/(name+'.csv'),rows,['reference_id','media_asset_id'] if not rows else None)
    payload={'works':read(M/'ANIMATION_WORK_INDEX.json'),'media':media,'chapters':chapters,'subtitles':{l['line_id']:{k:l[k] for k in ['line_id','track_id','start_time','end_time','language','plain_text','raw_text','speaker_field','style']} for l in lines},'shots':browser,'aliases':aliases,'sheets':read(M/'ANIMATION_CONTACT_SHEETS.json'),'summary':{'works':len(set(r['work_id'] for r in media)),'media':len(media),'coverage':sum(bool(by_media[r['media_asset_id']]) for r in media),'duration_hours':sum(r['duration'] for r in media)/3600,'shots':len(shots),'subtitle_lines':len(lines),'term_hits':len(hits)}}
    (A/'Browser').mkdir(exist_ok=True);(A/'Browser/data.js').write_text('window.ANIMATION_DATA='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8');save(M/'ANIMATION_SEARCH_INDEX_INFO.json',{'fts':'FTS5 trigram; NFKC plus Latin-diacritic-folded NFC text; Japanese dakuten preserved; LIKE fallback for 1 or 2 characters','browser':'offline static JS substring search, NFKC+Latin diacritic folding+NFC+alias expansion; all overlapping subtitle text included','word_boundary':'Latin vocabulary aliases require alphabetic/numeric boundaries','confirmed_semantics':'empty unless manually visually reviewed'})
    database(searchrows)
def database(searchrows):
    path=M/'ANIMATION_REFERENCE.sqlite';temp=path.with_name(path.name+'.tmp')
    if temp.exists():temp.unlink()
    db=sqlite3.connect(temp)
    files={'works':'ANIMATION_WORK_INDEX.json','media':'ANIMATION_MEDIA_INDEX.jsonl','tracks':'ANIMATION_TRACK_INDEX.jsonl','subtitles':'ANIMATION_SUBTITLE_LINES.jsonl','chapters':'ANIMATION_CHAPTER_INDEX.jsonl','shots':'ANIMATION_SHOT_INDEX.jsonl','sequences':'ANIMATION_SEQUENCE_INDEX.jsonl','tags':'ANIMATION_TAG_EVIDENCE.jsonl','terms':'ANIMATION_TERM_HITS.jsonl','relations':'ANIMATION_SHOT_SUBTITLE_RELATIONS.jsonl','review_queue':'ANIMATION_REVIEW_QUEUE.jsonl'}
    for table,file in files.items():
        rows=read(M/file) if file.endswith('.json') else readjl(M/file);fields=list(dict.fromkeys(k for r in rows for k in r)) or ['reference_id'];sample={k:next((r[k] for r in rows if r.get(k) is not None),None) for k in fields};types={k:'INTEGER' if isinstance(v,int) else 'REAL' if isinstance(v,float) else 'TEXT' for k,v in sample.items()};db.execute('CREATE TABLE '+table+' ('+','.join('"'+k+'" '+types[k] for k in fields)+')');db.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for k in fields)+')',[[json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in fields] for r in rows])
        for k in ['media_asset_id','shot_id','line_id','subtitle_line_id','work_id','track_id','sequence_id']:
            if k in fields:db.execute('CREATE INDEX '+table+'_'+k+' ON '+table+'("'+k+'")')
        log('SQLite',table,len(rows))
    db.execute("CREATE VIRTUAL TABLE subtitle_fts USING fts5(line_id UNINDEXED,media_asset_id UNINDEXED,text,tokenize='trigram')");db.executemany('INSERT INTO subtitle_fts VALUES (?,?,?)',[(l['line_id'],l['media_asset_id'],normalize(l['plain_text'])) for l in readjl(M/'ANIMATION_SUBTITLE_LINES.jsonl')]);db.execute("CREATE VIRTUAL TABLE metadata_fts USING fts5(shot_id UNINDEXED,text,tokenize='trigram')");db.executemany('INSERT INTO metadata_fts VALUES (?,?)',searchrows);db.commit();integrity=db.execute('PRAGMA integrity_check').fetchone()[0];assert integrity=='ok';db.close();os.replace(temp,path);save(M/'SQLITE_VALIDATION.json',{'integrity':integrity,'created_at':now(),'sha256':sha(path)})
def phash(p):
    a=np.asarray(Image.open(p).convert('L').resize((32,32)),dtype=float);cos=np.cos(np.pi*(np.arange(32)+.5)[None,:]*np.arange(8)[:,None]/32);d=cos@a@cos.T;bits=(d>np.median(d.flatten()[1:])).flatten();return sum(int(b)<<i for i,b in enumerate(bits)),float(np.std(a))
def duplicates():
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');rows=[];exact=collections.defaultdict(list);samples={}
    for r in media:
        exact[r['sha256']].append(r);ps=sorted((T/'overview-frames'/r['media_asset_id']).glob('*.jpg'));samples[r['media_asset_id']]=[phash(p) for p in ps]
    for h,rs in exact.items():
        if len(rs)>1:
            for r in rs[1:]:rows.append({'group_id':'EX-'+h[:16],'media_a':rs[0]['media_asset_id'],'media_b':r['media_asset_id'],'match_type':'exact_duplicate','sha256':h,'duration_delta':abs(r['duration']-rs[0]['duration']),'phash_distance':'','samples_matching':'','status':'confirmed_exact_payload','reference_primary_candidate':'','evidence':'streaming SHA256 equality'})
    for i,r in enumerate(media):
        for q in media[:i]:
            if r['sha256']==q['sha256'] or r['work_id']!=q['work_id'] or abs(r['duration']-q['duration'])>max(2.5,r['duration']*.005):continue
            pairs=[((a^b).bit_count(),sa,sb) for (a,sa),(b,sb) in zip(samples[r['media_asset_id']],samples[q['media_asset_id']]) if min(sa,sb)>12];matches=sum(d<=12 for d,_,_ in pairs);distance=round(float(np.mean([d for d,_,_ in pairs])),3) if pairs else 64
            if len(pairs)>=8 and matches>=8 and distance<14:
                gid='CP-'+hashlib.sha256((q['media_asset_id']+r['media_asset_id']).encode()).hexdigest()[:16];primary=max([r,q],key=lambda x:(x['width']*x['height'],x['size']))['media_asset_id'] if matches>=10 and distance<7 else '';rows.append({'group_id':gid,'media_a':q['media_asset_id'],'media_b':r['media_asset_id'],'match_type':'same_program_candidate','sha256':'','duration_delta':abs(r['duration']-q['duration']),'phash_distance':distance,'samples_matching':matches,'status':'visual_candidate','reference_primary_candidate':primary,'evidence':'12 uniform source-time samples, 64-bit pHash and luma variance; candidate only, no deletion'})
    csvout(M/'ANIMATION_DUPLICATES.csv',rows,['group_id','media_a','media_b','match_type','sha256','duration_delta','phash_distance','samples_matching','status','reference_primary_candidate','evidence']);save(M/'ANIMATION_DUPLICATES.json',rows);log('Duplicate candidates',len(rows))
if __name__=='__main__':{'Index':index,'Terms':index,'Duplicates':duplicates}[sys.argv[1] if len(sys.argv)>1 else 'Index']()
