from animation_common import *
WORKS={'FSN2006_TV':('Fate/stay night 2006','TV'),'FSN_TV_REPRO':('Fate/stay night TV Reproduction','Special'),'UBW_TV':('Fate/stay night Unlimited Blade Works TV','TV'),'UBW_2010_MOVIE':('Fate/stay night Unlimited Blade Works The Movie','Movie'),'UBW_SUNNY_DAY':('Sunny Day','Special'),'HF_MOVIE':("Fate/stay night Heaven’s Feel",'Movie'),'FATE_ZERO':('Fate/Zero','TV'),'EMIYA_GOHAN':('卫宫家今天的饭','TV'),'CARNIVAL_PHANTASM':('Carnival Phantasm','OVA'),'CARNIVAL_SPECIAL_SEASON':('Carnival Phantasm Special Season','Special'),'CURTAIN_RAISER':('Curtain Raiser','Special'),'SHINJI_DIARY':("Rider’s Shinji Observation Diary",'Special'),'REALTA_NUA_OP':('Fate/stay night Realta Nua PSVita OP','GameOP'),'HF_REMASTERED_OP':('Heaven’s Feel Opening Remastered','OP'),'FHA_VITA_OP':('Fate/hollow ataraxia PSVita OP','GameOP'),'TMFES':('TYPE-MOON FES SPDISC','EventVideo'),'FATE_PROTOTYPE':('Fate/Prototype','Special')}
def identity(r):
    rel=r['relative_source_path'];n=r['filename'];low=rel.casefold()
    if 'tmfes' in low:w='TMFES'
    elif 'curtain raiser' in low:w='CURTAIN_RAISER'
    elif 'shinji observation' in low:w='SHINJI_DIARY'
    elif 'special_season' in low:w='CARNIVAL_SPECIAL_SEASON'
    elif 'fate_prototype' in low:w='FATE_PROTOTYPE'
    elif 'carnival' in low:w='CARNIVAL_PHANTASM'
    elif 'reproduction' in low:w='FSN_TV_REPRO'
    elif 'the movie' in low:w='UBW_2010_MOVIE'
    elif 'sunny' in low:w='UBW_SUNNY_DAY'
    elif 'unlimited blade works' in low:w='UBW_TV'
    elif "heaven's feel" in low:w='HF_MOVIE'
    elif 'opening - remastered' in low:w='HF_REMASTERED_OP'
    elif 'fate zero' in low:w='FATE_ZERO'
    elif 'gohan' in low or '卫宫家今天的饭' in low:w='EMIYA_GOHAN'
    elif 'realt' in low:w='REALTA_NUA_OP'
    elif 'ataraxia' in low:w='FHA_VITA_OP'
    elif '[fate stay night]' in low:w='FSN2006_TV'
    else:w='UNKNOWN_'+hashlib.sha256(r['source_group'].encode()).hexdigest()[:8].upper()
    typ=WORKS.get(w,(r['source_group'],'Other'))[1];special='';ep='';season='';label=''
    b=re.findall(r'\[([^]]+)\]',n)
    marker=next((x for x in b if re.fullmatch(r'(?:NC)?(?:OP|ED)\d*|PV|CM|SP(?: Anime)?\d*|menu|Tokuten|Animation Material|Remix|Sunny Day|EX_Season|Ilya__s_Castle|Tohno_Akiha_wa_Nayandeiru',x,re.I)),None)
    if marker:
        ix=b.index(marker);nums=[x for x in b[ix+1:] if re.fullmatch(r'\d{1,3}|D\d+',x,re.I)];special=marker+(' '+' '.join(nums) if nums else '');typ=('NCOP' if marker.upper().startswith('NC') else 'OP') if 'OP' in marker.upper() else ('NCED' if marker.upper().startswith('NC') else 'ED') if 'ED' in marker.upper() else 'Menu' if marker.upper()=='MENU' else 'PV' if marker.upper() in ['PV','CM'] else 'Special';label=special
    else:
        m=re.search(r'S(\d+)E(\d+)',n,re.I)
        if m:season=int(m[1]);ep=int(m[2]);label=f'Episode {ep:02d}'
        else:
            nums=[x for x in b if re.fullmatch(r'\d{1,3}',x)]
            if nums:ep=int(nums[0]);label=f'Episode {ep:02d}' if w!='TMFES' else f'SPDISC {ep:02d}'
    if w=='HF_MOVIE':
        m=re.search(r"Heaven's Feel (III|II|I)\.([^\]]+)",n)
        if m:label=m[1]+'.'+m[2]+(' / '+special if special else '');ep={'I':1,'II':2,'III':3}[m[1]]
    if not label:label=r['title_tag'] or (pathlib.Path(rel).parent.name if n=='videoplayback.webm' else pathlib.Path(n).stem)
    return w,typ,season,ep,label,special
