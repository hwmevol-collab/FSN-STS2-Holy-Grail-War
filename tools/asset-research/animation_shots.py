from animation_common import *
import numpy as np, bisect, math, concurrent.futures
from PIL import Image,ImageDraw,ImageFont
REV='v1'; SETTINGS={'detector':'FFmpeg scdet','version':command([FF,'-version']).splitlines()[0],'threshold':8.0,'min_scene_len_seconds':0.167,'analysis_width':256,'analysis_format':'yuv420p','frame_skip':0,'motion_metric':'mean low-resolution consecutive-frame luma absolute difference (lavfi.scd.mafd), excluding first boundary frame','worker_count':1,'decoder_threads':2,'shot_index_revision':REV,'sources':'https://ffmpeg.org/ffmpeg-filters.html#scdet'}
FONT=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14); SMALL=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
def gpu(r):return r['video_codec'] in {'hevc','h264','vp9','av1'} and r['pixel_format'] in {'yuv420p','yuv420p10le'} and (r['video_codec']!='h264' or r['pixel_format']=='yuv420p') and r['video_codec']!='av1'
def input_args(r,seek=None,hardware=False):
    args=[FF,'-nostdin','-hide_banner','-v','warning','-threads','2','-copyts']
    if hardware:args+=['-hwaccel','cuda','-hwaccel_output_format','cuda']
    if seek is not None:args+=['-ss',str(seek)]
    return args+['-i',r['source_path'],'-map','0:v:0','-an','-sn','-dn']
def detect(r,seek=None,length=None):
    for hardware in ([True,False] if gpu(r) else [False]):
        filt=('scale_cuda=256:-2,hwdownload,format='+('p010le' if r['pixel_format']=='yuv420p10le' else 'nv12')+',format=yuv420p' if hardware else 'scale=256:-2,format=yuv420p')+',scdet=threshold=6,metadata=print:file=-'
        args=input_args(r,seek,hardware)
        # With copyts, -t is output duration relative to source start; use -to for sampled windows.
        if length is not None:args+=['-to',str((seek or 0)+length+r['container_start_time'])]
        args+=['-filter_threads','2','-vf',filt,'-fps_mode','passthrough','-f','null','-']
        err=T/'logs'/f"{r['media_asset_id']}-detect{'-probe' if seek is not None else ''}.log";err.parent.mkdir(exist_ok=True)
        points=[];current=None;start=time.monotonic()
        with err.open('w',encoding='utf-8') as ef:
            p=subprocess.Popen([str(x) for x in args],stdout=subprocess.PIPE,stderr=ef,encoding='utf-8',errors='replace',bufsize=1024*1024,creationflags=0x08000000)
            for line in p.stdout:
                if line.startswith('frame:'):
                    if current is not None:points.append(current)
                    m=re.search(r'pts:\s*(-?\d+)\s+pts_time:([\d.eE+-]+)',line);current=[int(m[1]),float(m[2]),0.,0.] if m else None
                elif current is not None and line.startswith('lavfi.scd.mafd='):current[2]=float(line.split('=')[1])
                elif current is not None and line.startswith('lavfi.scd.score='):current[3]=float(line.split('=')[1])
            if current is not None:points.append(current)
            p.wait()
        if p.returncode==0 and points:return np.array(points,dtype=np.float64),{'hardware':hardware,'command':[str(x) for x in args],'elapsed_seconds':time.monotonic()-start,'decoder_log':str(err)}
        log('Decoder retry',r['media_asset_id'],'GPU' if hardware else 'CPU',p.returncode,err.read_text(encoding='utf-8')[-300:])
    raise RuntimeError('Scene decoding failed: '+str(err))
def boundaries(points,threshold=8,minlen=.167):
    cuts=[0]
    for i in np.flatnonzero(points[:,3]>=threshold):
        if points[i,1]-points[cuts[-1],1]>=minlen:cuts.append(int(i))
    return cuts
def frame(r,seconds,dest,width=512):
    dest=pathlib.Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():command([FF,'-nostdin','-v','error','-threads','2','-ss',str(seconds),'-i',r['source_path'],'-map','0:v:0','-frames:v','1','-vf',f'scale={width}:-2','-q:v','4',dest],timeout=240)
    return dest
