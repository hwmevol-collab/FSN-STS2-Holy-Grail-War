from animation_common import *
from animation_shots import eval_fraction
from animation_index import phash
from PIL import Image, ImageDraw, ImageFont
import math, numpy as np
MAJOR=['FSN2006_TV','UBW_TV','UBW_2010_MOVIE','HF_MOVIE','FATE_ZERO','EMIYA_GOHAN','CARNIVAL_PHANTASM']
def qa():
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');shots=readjl(M/'ANIMATION_SHOT_INDEX.jsonl');by=collections.defaultdict(list)
    for s in shots:by[s['media_asset_id']].append(s)
    samples=[];decodes=[];previews=[];qadir=A/'Reports/QA';qadir.mkdir(parents=True,exist_ok=True);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14);cf=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    for work in dict.fromkeys(r['work_id'] for r in media):
        rs=[r for r in media if r['work_id']==work and by[r['media_asset_id']]];main=[r for r in rs if not r['special_label']] or rs
        selected=([main[0],main[-1]] if len(main)>1 else main[:1]);selection=[]
        for r in selected:
            ss=by[r['media_asset_id']]
            for category,t in [('beginning',r['duration']*.03),('middle',r['duration']*.5),('ending',r['duration']*.97)]:selection.append((r,min(ss,key=lambda s:abs(s['representative_ms']/1000-t)),category))
        if work in MAJOR and main:
            r=main[0];ss=by[r['media_asset_id']]
            dialogue=[s for s in ss if s['subtitle_char_count']>0 and r['duration']*.1<=s['representative_ms']/1000<=r['duration']*.9]
            for category,group,key in [('dialogue',dialogue,lambda s:s['duration']),('dense_subtitles',[s for s in ss if s['subtitle_char_count']>0],lambda s:s['subtitle_char_count']/max(s['duration'],.001)),('high_motion',ss,lambda s:s['motion_score']),('no_text_subtitles',[s for s in ss if s['subtitle_char_count']==0],lambda s:s['duration'])]:
                if category=='dialogue' and work=='UBW_2010_MOVIE':
                    # Visually reviewed ordinary spoken dialogue; automatic longest text shot was an incantation over black.
                    chosen=next(s for s in ss if s['shot_id']=='ANI-FSN270524-V1-P000003169166')
                    selection.append((r,chosen,category))
                elif group:selection.append((r,max(group,key=key),category))
                else:samples.append({'work_id':work,'category':category,'status':'not_applicable','reason':'No local text subtitles / no such source sample; no semantic claim'})
        extra_file=M/'ANIMATION_MANUAL_EXTRA_QA_SHOTS.json'
        if extra_file.exists():
            for e in read(extra_file):
                if e['work_id']!=work:continue
                s=next(s for s in shots if s['shot_id']==e['shot_id']);r=next(r for r in media if r['media_asset_id']==s['media_asset_id']);selection.append((r,s,e['category']))
        montage=[]
        for r,s,category in selection:
            exact=s['representative_pts']*eval_fraction(s['pts_time_base'])-r['container_start_time'];dest=qadir/(s['shot_id']+'-source.jpg');lp=qadir/(s['shot_id']+'-decode.log');record={'work_id':work,'media_asset_id':r['media_asset_id'],'shot_id':s['shot_id'],'category':category,'requested_seconds':exact,'expected_pts':s['representative_pts'],'source_sha256':r['sha256'],'thumbnail':s['thumbnail'],'source_frame':str(dest),'subtitle_excerpt':s['subtitle_excerpt']}
            try:
                if not dest.exists():
                    args=[FF,'-nostdin','-v','info','-threads','2','-copyts','-ss',str(max(0,exact-.00001)),'-i',r['source_path'],'-map','0:v:0','-frames:v','1','-vf','showinfo,scale=640:-2','-q:v','4',str(dest)];p=subprocess.run([str(x) for x in args],capture_output=True,encoding='utf-8',errors='replace',creationflags=0x08000000,timeout=180);lp.write_text(p.stderr,encoding='utf-8');assert p.returncode==0,p.stderr[-1500:]
                text=lp.read_text(encoding='utf-8');match=re.search(r' n:\s*0\s+pts:\s*(-?\d+)\s+pts_time:([\d.eE+-]+)',text);assert match,'No decoded source PTS';actual=int(match[1]);a,sa=phash(s['thumbnail']);b,sb=phash(dest);dist=(a^b).bit_count();ai=np.asarray(Image.open(s['thumbnail']).convert('RGB').resize((320,180)),dtype=float);bi=np.asarray(Image.open(dest).convert('RGB').resize((320,180)),dtype=float);mae=float(np.mean(np.abs(ai-bi)));flat_match=max(sa,sb)<2 and mae<3;record.update(actual_pts=actual,pts_error=actual-s['representative_pts'],seek_error_seconds=abs(actual*eval_fraction(s['pts_time_base'])-r['container_start_time']-exact),pts_time_log_rounding_seconds=abs(float(match[2])-actual*eval_fraction(s['pts_time_base'])),phash_distance=dist,pixel_mae=mae,flat_luma_exception=flat_match,status='success' if actual==s['representative_pts'] and (dist<=8 or flat_match) else 'review_required');montage.append((r,s,category,dest,record));samples.append(record)
            except Exception as e:record.update(status='failed',error=str(e));samples.append(record)
        if montage:
            sheet=Image.new('RGB',(2*680,math.ceil(len(montage)/2)*270+35),'#101c2c');draw=ImageDraw.Draw(sheet);draw.text((10,10),work+' / thumbnail left + independently decoded source right',font=font,fill='white')
            for i,(r,s,cat,dest,record) in enumerate(montage):
                x=i%2*680+8;y=i//2*270+35
                for j,p in enumerate([s['thumbnail'],dest]):im=Image.open(p);im.thumbnail((324,184));sheet.paste(im,(x+j*332,y))
                draw.text((x,y+185),s['shot_id']+' / '+cat,font=font,fill='#e2c477');draw.text((x,y+204),s['representative_frame']+f" PTS delta {record['pts_error']} pHash {record['phash_distance']}",font=font,fill='white');draw.text((x,y+226),s['subtitle_excerpt'].replace('\n',' ')[:39],font=cf,fill='#d5e0ef')
            sheet.save(qadir/(work+'-QA.jpg'),quality=85)
        if main:
            r=main[0]
            for t in [0,r['duration']/2,max(0,r['duration']-3)]:
                try:command([FF,'-nostdin','-v','error','-threads','2','-ss',str(t),'-i',r['source_path'],'-t','2','-map','0:v:0','-an','-sn','-f','null','-']);decodes.append({'work_id':work,'media_asset_id':r['media_asset_id'],'start':t,'length':2,'status':'success'})
                except Exception as e:decodes.append({'work_id':work,'media_asset_id':r['media_asset_id'],'start':t,'status':'failed','error':str(e)})
    # Small acceptance-only previews, never a second full-video library.
    for work in ['FSN2006_TV','UBW_TV','HF_MOVIE','FATE_ZERO','CARNIVAL_PHANTASM','REALTA_NUA_OP']:
        r=next((r for r in media if r['work_id']==work and by[r['media_asset_id']] and not r['special_label']),None)
        if not r:continue
        ss=by[r['media_asset_id']];s=min(ss,key=lambda x:abs(x['representative_ms']/1000-r['duration']/2));start=s['start_ms']/1000;length=min(4,r['duration']-start);dest=A/'Previews'/(r['media_asset_id']+'-QA.mp4');dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():command([FF,'-nostdin','-v','error','-threads','2','-ss',str(start),'-i',r['source_path'],'-t',str(length),'-map','0:v:0','-map','0:a:0?','-vf','scale=640:-2','-c:v','libx264','-preset','veryfast','-crf','25','-c:a','aac','-ac','2','-b:a','96k','-movflags','+faststart',dest],timeout=240)
        previews.append({'preview_id':r['media_asset_id']+'-QA','media_asset_id':r['media_asset_id'],'start':start,'end':start+length,'source_sha256':r['sha256'],'path':str(dest),'purpose':'short acceptance sample only','derived_from_media_asset_id':r['media_asset_id']})
    csvout(M/'ANIMATION_QA_SAMPLES.csv',samples);save(M/'ANIMATION_QA_SAMPLES.json',samples);save(M/'ANIMATION_DECODE_QA.json',decodes);csvout(M/'ANIMATION_PREVIEWS.csv',previews);save(M/'ANIMATION_PREVIEWS.json',previews);save(M/'ANIMATION_MANUAL_QA.json',{'status':'awaiting_visual_review','samples':len(samples),'source_frame_comparisons':sum(r['status']=='success' for r in samples),'review_required':[r for r in samples if r['status'] in ['review_required','failed']],'decode_samples':len(decodes),'decode_failed':[r for r in decodes if r['status']!='success'],'montage_directory':str(qadir),'major_works':MAJOR,'scope':'Source/time/thumbnail/text correspondence samples; high motion is not confirmed battle.'});log('QA samples',len(samples))
if __name__=='__main__':qa()