def build_media():
    src=read(M/'ANIMATION_SOURCE_INVENTORY.json');videos=[r for r in src if r['kind']=='video'];reg=M/'MEDIA_ID_REGISTRY.json'
    if reg.exists():registry=read(reg)
    else:registry={}
    rows=[]
    for r in videos:
        key=r['relative_source_path'];entry=registry.get(key)
        if entry:assert entry['sha256']==r['sha256'],'Source changed; create new revision explicitly'
        else:entry={'asset_id':f'FSN{270462+len(registry):06d}','sha256':r['sha256']};registry[key]=entry
        asset=entry['asset_id'];w,typ,season,ep,label,special=identity(r);p=read(r['probe_path']);langs=lambda kind:[x.get('tags',{}).get('language','und') for x in p['streams'] if x['codec_type']==kind]
        rows.append(dict(r,media_asset_id=asset,work_id=w,media_id='ANI-'+asset,season=season,episode_number=ep,episode_label=label,episode_title='',special_label=special,source_filename=r['filename'],media_type=typ,resolution=f"{r['width']}x{r['height']}",codec=r['video_codec'],audio_languages=langs('audio'),subtitle_languages=langs('subtitle'),identity_status='local_filename_identity' if not w.startswith('UNKNOWN') else 'unresolved',identity_evidence={'filename':r['filename'],'relative_path':key,'container_title':r['title_tag']},characters_present_confirmed=[],characters_present_candidate=[],source_family='AnimationReference',external_read_only=True,container_start_time=float(p.get('format',{}).get('start_time',0) or 0)))
    rows.sort(key=lambda r:r['media_asset_id']);save(reg,registry);jl(M/'ANIMATION_MEDIA_INDEX.jsonl',rows);csvout(M/'ANIMATION_MEDIA_INDEX.csv',rows)
    works=[]
    for w in dict.fromkeys(r['work_id'] for r in rows):
        rs=[r for r in rows if r['work_id']==w];title,typ=WORKS.get(w,(rs[0]['source_group'],'Other'));works.append({'work_id':w,'canonical_local_title':title,'source_title':list(dict.fromkeys(r['source_group'] for r in rs)),'work_type':typ,'source_root':list(dict.fromkeys(str(pathlib.Path(r['source_path']).parent) for r in rs)),'media_count':len(rs),'status':'local_identity' if not w.startswith('UNKNOWN') else 'unresolved','evidence':{'filenames':[r['filename'] for r in rs],'container_titles':list(set(r['title_tag'] for r in rs if r['title_tag']))}})
    csvout(M/'ANIMATION_WORK_INDEX.csv',works);save(M/'ANIMATION_WORK_INDEX.json',works);log('Media',len(rows),'works',len(works))
    return rows,src
def decode_text(p):
    data=pathlib.Path(p).read_bytes()
    for enc in ['utf-8-sig','utf-16','gb18030','cp932','big5']:
        try:return data.decode(enc),enc
        except UnicodeError:pass
    return data.decode('utf-8',errors='replace'),'utf-8 replacement'
def stamp(s):
    h,m,sec=s.strip().replace(',', '.').split(':');return round((int(h)*3600+int(m)*60+float(sec))*1000)
def plain(s):
    drawing=False;parts=[]
    for part in re.split(r'(\{[^}]*\})',s):
        if part.startswith('{'):
            m=re.search(r'\\p(\d+)(?!\d)',part)
            if m:drawing=int(m[1])>0
        elif not drawing:parts.append(part)
    s=''.join(parts);s=re.sub(r'<[^>]+>','',s);return s.replace('\\N','\n').replace('\\n','\n').replace('\\h',' ').strip()
def parse_subtitle(p,track):
    text,enc=decode_text(p);ext=pathlib.Path(p).suffix.lower();result=[]
    if ext in ['.ass','.ssa']:
        active=False;fields=[]
        for raw in text.splitlines():
            if raw.startswith('['):active=raw.strip().casefold()=='[events]'
            if not active:continue
            if raw.lower().startswith('format:'):fields=[x.strip().lower() for x in raw.split(':',1)[1].split(',')]
            elif raw.lower().startswith('dialogue:') and fields:
                vals=raw.split(':',1)[1].lstrip().split(',',len(fields)-1);d=dict(zip(fields,vals));result.append({'start_ms':stamp(d['start']),'end_ms':stamp(d['end']),'raw_text':d.get('text',''),'style':d.get('style',''),'speaker_field':d.get('name',''),'layer':d.get('layer',d.get('marked','')),'margin_l':d.get('marginl',''),'margin_r':d.get('marginr',''),'margin_v':d.get('marginv',''),'effect':d.get('effect',''),'event_raw':raw})
    else:
        for block in re.split(r'\r?\n\s*\r?\n',text):
            lines=block.splitlines();ix=next((i for i,x in enumerate(lines) if '-->' in x),None)
            if ix is None:continue
            a,b=lines[ix].split('-->',1);end=b.strip().split()[0]
            def st(s):return stamp('00:'+s if s.count(':')==1 else s)
            result.append({'start_ms':st(a.strip()),'end_ms':st(end),'raw_text':'\n'.join(lines[ix+1:]),'style':'','speaker_field':'','layer':'','margin_l':'','margin_r':'','margin_v':'','effect':'','event_raw':block})
    for i,d in enumerate(result):d.update(line_id=track['track_id']+f'-L{i+1:07d}',track_id=track['track_id'],media_asset_id=track['media_asset_id'],start_time=tc(d['start_ms']),end_time=tc(d['end_ms']),plain_text=plain(d['raw_text']),language=track['language'],text_encoding=enc,notes='ASS drawing command' if re.search(r'\\p[1-9]',d['raw_text']) else '')
    return result