def probe():
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');selected=[]
    for work in ['FSN2006_TV','UBW_TV','HF_MOVIE','FATE_ZERO','EMIYA_GOHAN','CARNIVAL_PHANTASM','REALTA_NUA_OP']:
        rs=[r for r in media if r['work_id']==work and not r['special_label']];selected.append(rs[0] if rs else next(r for r in media if r['work_id']==work))
    report=[]
    for r in selected:
        parts=[]
        for pos in sorted(set([0,round(r['duration']/2),max(0,round(r['duration']-60))])):
            length=min(60,r['duration']-pos);points,meta=detect(r,pos,length);entry={'media_asset_id':r['media_asset_id'],'work_id':r['work_id'],'source_start':pos,'length':length,'frames':len(points),'thresholds':{str(th):{'cut_count':len(boundaries(points,th))-1,'short_shots_under_half_second':int(sum(points[b,1]-points[a,1]<.5 for a,b in zip(boundaries(points,th),boundaries(points,th)[1:])))} for th in [6,8,10,12]},'settings':meta};report.append(entry)
            cs=boundaries(points,8)
            for a,b in list(zip(cs,cs[1:]+[len(points)]))[:8]:
                t=points[(a+b)//2,1]-r['container_start_time'];dest=frame(r,max(0,t),T/'probe-frames'/f"{r['media_asset_id']}-{pos}-{a}.jpg",320);parts.append((dest,t,b-a))
        sheet=Image.new('RGB',(4*336,math.ceil(len(parts)/4)*220),'#0c1725');dr=ImageDraw.Draw(sheet)
        for j,(p,t,n) in enumerate(parts):
            im=Image.open(p);im.thumbnail((320,180));x=j%4*336+8;y=j//4*220+8;sheet.paste(im,(x,y));dr.text((x,y+182),tc(t*1000)+f'  frames {n}',font=FONT,fill='white')
        dest=T/'probe-frames'/(r['work_id']+'-probe.jpg');sheet.save(dest,quality=85);log('Probe',r['work_id'],str(dest))
    save(M/'ANIMATION_DETECTOR_PROBE.json',{'samples':report,'candidate_settings':SETTINGS,'status':'awaiting_visual_review'});save(M/'ANIMATION_DETECTOR_SETTINGS.json',SETTINGS)
def pts_selector(targets):
    if len(targets)==1:return f'eq(pts,{targets[0]})'
    split=len(targets)//2
    return f'if(lt(pts,{targets[split]}),{pts_selector(targets[:split])},{pts_selector(targets[split:])})'
def thumbs(r,shots,points):
    folder=A/'Thumbnails'/REV/r['media_asset_id'];folder.mkdir(parents=True,exist_ok=True)
    overview_dir=T/'overview-frames'/r['media_asset_id'];overview_dir.mkdir(parents=True,exist_ok=True)
    if all(pathlib.Path(s['thumbnail']).exists() for s in shots) and len(list(overview_dir.glob('*.jpg')))==12:return
    times=np.linspace(.02,max(.02,r['duration']-.15),12);ovs=[]
    for i,t in enumerate(times):
        idx=min(len(points)-1,int(np.searchsorted(points[:,1],t+r['container_start_time'])));ovs.append({'media_asset_id':r['media_asset_id'],'sample_index':i,'requested_ms':round(t*1000),'actual_ms':round((points[idx,1]-r['container_start_time'])*1000),'source_pts':int(points[idx,0]),'source_sha256':r['sha256']})
    targets=sorted(set(s['representative_pts'] for s in shots)|{o['source_pts'] for o in ovs})
    staging=T/'thumbnail-staging'/r['media_asset_id'];staging.mkdir(parents=True,exist_ok=True);script=staging/'select.txt';expr=pts_selector(targets)
    for hardware in ([True,False] if gpu(r) else [False]):
        filt="select='"+expr+"',"+('scale_cuda=640:-2:format=nv12,hwdownload,format=nv12' if hardware else 'scale=640:-2')
        script.write_text(filt,encoding='utf-8');args=input_args(r,hardware=hardware)+['-y','-filter_threads','2','-filter_script:v',str(script),'-fps_mode','vfr','-q:v','4',str(staging/'frame-%06d.jpg')]
        err=T/'logs'/(r['media_asset_id']+'-thumbnails.log')
        with err.open('w',encoding='utf-8') as ef:p=subprocess.run([str(x) for x in args],stdout=subprocess.DEVNULL,stderr=ef,creationflags=0x08000000)
        found=sorted(staging.glob('frame-*.jpg'))
        if p.returncode==0 and len(found)==len(targets):
            pm=dict(zip(targets,found))
            for o in ovs:shutil.copy2(pm[o['source_pts']],overview_dir/f"{o['sample_index']:02d}.jpg")
            save(staging/'OVERVIEW_PROVENANCE.json',ovs)
            for s in shots:
                p=pm[s['representative_pts']]
                dest=pathlib.Path(s['thumbnail']);im=Image.open(p);im.save(dest,'WEBP',quality=78,method=4);p.unlink()
            for p in found:
                if p.exists():p.unlink()
            save(staging/'EXTRACTION.json',{'source_sha256':r['sha256'],'revision':REV,'command':[str(x) for x in args],'frames':len(found),'pts_exact':True});return
        # Own staging images only. Source path is never an output target.
        for p in found:p.unlink()
        log('Thumbnail retry',r['media_asset_id'],len(found),'expected',len(shots))
    raise RuntimeError('Representative frame extraction mismatch '+r['media_asset_id'])
def sheets(r,shots):
    records=[];folder=A/'ContactSheets'/REV/r['media_asset_id'];folder.mkdir(parents=True,exist_ok=True)
    for page in range(math.ceil(len(shots)/24)):
        group=shots[page*24:(page+1)*24];dest=folder/f'page-{page+1:04d}.jpg'
        if not dest.exists():
            im=Image.new('RGB',(4*336,math.ceil(len(group)/4)*244+40),'#101c2c');dr=ImageDraw.Draw(im);dr.text((10,10),r['media_asset_id']+' / '+r['work_id']+f' / page {page+1}',font=FONT,fill='white')
            for i,s in enumerate(group):
                thumb=Image.open(s['thumbnail']);thumb.thumbnail((320,180));x=i%4*336+8;y=i//4*244+40;im.paste(thumb,(x,y));dr.text((x,y+181),s['shot_id'],font=FONT,fill='#e5edf7');dr.text((x,y+199),s['start_time']+f"  {s['duration']:.3f}s",font=FONT,fill='#d5b767');dr.text((x,y+217),s.get('subtitle_excerpt','').replace('\n',' ')[:23],font=SMALL,fill='#cbd5e1')
            im.save(dest,quality=83)
        records.append({'media_asset_id':r['media_asset_id'],'type':'shot_contact_sheet','page':page+1,'shot_count':len(group),'path':str(dest),'first_shot_id':group[0]['shot_id'],'last_shot_id':group[-1]['shot_id']})
    overview=A/'OverviewSheets'/(r['media_asset_id']+'.jpg');overview.parent.mkdir(parents=True,exist_ok=True)
    if not overview.exists():
        im=Image.new('RGB',(4*336,3*220+40),'#101c2c');dr=ImageDraw.Draw(im);dr.text((10,10),r['media_asset_id']+' / uniform overview',font=FONT,fill='white')
        times=np.linspace(.02,max(.02,r['duration']-.15),12);op=T/'thumbnail-staging'/r['media_asset_id']/'OVERVIEW_PROVENANCE.json';ov=read(op) if op.exists() else []
        for i,t in enumerate(times):
            p=frame(r,float(t),T/'overview-frames'/r['media_asset_id']/f'{i:02d}.jpg',320);th=Image.open(p);th.thumbnail((320,180));x=i%4*336+8;y=i//4*220+40;im.paste(th,(x,y));label=(ov[i]['source_pts']*eval_fraction(r['video_time_base'])-r['container_start_time'])*1000 if ov else t*1000;dr.text((x,y+182),tc(label),font=FONT,fill='white')
        im.save(overview,quality=83)
    records.append({'media_asset_id':r['media_asset_id'],'type':'uniform_overview','page':1,'shot_count':12,'path':str(overview),'first_shot_id':'','last_shot_id':''});return records
def process(r):
    asset=r['media_asset_id'];cache=T/'shots'/REV/asset;cache.mkdir(parents=True,exist_ok=True);marker=cache/'COMPLETE.json'
    if marker.exists():
        m=read(marker);assert m['sha256']==r['sha256'] and {k:v for k,v in m['settings'].items() if k!='worker_count'}=={k:v for k,v in SETTINGS.items() if k!='worker_count'}
        return m
    points_path=cache/'metrics.npz'
    if points_path.exists():points=np.load(points_path)['frames'];meta=read(cache/'DECODE.json')
    else:points,meta=detect(r);np.savez_compressed(points_path,frames=points);save(cache/'DECODE.json',meta)
    assert len(points)>0 and np.all(np.diff(points[:,1])>0),'Broken or duplicate video PTS'
    cuts=boundaries(points,SETTINGS['threshold'],SETTINGS['min_scene_len_seconds']);shots=[];offset=r['container_start_time'];duration=r['duration'];subp=A/'Subtitles/Normalized'/(asset+'.jsonl');subtitles=readjl(subp) if subp.exists() else [];chapters=[c for c in readjl(M/'ANIMATION_CHAPTER_INDEX.jsonl') if c['media_asset_id']==asset]
    for a,b in zip(cuts,cuts[1:]+[len(points)]):
        start=float(points[a,1]-offset);end=float(points[b,1]-offset) if b<len(points) else duration;mid=(start+end)/2;idx=min(b-1,max(a,int(np.searchsorted(points[:,1],mid+offset))));pt=int(points[a,0]);rep=int(points[idx,0]);shotid=f'ANI-{asset}-{REV.upper()}-P{pt:012d}';ss=round(start*1000);ee=round(end*1000);sl=[x for x in subtitles if x['start_ms']<ee and x['end_ms']>ss];ch=next((c['chapter_id'] for c in chapters if c['start']<=start<c['end']),'');motion=float(np.mean(points[a+1:b,2])) if b-a>1 else 0
        shots.append({'shot_id':shotid,'media_asset_id':asset,'work_id':r['work_id'],'start_time':tc(ss),'end_time':tc(ee),'start_ms':ss,'end_ms':ee,'duration':end-start,'start_pts':pt,'end_pts':int(points[b,0]) if b<len(points) else round((duration+offset)*float(eval_fraction(r['video_time_base'],invert=True))),'pts_time_base':r['video_time_base'],'end_pts_status':'next_source_frame' if b<len(points) else 'container_duration_boundary_estimate','detector':SETTINGS['detector'],'detector_revision':REV,'cut_score':float(points[a,3]),'representative_frame':tc((points[idx,1]-offset)*1000),'representative_ms':round((points[idx,1]-offset)*1000),'representative_pts':rep,'thumbnail':str(A/'Thumbnails'/REV/asset/(shotid+'.webp')),'motion_score':round(motion,6),'visual_motion_score':round(motion,6),'subtitle_line_count':len(sl),'subtitle_char_count':sum(len(x['plain_text']) for x in sl),'subtitle_excerpt':' / '.join(dict.fromkeys(x['plain_text'] for x in sl))[:220],'chapter_id':ch,'auto_sequence_id':'','semantic_status':'unreviewed','characters_mentioned':[],'characters_present_confirmed':[],'characters_present_candidate':[],'actions_confirmed':[],'derived_from_media_asset_id':asset,'source_sha256':r['sha256'],'notes':'automatic shot boundary; no semantic scene assertion'})
    jl(cache/'shots.jsonl',shots);thumbs(r,shots,points);records=sheets(r,shots);save(cache/'SHEETS.json',records);result={'media_asset_id':asset,'sha256':r['sha256'],'settings':SETTINGS,'shots':len(shots),'frames_decoded':len(points),'first_pts':int(points[0,0]),'last_pts':int(points[-1,0]),'duration':duration,'completed_at':now(),'status':'success'};save(marker,result);log('Shots complete',asset,r['work_id'],len(shots),'frames',len(points),'decode seconds',round(meta['elapsed_seconds'],1));return result
def eval_fraction(s,invert=False):
    a,b=map(float,s.split('/'));return b/a if invert else a/b
def all_shots():
    probe_evidence=read(M/'ANIMATION_DETECTOR_PROBE.json');assert probe_evidence['status']=='visually_reviewed','Probe must be reviewed first'
    assert {k:v for k,v in probe_evidence['candidate_settings'].items() if k!='worker_count'}=={k:v for k,v in SETTINGS.items() if k!='worker_count'},'Detector changed; preserve v1 and create an explicitly reviewed new revision'
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');statuses=[];SETTINGS['worker_count']=4;save(M/'ANIMATION_DETECTOR_SETTINGS.json',SETTINGS)
    def run_item(pair):
        i,r=pair;log('Processing',i+1,'/',len(media),r['media_asset_id'],r['filename'])
        try:return process(r)
        except Exception as e:
            result={'media_asset_id':r['media_asset_id'],'status':'failed','error':str(e),'sha256':r['sha256']};log('SHOTS FAILED',result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures=[executor.submit(run_item,pair) for pair in enumerate(media)]
        for future in concurrent.futures.as_completed(futures):
            statuses.append(future.result());save(M/'ANIMATION_STAGE_STATUS.json',{'completed':len(statuses),'total':len(media),'worker_count':4,'status':sorted(statuses,key=lambda x:x['media_asset_id']),'updated_at':now()})
    shots=[];records=[]
    for r in media:
        cache=T/'shots'/REV/r['media_asset_id']
        if (cache/'COMPLETE.json').exists():shots+=readjl(cache/'shots.jsonl');records+=read(cache/'SHEETS.json')
    jl(M/'ANIMATION_SHOT_INDEX.jsonl',shots);csvout(M/'ANIMATION_SHOT_INDEX.csv',shots);csvout(M/'ANIMATION_CONTACT_SHEETS.csv',records);save(M/'ANIMATION_CONTACT_SHEETS.json',records);log('All shots',len(shots))
if __name__=='__main__':{'Probe':probe,'Shots':all_shots}[sys.argv[1] if len(sys.argv)>1 else 'Probe']()
