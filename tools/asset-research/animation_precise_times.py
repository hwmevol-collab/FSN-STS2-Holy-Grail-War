from animation_common import *
from animation_shots import eval_fraction,sheets
import numpy as np

def repair():
    media=readjl(M/'ANIMATION_MEDIA_INDEX.jsonl');chapters=readjl(M/'ANIMATION_CHAPTER_INDEX.jsonl');records=[];allshots=[];repaired=[]
    for r in media:
        cache=T/'shots/v1'/r['media_asset_id']
        if not (cache/'COMPLETE.json').exists():continue
        rows=readjl(cache/'shots.jsonl');original=cache/'shots-detector-display-time.jsonl';originals={s['shot_id']:s for s in readjl(original)} if original.exists() else {s['shot_id']:dict(s) for s in rows};tb=eval_fraction(r['video_time_base']);offset=r['container_start_time'];changed=False;maximum=0;subp=A/'Subtitles/Normalized'/(r['media_asset_id']+'.jsonl');subs=readjl(subp) if subp.exists() else []
        for s in rows:
            start=s['start_pts']*tb-offset;end=s['end_pts']*tb-offset if s['end_pts_status']=='next_source_frame' else r['duration'];rep=s['representative_pts']*tb-offset
            old=originals[s['shot_id']];maximum=max(maximum,abs(start*1000-old['start_ms']),abs(rep*1000-old['representative_ms']))
            if s.get('timecode_basis')!='integer_source_pts':changed=True
            s.update(start_ms=round(start*1000),end_ms=round(end*1000),duration=end-start,start_time=tc(start*1000),end_time=tc(end*1000),representative_ms=round(rep*1000),representative_frame=tc(rep*1000),timecode_basis='integer_source_pts',chapter_id=next((c['chapter_id'] for c in chapters if c['media_asset_id']==r['media_asset_id'] and c['start']<=start<c['end']),''))
            sl=[l for l in subs if l['start_ms']<s['end_ms'] and l['end_ms']>s['start_ms']];counts=(len(sl),sum(len(l['plain_text']) for l in sl),' / '.join(dict.fromkeys(l['plain_text'] for l in sl))[:220])
            if counts!=(s['subtitle_line_count'],s['subtitle_char_count'],s['subtitle_excerpt']):changed=True
            s.update(subtitle_line_count=counts[0],subtitle_char_count=counts[1],subtitle_excerpt=counts[2])
        if changed:
            if not original.exists():shutil.copy2(cache/'shots.jsonl',original)
            jl(cache/'shots.jsonl',rows)
            # Re-render only own contact sheets from existing thumbnails; no video decode.
            for rec in read(cache/'SHEETS.json'):
                p=pathlib.Path(rec['path'])
                assert p.is_relative_to(A/'ContactSheets') or p.is_relative_to(A/'OverviewSheets')
                if rec['type']=='shot_contact_sheet' and p.exists():p.unlink()
            recs=sheets(r,rows);save(cache/'SHEETS.json',recs)
        else:recs=read(cache/'SHEETS.json')
        repaired.append({'media_asset_id':r['media_asset_id'],'maximum_original_display_rounding_ms':maximum,'shots':len(rows),'published_times':'integer source PTS × original stream time_base minus container start','stable_shot_ids_preserved':True,'representative_source_pts_preserved':True});records+=recs;allshots+=rows
    jl(M/'ANIMATION_SHOT_INDEX.jsonl',allshots);csvout(M/'ANIMATION_SHOT_INDEX.csv',allshots);save(M/'ANIMATION_CONTACT_SHEETS.json',records);csvout(M/'ANIMATION_CONTACT_SHEETS.csv',records)
    save(M/'ANIMATION_TIME_PRECISION_POLICY.json',{'created_at':now(),'status':'PASS' if len(repaired)==len(media) else 'in_progress','media_corrected':len(repaired),'media_total':len(media),'detector_revision':'v1','boundary_decisions':'Original pinned scdet scores and display-time spacing decisions preserved. Published boundary/reference times independently reconstructed from exact source PTS.','representative_policy':'Original midpoint-selected source PTS retained, with selection rounding bounded below one source frame for these media. Published timecode is reconstructed from its integer PTS.','end_boundary':'Last shot uses explicitly marked container-duration estimate. Other ends are next source frame PTS.','items':repaired});log('Exact PTS timecodes',len(repaired),'media',len(allshots),'shots')

if __name__=='__main__':repair()
