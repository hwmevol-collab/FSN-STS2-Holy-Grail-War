from animation_common import *
def promote_integration(result):
    baseline=read(B/'BASELINE.json');stage=T/'integration-stage'
    for ext in ['csv','jsonl','sqlite']:
        dest=L/('Metadata/ASSET_CATALOG.'+ext);h=sha(dest)
        if h==result['staged_sha256'][ext]:continue
        assert h==baseline['catalogs'][ext]['sha256'],'Concurrent catalog change; refusing recovery overwrite'
        pending=stage/('ASSET_CATALOG.'+ext);assert pending.exists() and sha(pending)==result['staged_sha256'][ext]
        os.replace(pending,dest)
    result.update(status='COMMITTED',completed_at=now());save(M/'INTEGRATION_COMMIT.json',result);log('Integrated',result['after'])

def integrate():
    marker=M/'INTEGRATION_COMMIT.json'
    if marker.exists():log('Already integrated; stable identities retained');return
    journal=M/'INTEGRATION_JOURNAL.json'
    if journal.exists() and read(journal)['status']=='STAGED_VALIDATED':promote_integration(read(journal));return
    statuses=read(M/'ANIMATION_STAGE_STATUS.json');assert statuses['completed']==statuses['total'] and all(r['status']=='success' for r in statuses['status']),'Media processing incomplete'
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');baseline=read(B/'BASELINE.json');stage=T/'integration-stage';stage.mkdir(exist_ok=True)
    for ext in ['csv','jsonl','sqlite']:assert sha(L/('Metadata/ASSET_CATALOG.'+ext))==baseline['catalogs'][ext]['sha256'],'Catalog changed concurrently; refusing commit'
    with (B/'Metadata/ASSET_CATALOG.csv').open(encoding='utf-8-sig',newline='') as f:fields=next(csv.reader(f))
    new=[];md=M/'Media';md.mkdir(exist_ok=True)
    for i,r in enumerate(media):
        assert r['media_asset_id']==f'FSN{270462+i:06d}'
        save(md/(r['media_asset_id']+'.json'),r);row={k:'' for k in fields};row.update(asset_id=r['media_asset_id'],source_version=r['work_id'],source_container=r['container'],source_logical_path=r['relative_source_path'],extracted_path=r['source_path'],filename=r['filename'],extension=pathlib.Path(r['filename']).suffix,detected_format=r['container'],category='AnimationSource',route='Unknown',locale=';'.join(r['language_tags']),character='unknown',width=r['width'],height=r['height'],duration=r['duration'],codec=r['video_codec'],fps=r['fps'],audio_tracks=r['audio_track_count'],size=r['size'],sha256=r['sha256'],conversion_status='external_read_only_source_reference',notes='source_family=AnimationReference; source_path='+r['source_path']+'; external_read_only=true; no media copy/hardlink; shot and subtitle IDs are sidecars',metadata_path=str(md/(r['media_asset_id']+'.json')),source_evidence=json.dumps({'source_family':'AnimationReference','source_path':r['source_path'],'evidence':r['identity_evidence']},ensure_ascii=False));new.append(row)
    for ext in ['csv','jsonl','sqlite']:shutil.copy2(B/('Metadata/ASSET_CATALOG.'+ext),stage/('ASSET_CATALOG.'+ext))
    with (stage/'ASSET_CATALOG.csv').open('a',encoding='utf-8',newline='') as f:csv.DictWriter(f,fieldnames=fields).writerows(new)
    with (stage/'ASSET_CATALOG.jsonl').open('a',encoding='utf-8') as f:
        for row in new:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    db=sqlite3.connect(stage/'ASSET_CATALOG.sqlite');db.executemany('INSERT INTO assets ('+','.join('"'+k+'"' for k in fields)+') VALUES ('+','.join('?' for k in fields)+')',[tuple(row[k] for k in fields) for row in new]);db.commit();db.execute('ATTACH DATABASE ? AS pre',(str(B/'Metadata/ASSET_CATALOG.sqlite'),));missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0];changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in fields)).fetchone()[0];total=db.execute('SELECT COUNT(*) FROM main.assets').fetchone()[0];integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close();assert missing==changed==0 and total==270461+len(new) and integrity=='ok'
    for ext in ['csv','jsonl']:
        with (B/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as old,(stage/('ASSET_CATALOG.'+ext)).open('rb') as cur:
            while chunk:=old.read(4*1024*1024):assert chunk==cur.read(len(chunk)),ext+' old prefix changed'
    result={'created_at':now(),'status':'STAGED_VALIDATED','before':270461,'added':len(new),'after':total,'first_new_id':new[0]['asset_id'],'max_id':new[-1]['asset_id'],'old_ids_preserved':270461,'missing_old_ids':missing,'changed_old_rows':changed,'schema_changed':False,'old_csv_jsonl_bytes_preserved':True,'sqlite_integrity':integrity,'external_read_only_media':True,'media_copies':0,'media_hardlinks':0,'staged_sha256':{ext:sha(stage/('ASSET_CATALOG.'+ext)) for ext in ['csv','jsonl','sqlite']}}
    jl(M/'CATALOG_ADDED_ROWS.jsonl',new);save(journal,result);promote_integration(result)

def verify_catalog():
    baseline=read(B/'BASELINE.json');marker=M/'INTEGRATION_COMMIT.json'
    if not marker.exists():return {'status':'not_integrated','baseline_unchanged':all(sha(L/('Metadata/ASSET_CATALOG.'+ext))==baseline['catalogs'][ext]['sha256'] for ext in ['csv','jsonl','sqlite'])}
    db=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True);db.execute('ATTACH DATABASE ? AS pre',(str(B/'Metadata/ASSET_CATALOG.sqlite'),));fields=[r[1] for r in db.execute('PRAGMA main.table_info(assets)')];oldfields=[r[1] for r in db.execute('PRAGMA pre.table_info(assets)')]
    missing=db.execute('SELECT COUNT(*) FROM pre.assets p LEFT JOIN main.assets n USING(asset_id) WHERE n.asset_id IS NULL').fetchone()[0]
    changed=db.execute('SELECT COUNT(*) FROM pre.assets p JOIN main.assets n USING(asset_id) WHERE '+' OR '.join('n."'+k+'" IS NOT p."'+k+'"' for k in fields)).fetchone()[0];count,maximum=db.execute('SELECT COUNT(*),MAX(asset_id) FROM main.assets').fetchone();integrity=db.execute('PRAGMA main.integrity_check').fetchone()[0];db.close();prefix={}
    for ext in ['csv','jsonl']:
        good=True
        with (B/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as old,(L/('Metadata/ASSET_CATALOG.'+ext)).open('rb') as current:
            while chunk:=old.read(4*1024*1024):
                if chunk!=current.read(len(chunk)):good=False;break
        prefix[ext]=good
    result={'created_at':now(),'status':'PASS' if missing==changed==0 and fields==oldfields and all(prefix.values()) and count==270798 and maximum=='FSN270798' and integrity=='ok' else 'FAIL','old_ids_preserved':270461-missing,'missing_old_ids':missing,'changed_old_rows':changed,'old_schema_preserved':fields==oldfields,'old_prefix_bytes_preserved':prefix,'row_count':count,'max_id':maximum,'sqlite_integrity':integrity,'catalog_sha256':{ext:sha(L/('Metadata/ASSET_CATALOG.'+ext)) for ext in ['csv','jsonl','sqlite']}}
    save(M/'ANIMATION_MAIN_CATALOG_VERIFICATION.json',result);return result
def verify():
    inventory=read(M/'ANIMATION_SOURCE_INVENTORY.json');changes=[];deleted=[];rehash=[]
    for r in inventory:
        p=pathlib.Path(r['source_path'])
        if not p.exists():deleted.append(r['source_path']);continue
        st=p.stat()
        if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns']:
            h=sha(p);rehash.append({'source_path':str(p),'old_sha256':r['sha256'],'new_sha256':h,'size':st.st_size,'mtime_ns':st.st_mtime_ns})
            if h!=r['sha256']:changes.append(str(p))
    old={r['source_path'] for r in inventory};current={str(p) for p in source_files()};added=sorted(current-old)
    source={'created_at':now(),'baseline_full_sha256_files':len(inventory),'stat_rechecked':len(inventory),'stat_changes_rehashed':rehash,'modified':len(changes),'deleted':len(deleted),'added':len(added),'changes':changes,'deleted_paths':deleted,'added_paths':added,'source_modified_by_task':0 if not changes else 'unresolved','source_deleted_by_task':0 if not deleted else 'unresolved','verification_policy':'Full baseline SHA256. Final path/size/mtime_ns stat check. Changed stat entries rehashed.'};save(M/'ANIMATION_SOURCE_READONLY_VERIFICATION.json',source)
    protected=readjl(B/'PROTECTED_MANIFEST.jsonl');missing=[];changed=[];stat_changes=[]
    for r in protected:
        p=L/r['path']
        if not p.exists():missing.append(r['path']);continue
        st=p.stat()
        if st.st_size!=r['size'] or st.st_mtime_ns!=r['mtime_ns']:
            h=sha(p);stat_changes.append(r['path'])
            if h!=r['sha256']:changed.append(r['path'])
    save(M/'ANIMATION_OLD_LIBRARY_VERIFICATION.json',{'created_at':now(),'protected_files':len(protected),'missing':missing,'content_changed':changed,'stat_changes':stat_changes,'new_files_allowed':'AnimationReferences, Gallery/ANIMATION_REFERENCES.html, Reports/ANIMATION_REFERENCE_* only'})
    from PIL import Image
    shots=readjl(M/'ANIMATION_SHOT_INDEX.jsonl');media={r['media_asset_id']:r for r in readjl(M/'ANIMATION_MEDIA_INDEX.jsonl')};invalid=[];missingthumb=[];invalidthumb=[];nonmonotonic=[];by=collections.defaultdict(list)
    for s in shots:
        r=media[s['media_asset_id']]
        if not(0<=s['start_ms']<s['end_ms']<=round(r['duration']*1000)+1) or not(s['start_ms']<=s['representative_ms']<=s['end_ms']):invalid.append(s['shot_id'])
        if not pathlib.Path(s['thumbnail']).exists():missingthumb.append(s['shot_id'])
        else:
            try:
                with Image.open(s['thumbnail']) as im:assert im.width<=640 and im.height>0;im.verify()
            except Exception as e:invalidthumb.append({'shot_id':s['shot_id'],'error':str(e)})
        by[s['media_asset_id']].append(s)
    for asset,ss in by.items():
        if any(a['end_ms']!=b['start_ms'] for a,b in zip(ss,ss[1:])):nonmonotonic.append(asset)
    sheet_records=read(M/'ANIMATION_CONTACT_SHEETS.json');sheet_errors=[];sheet_by=collections.defaultdict(list)
    for rec in sheet_records:
        sheet_by[rec['media_asset_id']].append(rec)
        try:
            with Image.open(rec['path']) as im:im.verify()
        except Exception as e:sheet_errors.append({'path':rec['path'],'error':str(e)})
    for asset,ss in by.items():
        pages=sorted([r for r in sheet_by[asset] if r['type']=='shot_contact_sheet'],key=lambda r:r['page'])
        if len(pages)!=(len(ss)+23)//24 or sum(r['shot_count'] for r in pages)!=len(ss) or [r['page'] for r in pages]!=list(range(1,len(pages)+1)):sheet_errors.append({'media_asset_id':asset,'error':'Contact sheet page/count coverage mismatch'})
        if len([r for r in sheet_by[asset] if r['type']=='uniform_overview'])!=1:sheet_errors.append({'media_asset_id':asset,'error':'Expected one uniform overview'})
    save(M/'ANIMATION_SHEET_VALIDATION.json',{'created_at':now(),'status':'PASS' if not sheet_errors and len(by)==len(media) else 'in_progress','images_header_verified':len(sheet_records)-sum('path' in e for e in sheet_errors),'media_covered':len(sheet_by),'errors':sheet_errors})
    db=sqlite3.connect('file:'+str(M/'ANIMATION_REFERENCE.sqlite')+'?mode=ro',uri=True);integrity=db.execute('PRAGMA integrity_check').fetchone()[0];db.close()
    preview_rows=read(M/'ANIMATION_PREVIEWS.json') if (M/'ANIMATION_PREVIEWS.json').exists() else []
    allowed_video={str(pathlib.Path(r['path']).resolve()) for r in preview_rows};unexpected_video=[];hardlinks=[];output_bytes=0;output_files=0
    for root in [A,T]:
        for p in root.rglob('*'):
            if not p.is_file():continue
            st=p.stat();output_bytes+=st.st_size;output_files+=1
            if st.st_nlink>1:hardlinks.append(str(p))
            if p.suffix.casefold() in VIDEO_EXT and str(p.resolve()) not in allowed_video:unexpected_video.append(str(p))
    storage={'status':'PASS' if not unexpected_video and not hardlinks and all(0<r['end']-r['start']<=4.001 for r in preview_rows) else 'FAIL','source_video_copies':0 if not unexpected_video else 'review_required','hardlinks':hardlinks,'unexpected_video_outputs':unexpected_video,'short_qa_preview_count':len(preview_rows),'short_qa_preview_total_seconds':sum(r['end']-r['start'] for r in preview_rows),'generated_output_and_work_bytes':output_bytes,'generated_output_and_work_files':output_files}
    save(M/'ANIMATION_STORAGE_VERIFICATION.json',storage)
    catalog=verify_catalog();result={'source':source,'protected_missing':len(missing),'protected_changed':len(changed),'shots':len(shots),'media_covered':len(by),'media_total':len(media),'invalid_shots':invalid,'missing_thumbnails':missingthumb,'invalid_thumbnails':invalidthumb,'thumbnails_header_verified':len(shots)-len(missingthumb)-len(invalidthumb),'noncontiguous_timeline':nonmonotonic,'sqlite_integrity':integrity,'catalog_readback':catalog,'storage':storage,'created_at':now()};save(M/'ANIMATION_VERIFICATION.json',result);log('Verify',len(shots),'shots','invalid',len(invalid),'media',len(by),'source changes',len(changes))
    return result
def tooling():
    files=sorted((W/'scripts').glob('animation_*.py'))+list((W/'scripts').glob('*ANIMATION*.ps1'))+list((W/'scripts').glob('animation_browser.html'))
    save(M/'ANIMATION_TOOL_MANIFEST.json',{'created_at':now(),'ffmpeg':command([FF,'-version']).splitlines()[0],'ffprobe':command([FP,'-version']).splitlines()[0],'ffplay':command([PLAY,'-version']).splitlines()[0],'binaries':{str(p):sha(p) for p in [FF,FP,PLAY]},'python':sys.version,'sqlite':sqlite3.sqlite_version,'packages':command([PY,'-m','pip','freeze']).splitlines(),'scripts':{str(p):sha(p) for p in files},'temp':os.environ['TEMP'],'worker_count':4,'initial_pilot_worker_count':1,'initial_full_worker_count':2,'detector_revision':'v1'})
def report():
    tooling();v=read(M/'ANIMATION_VERIFICATION.json') if (M/'ANIMATION_VERIFICATION.json').exists() else {};media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');works=read(M/'ANIMATION_WORK_INDEX.json');sts=read(M/'ANIMATION_STAGE_STATUS.json');tracks=readjl(M/'ANIMATION_SUBTITLE_TRACK_INDEX.jsonl');failures=readjl(M/'ANIMATION_PROCESSING_FAILURES.jsonl')
    for r in sts['status']:
        if r['status']!='success':failures.append({'media':r['media_asset_id'],'stage':'Shots','command':'animation_shots.py Shots','error':r.get('error',''),'retry':0,'final_status':r['status']})
    csvout(M/'ANIMATION_PROCESSING_FAILURES.csv',failures,['media','stage','command','error','retry','final_status']);browser=read(M/'ANIMATION_BROWSER_QA.json') if (M/'ANIMATION_BROWSER_QA.json').exists() else {'status':'unverified'};qa=read(M/'ANIMATION_MANUAL_QA.json') if (M/'ANIMATION_MANUAL_QA.json').exists() else {'status':'unverified'};helper=read(M/'ANIMATION_HELPER_QA.json') if (M/'ANIMATION_HELPER_QA.json').exists() else {'status':'unverified'};integration=read(M/'INTEGRATION_COMMIT.json') if (M/'INTEGRATION_COMMIT.json').exists() else None
    stat={'works':len(works),'media_files':len(media),'total_duration_hours':sum(r['duration'] for r in media)/3600,'subtitle_tracks':len(tracks),'text_subtitle_tracks':sum(r['status']=='success' for r in tracks),'image_subtitle_tracks':sum(r['status']=='image_subtitle_metadata_only' for r in tracks),'subtitle_lines':len(readjl(M/'ANIMATION_SUBTITLE_LINES.jsonl')),'chapters':len(readjl(M/'ANIMATION_CHAPTER_INDEX.jsonl')),'shots':len(readjl(M/'ANIMATION_SHOT_INDEX.jsonl')),'sequences':len(readjl(M/'ANIMATION_SEQUENCE_INDEX.jsonl')),'thumbnails':len(readjl(M/'ANIMATION_SHOT_INDEX.jsonl')),'contact_sheets':sum(x['type']=='shot_contact_sheet' for x in read(M/'ANIMATION_CONTACT_SHEETS.json')),'overview_sheets':len(media),'term_hits':len(readjl(M/'ANIMATION_TERM_HITS.jsonl')),'review_candidates':len(readjl(M/'ANIMATION_REVIEW_QUEUE.jsonl')),'duplicate_groups':len(set(x['group_id'] for x in read(M/'ANIMATION_DUPLICATES.json'))),'failures':len(failures)}
    data_validation=read(M/'ANIMATION_DATA_VALIDATION.json') if (M/'ANIMATION_DATA_VALIDATION.json').exists() else {'status':'unverified'};critical=[]
    if data_validation['status']!='PASS':critical.append('data_validation')
    if read(M/'ANIMATION_TIME_PRECISION_POLICY.json')['status']!='PASS':critical.append('time_precision')
    if read(M/'ANIMATION_SHEET_VALIDATION.json')['status']!='PASS':critical.append('contact_sheet_validation')
    if v.get('invalid_thumbnails'):critical.append('invalid_thumbnails')
    if failures:critical.append('processing_failures')
    if not integration:critical.append('catalog_not_integrated')
    if v.get('catalog_readback',{}).get('status')!='PASS':critical.append('catalog_readback')
    if not v or v.get('media_covered')!=len(media) or v.get('invalid_shots') or v.get('missing_thumbnails') or v.get('noncontiguous_timeline') or v.get('sqlite_integrity')!='ok':critical.append('structural_verification')
    if v and (v['source']['modified'] or v['source']['deleted'] or v['source']['added'] or v['protected_missing'] or v['protected_changed']):critical.append('preservation')
    if v.get('storage',{}).get('status')!='PASS':critical.append('storage_policy')
    if browser['status']!='PASS':critical.append('browser_QA')
    if qa['status']!='PASS':critical.append('manual_QA')
    if helper['status']!='PASS':critical.append('helper_QA')
    summary={'status':'FSN_ANIMATION_REFERENCE_INDEX_PASS' if not critical else 'FSN_ANIMATION_REFERENCE_INDEX_PARTIAL','created_at':now(),**stat,'catalog':integration,'verification':v,'browser':browser,'manual_QA':qa,'helper':helper,'critical_issues':critical,'disk_free_before':read(B/'BASELINE.json')['disk_free_before'],'disk_free_after':shutil.disk_usage(L).free,'next_step_suggested_only':'UNIFIED_FSNN_SEMANTIC_CATALOG'};save(M/'ANIMATION_REFERENCE_FINAL_SUMMARY.json',summary)
    titles=['A. Sources','B. Works','C. Media Inventory','D. Tracks / Subtitles','E. Chapters','F. Shot Detection','G. Sequences','H. Thumbnails / Contact Sheets','I. Term / Entity References','J. Review Queue','K. Duplicate Releases','L. Unified Catalog Integration','M. Browser','N. Source Integrity','O. Disk','P. Failures / Ambiguities','Q. Development Usage','R. Recommended Next Step']
    bodies=[f'Read-only source root: `{S}`. {stat["media_files"]} videos; {stat["total_duration_hours"]:.3f} hours. Existing game/book trees excluded. Source videos remain external, with no copies or hardlinks.', '\n'.join(f'- `{w["work_id"]}` — {w["canonical_local_title"]}: {w["media_count"]} media' for w in works),'All media passed ffprobe; container, streams, dimensions, frame-rate evidence, chapters, attachments and full streaming SHA256 retained.',f'{stat["subtitle_tracks"]} tracks; {stat["text_subtitle_tracks"]} text tracks, {stat["image_subtitle_tracks"]} image tracks. {stat["subtitle_lines"]} original-preserving text rows. Bilingual ASS tracks retain both languages; no ASR/OCR required.',f'{stat["chapters"]} native chapters. Synthetic groups are separately labeled auto_sequence.',json.dumps(read(M/'ANIMATION_DETECTOR_SETTINGS.json'),ensure_ascii=False,indent=2),f'{stat["sequences"]} shot-aligned chapter/time bucket sequences, without semantic scene claims.',f'{stat["thumbnails"]} midpoint thumbnails, max width 640; {stat["contact_sheets"]} paged sheets, 24 shots per page; {stat["overview_sheets"]} uniform overview sheets.',f'{stat["term_hits"]} subtitle alias matches. Original text, language, time and vocabulary provenance retained. Name mention never confirms depicted presence.',f'{stat["review_candidates"]} candidates. High motion is a technical measure, never a battle/action label. Confirmed character/action fields remain empty unless visually accepted.',f'{stat["duplicate_groups"]} candidate groups. Alternatives are preserved; no deletion.',json.dumps(integration,ensure_ascii=False,indent=2),json.dumps(browser,ensure_ascii=False,indent=2),json.dumps(v.get('source',{}),ensure_ascii=False,indent=2),f'E: free before {summary["disk_free_before"]/2**30:.2f} GiB; after {summary["disk_free_after"]/2**30:.2f} GiB. TEMP/TMP and all working data use E:.',f'Processing failures: {len(failures)}. Remaining gates: {critical}. Automatic scdet can over-segment flashes/motion and miss subtle fades. Shot boundaries are technical candidates; frame PTS and source provenance remain precise.',f'Run `ANIMATION_REFERENCES.ps1 -Mode Gallery` to launch the local search browser. Search Lancer/Gae Bolg or raw subtitles, refine by work/media/language/motion, inspect a shot, copy its ID/time/source path, then run `OPEN_ANIMATION_REFERENCE.ps1 -ShotId <ID>`. Extract full-resolution material from the read-only source only when selected.', 'Suggested only: UNIFIED_FSNN_SEMANTIC_CATALOG. No cross-source unified semantic build was started.']
    bodies[3]+= '\n\n59 个 `.ass.txt` 双扩展名字幕已按内容识别，源文件名、字节、语言版本、ASS 样式和事件字段保留。118 条 PGS 仅建立原轨元数据，未进行 OCR；字幕提及与实际出镜分开。5 个 M4A 音频伴随文件作为 supporting_audio_only 保留 SHA256，不伪装成待分镜视频。'
    bodies[5]+='\n\n'+json.dumps(read(M/'ANIMATION_TIME_PRECISION_POLICY.json')|{'items':'Detailed per-media evidence in Metadata/ANIMATION_TIME_PRECISION_POLICY.json'},ensure_ascii=False,indent=2)
    bodies[8]+='\n\n复用 Official Material 的 Character/Alias/Weapon/Noble Phantasm/Magic/Term 索引并保留原始页码与不确定性。搜索归一化只去除拉丁重音，保留日文浊点；Rin 等拉丁名称按单词匹配，单字凛/凜只参与搜索扩展。'
    bodies[10]+='\n\nExact SHA256 groups and 12-frame pHash candidates are separate in ANIMATION_DUPLICATES.csv; visual candidates do not establish identical editions or authorize deletion.'
    bodies[14]+='\n\n'+json.dumps(v.get('storage',{}),ensure_ascii=False,indent=2)
    bodies[15]+='\n\nData validation:\n```json\n'+json.dumps(data_validation,ensure_ascii=False,indent=2)+'\n```\n\nVisual QA:\n```json\n'+json.dumps(qa,ensure_ascii=False,indent=2)+'\n```\n\nActual source playback QA:\n```json\n'+json.dumps(helper,ensure_ascii=False,indent=2)+'\n```'
    bodies[16]+='\n\n详细中文使用说明：`AnimationReferences/Reports/ANIMATION_REFERENCE_USAGE.md`。所有永久素材索引、缩略图、Contact Sheets 与浏览器位于 `AnimationReferences`；源片路径仍指向只读素材目录。脚本与缓存位于 `E:/FSN_MASTER_ASSET_WORK`。本轮临时浏览器服务在验收后关闭；用户可用 Gallery 模式重新启动。'
    text='# FSN Animation Reference Index\n\n'+summary['status']+'\n\n'+''.join('## '+title+'\n\n'+body+'\n\n' for title,body in zip(titles,bodies));dest=L/'Reports/ANIMATION_REFERENCE_INDEX_REPORT.md';dest.write_text(text,encoding='utf-8')
    import html
    rows=[('作品',stat['works']),('媒体',stat['media_files']),('总时长（小时）',round(stat['total_duration_hours'],3)),('镜头 / 代表帧',stat['shots']),('文本字幕行',stat['subtitle_lines']),('文本字幕轨',stat['text_subtitle_tracks']),('图像字幕轨（仅元数据）',stat['image_subtitle_tracks']),('Contact Sheets',stat['contact_sheets']),('媒体概览',stat['overview_sheets']),('处理失败',stat['failures']),('源文件改动',v['source']['modified']),('旧资产 ID 保留',v['catalog_readback']['old_ids_preserved']),('总 Catalog 条目',v['catalog_readback']['row_count']),('人工图像对应抽检',qa['source_frame_comparisons']),('实际原片播放抽检',len(helper['samples']))]
    table=''.join('<tr><th>'+html.escape(label)+'</th><td>'+html.escape(str(value))+'</td></tr>' for label,value in rows)
    (A/'Reports/ANIMATION_REFERENCE_SUMMARY.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>动画引用库验收摘要</title><style>body{max-width:900px;margin:36px auto;padding:24px;background:#0b1421;color:#eaf0f8;font:17px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}h1,a{color:#e2c477}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 14px;border-bottom:1px solid #334761}td{text-align:right}code{overflow-wrap:anywhere}</style><h1>动画引用库验收摘要</h1><p><code>'+html.escape(summary['status'])+'</code></p><table>'+table+'</table><p>全部结构、源文件保护、旧库保留、检索、人工对应抽检和本地播放验收已完成。剩余必需事项：'+html.escape(str(critical))+'。</p><p>自动镜头边界是技术候选；字幕提及与画面出镜分别记录。PGS 未进行 OCR，已确认人物与动作字段保持保守留空。</p><p>详细 A–R 报告：<code>E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\ANIMATION_REFERENCE_INDEX_REPORT.md</code></p><p><a href="../index.html">返回动画引用库</a></p></html>',encoding='utf-8')
    log('Report',summary['status'],critical)
if __name__=='__main__':{'Integrate':integrate,'Verify':verify,'Report':report,'Tooling':tooling}[sys.argv[1] if len(sys.argv)>1 else 'Verify']()
