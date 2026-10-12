from animation_common import *
from animation_shots import eval_fraction,sheets
import numpy as np

def overviews():
    records=[];all_sheets=[]
    for r in readjl(M/'ANIMATION_MEDIA_INDEX.jsonl'):
        aid=r['media_asset_id'];cache=T/'shots/v1'/aid
        if not (cache/'COMPLETE.json').exists():continue
        folder=T/'thumbnail-staging'/aid;meta=folder/'OVERVIEW_PROVENANCE.json';tb=eval_fraction(r['video_time_base']);offset=r['container_start_time']
        if meta.exists():samples=read(meta)
        else:
            points=np.load(cache/'metrics.npz')['frames'];times=points[:,0]*tb-offset;samples=[];dest=T/'overview-frames'/aid;dest.mkdir(parents=True,exist_ok=True)
            for i,t in enumerate(np.linspace(.02,max(.02,r['duration']-.15),12)):
                ix=min(len(points)-1,int(np.searchsorted(times,t)));pts=int(points[ix,0]);exact=pts*tb-offset;p=dest/f'{i:02d}.jpg';tmp=dest/f'{i:02d}-exact.jpg';lp=dest/f'{i:02d}-exact.log'
                args=[FF,'-nostdin','-v','info','-threads','2','-copyts','-ss',str(max(0,exact-.00001)),'-i',r['source_path'],'-map','0:v:0','-frames:v','1','-vf','showinfo,scale=640:-2','-q:v','4','-y',tmp];process=subprocess.run([str(x) for x in args],capture_output=True,encoding='utf-8',errors='replace',creationflags=0x08000000,timeout=180);lp.write_text(process.stderr,encoding='utf-8');actual=re.search(r'n:\s*0\s+pts:\s*(-?\d+)',process.stderr);assert process.returncode==0 and actual and int(actual[1])==pts,'Overview exact source-frame mismatch '+aid;os.replace(tmp,p);samples.append({'media_asset_id':aid,'sample_index':i,'requested_ms':round(t*1000),'source_pts':pts,'source_sha256':r['sha256']})
            save(meta,samples)
        for s in samples:s.update(actual_ms=round((s['source_pts']*tb-offset)*1000),timecode=tc((s['source_pts']*tb-offset)*1000),pts_time_base=r['video_time_base'],derived_from_media_asset_id=aid,reference_type='uniform_overview_source_frame')
        save(meta,samples)
        label_marker=folder/'EXACT_OVERVIEW_LABELS.json'
        if not label_marker.exists():
            old=A/'OverviewSheets'/(aid+'.jpg');assert old.is_relative_to(A/'OverviewSheets')
            if old.exists():old.unlink()
            save(cache/'SHEETS.json',sheets(r,readjl(cache/'shots.jsonl')));save(label_marker,{'source_sha256':r['sha256'],'exact_source_pts':True})
        records.extend(samples);all_sheets+=read(cache/'SHEETS.json')
    csvout(M/'ANIMATION_OVERVIEW_FRAME_INDEX.csv',records);jl(M/'ANIMATION_OVERVIEW_FRAME_INDEX.jsonl',records);save(M/'ANIMATION_CONTACT_SHEETS.json',all_sheets);csvout(M/'ANIMATION_CONTACT_SHEETS.csv',all_sheets);save(M/'ANIMATION_OVERVIEW_VALIDATION.json',{'created_at':now(),'source_samples':len(records),'media_count':len(set(s['media_asset_id'] for s in records)),'exact_source_pts':True});log('Overview exact source provenance',len(records))

if __name__=='__main__':overviews()
