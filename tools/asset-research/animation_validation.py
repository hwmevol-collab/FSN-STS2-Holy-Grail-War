from animation_common import *
from animation_tracks import parse_subtitle,plain
from animation_shots import eval_fraction
import random,bisect,numpy as np

def validate():
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');lines=readjl(M/'ANIMATION_SUBTITLE_LINES.jsonl');tracks=readjl(M/'ANIMATION_SUBTITLE_TRACK_INDEX.jsonl');shots=readjl(M/'ANIMATION_SHOT_INDEX.jsonl');anomalies=readjl(M/'ANIMATION_ANOMALIES.jsonl');anomalies=[a for a in anomalies if a['type'] not in {'decoder_error','duration_mismatch','no_video_stream','very_short_file','possible_duplicate'}];pts=[]
    inventory=read(M/'ANIMATION_SOURCE_INVENTORY.json')
    for r in inventory:
        if r['kind']=='no_video_stream':anomalies.append({'media_asset_id':'','type':'no_video_stream','reference_id':r['relative_source_path'],'detail':'Audio-only companion: retained as supporting source; not a missing video','status':'expected_supporting_source'})
    for r in media:
        cache=T/'shots/v1'/r['media_asset_id'];p=cache/'metrics.npz'
        if not p.exists():continue
        a=np.load(p)['frames'];tb=eval_fraction(r['video_time_base']);dt=np.diff(a[:,0])*tb
        try:expected=eval_fraction(r['fps'],invert=True)
        except (ZeroDivisionError,ValueError):expected=float(np.median(dt)) if len(dt) else r['duration']
        outliers=int(np.sum(np.abs(dt-expected)>max(2.1*tb,.05*expected)));mode='single_decoded_frame_no_rate_inference' if len(dt)==0 else 'source_pts_vfr' if outliers>max(2,len(dt)*.005) else 'source_pts_consistent_with_nominal_cfr';r['frame_rate_mode']=mode
        end=float(a[-1,0])*tb-r['container_start_time']+(float(np.median(dt)) if len(dt) else expected);delta=r['duration']-end;pts.append({'media_asset_id':r['media_asset_id'],'frames':len(a),'first_source_pts':int(a[0,0]),'last_source_pts':int(a[-1,0]),'last_frame_end_estimate':end,'container_duration':r['duration'],'duration_delta_seconds':delta,'nominal_frame_interval':expected,'outlier_intervals':outliers,'frame_rate_mode':mode})
        probe=read(r['probe_path']);video=next(s for s in probe['streams'] if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic'));declared=video.get('nb_frames','')
        if str(declared).isdigit() and int(declared)>0:
            pts[-1].update(container_declared_video_frames=int(declared),declared_frame_count_matches=int(declared)==len(a))
            if int(declared)!=len(a):anomalies.append({'media_asset_id':r['media_asset_id'],'type':'declared_frame_count_mismatch','reference_id':r['media_asset_id'],'detail':f'Container nb_frames={declared}; complete detector records={len(a)}','status':'review_required'})
        if abs(delta)>2:anomalies.append({'media_asset_id':r['media_asset_id'],'type':'duration_mismatch','reference_id':r['media_asset_id'],'detail':f'Container minus last decoded video frame end = {delta:.6f}s; container may include other stream durations','status':'review_required'})
        if r['duration']<.25:anomalies.append({'media_asset_id':r['media_asset_id'],'type':'very_short_file','reference_id':r['media_asset_id'],'detail':str(r['duration']),'status':'expected_static_menu' if len(a)==1 and 'menu' in r['special_label'].lower() else 'review_required'})
        for stage in ['detect','thumbnails']:
            lp=T/'logs'/(r['media_asset_id']+'-'+stage+'.log')
            if not lp.exists():continue
            errors=[x for x in lp.read_text(encoding='utf-8',errors='replace').splitlines() if re.search(r'error while decoding|invalid data found|corrupt decoded|invalid nal|missing reference|failed to decode',x,re.I)]
            if errors:anomalies.append({'media_asset_id':r['media_asset_id'],'type':'decoder_error','reference_id':str(lp),'detail':'\n'.join(errors[:20]),'status':'review_required'})
    jl(M/'ANIMATION_MEDIA_INDEX.jsonl',media);csvout(M/'ANIMATION_MEDIA_INDEX.csv',media);csvout(M/'ANIMATION_PTS_VALIDATION.csv',pts);save(M/'ANIMATION_PTS_VALIDATION.json',pts)
    bypath={r['source_path']:r for r in media}
    for r in inventory:
        if r['source_path'] in bypath:r['frame_rate_mode']=bypath[r['source_path']]['frame_rate_mode']
    save(M/'ANIMATION_SOURCE_INVENTORY.json',inventory);csvout(M/'ANIMATION_SOURCE_INVENTORY.csv',inventory)
    if (M/'ANIMATION_DUPLICATES.json').exists():
        for d in read(M/'ANIMATION_DUPLICATES.json'):anomalies.append({'media_asset_id':d['media_a'],'type':'possible_duplicate','reference_id':d['group_id'],'detail':json.dumps(d,ensure_ascii=False),'status':d['status']})
    csvout(M/'ANIMATION_ANOMALIES.csv',anomalies,['media_asset_id','type','reference_id','detail','status']);jl(M/'ANIMATION_ANOMALIES.jsonl',anomalies)
    # Actual local formats only. Preserve a sample of embedded, external and bilingual ASS.
    format_samples=[];line_map={l['line_id']:l for l in lines};groups=collections.defaultdict(list)
    for t in tracks:groups[(t['source_type'],t['codec'],t['language'])].append(t)
    for key,ts in groups.items():
        t=ts[len(ts)//2]
        if t['status']=='image_subtitle_metadata_only':format_samples.append({'group':key,'track_id':t['track_id'],'status':'metadata_only_allowed','line_count':0});continue
        raw=pathlib.Path(t['working_copy']);parsed=parse_subtitle(raw,t);chosen=parsed[::max(1,len(parsed)//5)][:6];checks=[]
        for x in chosen:
            old=line_map[x['line_id']];checks.append(all(old[k]==x[k] for k in ['raw_text','plain_text','event_raw','language','start_ms','end_ms','style','speaker_field','layer','margin_l','margin_r','margin_v','effect']))
        format_samples.append({'group':key,'track_id':t['track_id'],'raw_sha256':sha(raw),'recorded_sha256':t['working_sha256'],'source_copy_hash_equal':sha(raw)==t.get('source_sha256',t['working_sha256']),'samples':[x['line_id'] for x in chosen],'fields_match':all(checks),'status':'PASS' if all(checks) and sha(raw)==t['working_sha256'] else 'FAIL'})
    drawing=[l for l in lines if re.search(r'\\p[1-9]',l['raw_text'])];assert all(plain(l['raw_text'])==l['plain_text'] for l in drawing)
    groupshots=collections.defaultdict(list)
    for s in shots:groupshots[s['media_asset_id']].append(s)
    rng=random.Random(20261007);chosen=rng.sample(lines,min(1000,len(lines)));db=sqlite3.connect('file:'+str(M/'ANIMATION_REFERENCE.sqlite')+'?mode=ro',uri=True);overlap_errors=[]
    for l in chosen:
        expected={s['shot_id'] for s in groupshots[l['media_asset_id']] if s['start_ms']<l['end_ms'] and s['end_ms']>l['start_ms']};actual={x[0] for x in db.execute('SELECT shot_id FROM relations WHERE subtitle_line_id=?',(l['line_id'],))}
        if expected!=actual:overlap_errors.append(l['line_id'])
    search=[]
    from animation_index import normalize
    for q in ['Lancer','Gae Bolg','Saber','Rin','投影','魔術','宝具','你好','令呪']:
        n=normalize(q);count=db.execute('SELECT COUNT(*) FROM subtitle_fts WHERE text LIKE ?',('%'+n+'%',)).fetchone()[0];fts=db.execute('SELECT COUNT(*) FROM subtitle_fts WHERE subtitle_fts MATCH ?',('"'+n+'"',)).fetchone()[0] if len(n)>=3 else None;search.append({'query':q,'normalized':n,'substring_rows':count,'fts_rows':fts,'short_query_fallback':len(n)<3,'status':'PASS' if fts is None or count==fts else 'review_required'})
    db.close()
    db=sqlite3.connect(M/'ANIMATION_REFERENCE.sqlite');db.executemany('UPDATE media SET frame_rate_mode=? WHERE media_asset_id=?',[(r['frame_rate_mode'],r['media_asset_id']) for r in media]);db.commit();integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.close();assert integrity=='ok';save(M/'SQLITE_VALIDATION.json',{'integrity':integrity,'validated_at':now(),'sha256':sha(M/'ANIMATION_REFERENCE.sqlite')})
    data_path=A/'Browser/data.js';data=json.loads(data_path.read_text(encoding='utf-8')[len('window.ANIMATION_DATA='):-1]);data['media']=media;tmp=data_path.with_suffix('.js.tmp');tmp.write_text('window.ANIMATION_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8');os.replace(tmp,data_path)
    required={'WORK_INDEX':['work_id','canonical_local_title','source_title','work_type','source_root','media_count','status','evidence'],'MEDIA_INDEX':['media_asset_id','work_id','media_id','source_path','sha256','duration','resolution','codec','identity_status','technical_status'],'TRACK_INDEX':['track_id','media_asset_id','codec','source_path'],'SUBTITLE_TRACK_INDEX':['track_id','media_asset_id','language','codec','title','default','forced','source_type','source_path','line_count','status'],'SUBTITLE_LINES':['line_id','track_id','media_asset_id','start_ms','end_ms','raw_text','plain_text','language','style','speaker_field'],'CHAPTER_INDEX':['chapter_id','media_asset_id','start','end'],'SHOT_INDEX':['shot_id','media_asset_id','start_pts','end_pts','start_ms','end_ms','representative_pts','thumbnail','motion_score','auto_sequence_id','semantic_status'],'SEQUENCE_INDEX':['sequence_id','media_asset_id','start','end','shot_count','grouping_method','semantic_status'],'SHOT_SUBTITLE_RELATIONS':['shot_id','subtitle_line_id','overlap_ms'],'TERM_HITS':['shot_id','subtitle_line_id','matched_term','canonical_alias','raw_subtitle','language','evidence_type'],'TAG_EVIDENCE':['reference_id','tag_type','tag','evidence_type','source','confidence','status','notes'],'DUPLICATES':['group_id','media_a','media_b','match_type','status'],'REVIEW_QUEUE':['reference_id','media_asset_id','status'],'ANOMALIES':['media_asset_id','type','reference_id','detail','status'],'CONTACT_SHEETS':['media_asset_id','type','page','shot_count','path']};schema=[]
    for name,fields in required.items():
        p=M/('ANIMATION_'+name+'.csv')
        with p.open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
        missing=sorted(set(fields)-set(header));schema.append({'file':p.name,'missing_columns':missing,'status':'PASS' if not missing else 'FAIL'})
    save(M/'ANIMATION_INDEX_SCHEMA_VALIDATION.json',{'created_at':now(),'status':'PASS' if all(r['status']=='PASS' for r in schema) else 'FAIL','required_csv_files':len(schema),'items':schema})
    result={'created_at':now(),'subtitle_format_samples':format_samples,'formats_present':sorted(set(t['codec'] for t in tracks)),'drawing_rows_checked':len(drawing),'overlap_samples':len(chosen),'overlap_errors':overlap_errors,'search':search,'pts_media_validated':len(pts),'index_schema':schema,'unresolved_anomalies':[a for a in anomalies if a['status']=='review_required']};result['status']='PASS' if not overlap_errors and all(x['status']!='FAIL' for x in format_samples) and all(x['status']=='PASS' for x in search) and all(x['status']=='PASS' for x in schema) and not result['unresolved_anomalies'] and len(pts)==len(media) else 'review_required';save(M/'ANIMATION_DATA_VALIDATION.json',result);log('Data validation',result['status'],len(pts),'PTS files',len(anomalies),'anomalies')

if __name__=='__main__':validate()