def tracks():
    rows,src=build_media();tracks=[];subs=[];chapters=[];lines=[];attachments=[];failures=[];anomalies=[]
    raws=A/'Subtitles/Raw';raws.mkdir(parents=True,exist_ok=True)
    for r in rows:
        asset=r['media_asset_id'];probe=read(r['probe_path']);external=[];vp=pathlib.Path(r['source_path']);cache=T/'tracks-cache'/(asset+'.json');cache.parent.mkdir(exist_ok=True)
        if cache.exists():
            d=read(cache)
            if d['sha256']==r['sha256'] and d.get('parser_revision')==4:
                tracks+=d['tracks'];subs+=d['subs'];chapters+=d['chapters'];lines+=d['lines'];attachments+=d['attachments'];failures+=d['failures'];anomalies+=d['anomalies'];continue
        mt=[];ms=[];mc=[];ml=[];ma=[];mf=[];mn=[]
        for st in probe['streams']:
            tags=st.get('tags',{});idx=st['index'];tr={'track_id':f'{asset}-T{idx:03d}','media_asset_id':asset,'stream_index':idx,'track_type':st['codec_type'],'language':tags.get('language','und'),'codec':st.get('codec_name',''),'title':tags.get('title',''),'default':st.get('disposition',{}).get('default',0),'forced':st.get('disposition',{}).get('forced',0),'source_type':'embedded','source_path':r['source_path'],'line_count':0,'status':'metadata_only','metadata':st};mt.append(tr)
            if st['codec_type']=='subtitle':
                codec=st.get('codec_name','');ext={'ass':'.ass','ssa':'.ssa','subrip':'.srt','webvtt':'.vtt','mov_text':'.srt','text':'.srt'}.get(codec)
                if ext:
                    dest=raws/(tr['track_id']+ext)
                    try:
                        if not dest.exists():command([FF,'-nostdin','-v','error','-i',vp,'-map',f'0:{idx}','-c:s','srt' if codec in ['mov_text','text'] else 'copy',dest])
                        sl=parse_subtitle(dest,tr);tr.update(status='success',line_count=len(sl),working_copy=str(dest),working_sha256=sha(dest));ml+=sl
                    except Exception as e:tr['status']='failed';mf.append({'media':asset,'stage':'Subtitles','command':f'ffmpeg map 0:{idx} / parse {dest}','error':str(e),'retry':0,'final_status':'failed'})
                else:tr.update(status='image_subtitle_metadata_only')
                ms.append(tr)
            elif st['codec_type']=='attachment':
                ma.append({'attachment_id':f'{asset}-A{idx:03d}','media_asset_id':asset,'stream_index':idx,'filename':tags.get('filename',''),'mimetype':tags.get('mimetype',''),'codec':st.get('codec_name',''),'source_path':r['source_path'],'status':'preserved_in_read_only_source','metadata':st})
        for c in probe.get('chapters',[]):
            cm={'media_asset_id':asset,'chapter_id':f'{asset}-CH{c["id"]}','start':float(c['start_time']),'end':float(c['end_time']),'title':c.get('tags',{}).get('title',''),'language':c.get('tags',{}).get('language','und'),'status':'source_chapter','raw_metadata':c};mc.append(cm)
        for sub in src:
            sp=pathlib.Path(sub['source_path'])
            if sub['kind']!='subtitle' or sp.parent!=vp.parent:continue
            sf=sub.get('subtitle_format') or sp.suffix[1:].casefold();logical_name=sp.name[:-4] if sp.suffix.casefold()=='.txt' else sp.name;logical_stem=pathlib.Path(logical_name).stem
            # Exact video stem plus explicit language suffix; never nearest filename guessing.
            rest=logical_stem[len(vp.stem):] if logical_stem.casefold().startswith(vp.stem.casefold()) else None
            if rest is None or (rest and not re.fullmatch(r'[._ -]*(?:scjp|tcjp|sc|tc|chs|cht|jpn|ja|jp|eng|en|zh|zh-cn|zh-tw|简|繁|简日|繁日|gb|big5)',rest,re.I)):continue
            language='zh-Hans' if re.search(r'sc|chs|简|gb',rest or '',re.I) else 'zh-Hant' if re.search(r'tc|cht|繁|big5',rest or '',re.I) else 'ja' if re.search(r'ja|jp',rest or '',re.I) else 'en' if re.search(r'eng|en',rest or '',re.I) else 'und'
            if language.startswith('zh') and re.search(r'jp|日',rest or '',re.I):language+=' + ja'
            key=hashlib.sha256(sub['relative_source_path'].encode()).hexdigest()[:12];tr={'track_id':f'{asset}-EXT-{key}','media_asset_id':asset,'language':language,'codec':sf,'title':sp.name,'default':0,'forced':0,'source_type':'external','source_path':str(sp),'source_sha256':sub['sha256'],'source_extension':sp.suffix,'format_evidence':sub.get('magic',''),'line_count':0,'status':'metadata_only'};dest=raws/(tr['track_id']+'.'+sf)
            try:
                if not dest.exists():shutil.copy2(sp,dest)
                assert sha(dest)==sub['sha256'];sl=parse_subtitle(dest,tr);tr.update(status='success',line_count=len(sl),working_copy=str(dest),working_sha256=sha(dest));ml+=sl
            except Exception as e:tr['status']='failed';mf.append({'media':asset,'stage':'Subtitles','command':'parse '+str(sp),'error':str(e),'retry':0,'final_status':'failed'})
            ms.append(tr)
        for sl in ml:
            for issue,cond in [('negative_timestamp',sl['start_ms']<0),('broken_timestamp',sl['end_ms']<sl['start_ms']),('subtitle_out_of_range',sl['end_ms']>r['duration']*1000+2000)]:
                if cond:mn.append({'media_asset_id':asset,'type':issue,'reference_id':sl['line_id'],'detail':f"{sl['start_ms']}..{sl['end_ms']} / duration {r['duration']}",'status':'review_required'})
        save(cache,{'sha256':r['sha256'],'parser_revision':4,'tracks':mt,'subs':ms,'chapters':mc,'lines':ml,'attachments':ma,'failures':mf,'anomalies':mn});tracks+=mt;subs+=ms;chapters+=mc;lines+=ml;attachments+=ma;failures+=mf;anomalies+=mn;log('Tracks',asset,len(ms),'sub tracks',len(ml),'lines')
    for name,data,fields in [('ANIMATION_TRACK_INDEX',tracks,['track_id','media_asset_id','track_type']),('ANIMATION_SUBTITLE_TRACK_INDEX',subs,['track_id','media_asset_id','language','codec','title','default','forced','source_type','source_path','line_count','status']),('ANIMATION_SUBTITLE_LINES',lines,['line_id','track_id','media_asset_id','start_time','end_time','start_ms','end_ms','raw_text','plain_text','language','style','speaker_field','notes']),('ANIMATION_CHAPTER_INDEX',chapters,['media_asset_id','chapter_id','start','end','title','language','status']),('ANIMATION_ATTACHMENT_INDEX',attachments,['attachment_id','media_asset_id','stream_index']),('ANIMATION_PROCESSING_FAILURES',failures,['media','stage','command','error','retry','final_status']),('ANIMATION_ANOMALIES',anomalies,['media_asset_id','type','reference_id','detail','status'])]:
        csvout(M/(name+'.csv'),data, list(dict.fromkeys(fields+[k for r in data for k in r])));jl(M/(name+'.jsonl'),data)
    norm=A/'Subtitles/Normalized';norm.mkdir(parents=True,exist_ok=True)
    for r in rows:
        jl(norm/(r['media_asset_id']+'.jsonl'),[x for x in lines if x['media_asset_id']==r['media_asset_id']]);r['subtitle_languages']=list(dict.fromkeys(x['language'] for x in subs if x['media_asset_id']==r['media_asset_id']))
    jl(M/'ANIMATION_MEDIA_INDEX.jsonl',rows);csvout(M/'ANIMATION_MEDIA_INDEX.csv',rows)
    linked={x['source_path'] for x in subs if x['source_type']=='external'};csvout(M/'ANIMATION_UNMATCHED_SUBTITLES.csv',[x for x in src if x['kind']=='subtitle' and x['source_path'] not in linked],['source_path','filename','sha256','kind']);log('Subtitle lines',len(lines),'failures',len(failures),'anomalies',len(anomalies))
if __name__=='__main__':tracks()
