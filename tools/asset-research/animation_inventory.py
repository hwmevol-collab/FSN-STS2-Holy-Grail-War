from animation_common import *

def subtitle_format(p):
    ext=p.suffix.casefold()
    if ext in SUB_EXT:return ext[1:]
    if ext not in {'.txt','.text',''}:return ''
    with p.open('rb') as f:raw=f.read(32768)
    text=''
    for enc in ['utf-8-sig','utf-16','gb18030','cp932','big5']:
        try:text=raw.decode(enc);break
        except UnicodeError:pass
    if re.search(r'^\s*\[Script Info\]',text,re.M|re.I) and re.search(r'^\s*\[(?:Events|V4\+? Styles)\]',text,re.M|re.I):return 'ssa' if p.name.casefold().endswith('.ssa.txt') else 'ass'
    if text.lstrip().startswith('WEBVTT'):return 'vtt'
    if re.search(r'^\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}',text,re.M):return 'srt'
    return ''
def inventory():
    frozen_baseline();files=source_files();candidates=[]
    if (M/'ANIMATION_SOURCE_INVENTORY.json').exists():
        initial=read(M/'ANIMATION_SOURCE_INVENTORY.json')
        if not (T/'SOURCE_BASELINE_INITIAL.json').exists():save(T/'SOURCE_BASELINE_INITIAL.json',initial)
        for old in initial:
            p=pathlib.Path(old['source_path']);assert p.exists(),'Source disappeared since frozen inventory: '+str(p);st=p.stat()
            assert st.st_size==old['size'] and st.st_mtime_ns==old['mtime_ns'],'Source stat changed; verify against preserved baseline before refreshing: '+str(p)
    for p in files:
        sig=magic(p);ext=p.suffix.lower();sf=subtitle_format(p)
        kind='subtitle' if sf else 'video_candidate' if ext in VIDEO_EXT or sig!='other' else 'font' if ext in FONT_EXT else 'font_archive' if 'font' in p.name.lower() and ext in {'.rar','.zip','.7z'} else 'supporting_file'
        st=p.stat();candidates.append({'source_path':str(p),'relative_source_path':str(p.relative_to(S)),'filename':p.name,'kind':kind,'magic':'subtitle_'+sf+'_text' if sf in {'ass','ssa','srt','vtt'} else sig,'subtitle_format':sf,'size':st.st_size,'mtime':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat(),'mtime_ns':st.st_mtime_ns})
    save(T/'DISCOVERY.json',{'created_at':now(),'excluded_roots':[str(p) for p in S.iterdir() if p.is_dir() and excluded(p.name)],'files':candidates});log('Discovered',len(candidates),'video candidates',sum(r['kind']=='video_candidate' for r in candidates))
    rows=[];probe_dir=M/'Probes';probe_dir.mkdir(exist_ok=True);cache=T/'inventory-cache';cache.mkdir(exist_ok=True)
    for i,r in enumerate(candidates):
        p=pathlib.Path(r['source_path']);key=hashlib.sha256(str(p).encode()).hexdigest()[:20];cp=cache/(key+'.json')
        if cp.exists():
            old=read(cp)
            if old['size']==r['size'] and old['mtime_ns']==r['mtime_ns']:
                if r['kind']=='subtitle':old.update(kind='subtitle',subtitle_format=r['subtitle_format'],magic=r['magic']);save(cp,old)
                if old.get('kind')=='no_video_stream' and old.get('audio_track_count',0)>0:old.update(technical_status='supporting_audio_only',notes='Audio-only companion; preserved with full source SHA256; no video stream to segment');save(cp,old)
                rows.append(old);continue
        r['sha256']=sha(p)
        if r['kind']=='video_candidate':
            try:
                probe=json.loads(command([FP,'-v','error','-show_format','-show_streams','-show_chapters','-of','json',p]));save(probe_dir/(key+'.json'),probe);r['probe_path']=str(probe_dir/(key+'.json'))
                vs=[x for x in probe['streams'] if x['codec_type']=='video' and not x.get('disposition',{}).get('attached_pic')];v=vs[0] if vs else {};fmt=probe.get('format',{});tags=fmt.get('tags',{})
                r.update(kind='video' if vs else 'no_video_stream',container=fmt.get('format_name',''),duration=float(fmt.get('duration',v.get('duration',0)) or 0),video_codec=v.get('codec_name',''),width=v.get('width',0),height=v.get('height',0),pixel_format=v.get('pix_fmt',''),bit_depth=v.get('bits_per_raw_sample') or (10 if '10' in v.get('pix_fmt','') else 8),fps=v.get('avg_frame_rate',''),frame_rate_mode='candidate_vfr' if v.get('avg_frame_rate')!=v.get('r_frame_rate') else 'nominal_cfr_unverified',audio_track_count=sum(x['codec_type']=='audio' for x in probe['streams']),subtitle_track_count=sum(x['codec_type']=='subtitle' for x in probe['streams']),chapter_count=len(probe.get('chapters',[])),attachment_count=sum(x['codec_type']=='attachment' for x in probe['streams']),language_tags=[x.get('tags',{}).get('language','und') for x in probe['streams']],title_tag=tags.get('title',''),source_group=p.relative_to(S).parts[0] if p.parent!=S else 'root',notes='',technical_status='success' if vs and float(fmt.get('duration',0) or 0)>0 else 'failed',video_time_base=v.get('time_base',''),video_start_time=float(v.get('start_time',0) or 0),video_start_pts=v.get('start_pts',0))
            except Exception as e:r.update(kind='unreadable_media',technical_status='failed',notes=str(e));log('PROBE FAILURE',p.name,str(e)[:200])
        save(cp,r);rows.append(r)
        if i%10==0 or r['kind']=='video':log('Inventory',i+1,'/',len(candidates),r['filename'],r.get('duration',''))
    csvout(M/'ANIMATION_SOURCE_INVENTORY.csv',rows);save(M/'ANIMATION_SOURCE_INVENTORY.json',rows)
    videos=[x for x in rows if x['kind']=='video'];save(T/'INVENTORY_SUMMARY.json',{'videos':len(videos),'duration_hours':sum(x['duration'] for x in videos)/3600,'video_GiB':sum(x['size'] for x in videos)/2**30,'sources':len(rows),'source_groups':dict(collections.Counter(x['source_group'] for x in videos))});log('Inventory done',read(T/'INVENTORY_SUMMARY.json'))
if __name__=='__main__':inventory()
