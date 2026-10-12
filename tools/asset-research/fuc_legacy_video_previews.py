"""Add browser-only MP4 previews; never modify any legacy catalog or raw video."""
from fuc_common import *
import concurrent.futures
def convert(item):
    path,ids=item;src=pathlib.Path(path);h=sha(src);dst=L/'Gallery/video_previews'/(h+'.mp4');dst.parent.mkdir(exist_ok=True)
    probe=subprocess.run([str(FP),'-v','error','-show_streams','-of','json',str(dst)],capture_output=True) if dst.exists() else None
    valid=probe is not None and probe.returncode==0 and any(s.get('codec_type')=='video' for s in json.loads(probe.stdout).get('streams',[]))
    if not valid:
        temp=FW/'Europe/LegacyPreviewTranscode'/(h+'.mp4');temp.parent.mkdir(parents=True,exist_ok=True)
        p=subprocess.run([str(FF),'-nostdin','-v','error','-xerror','-i',str(src),'-map','0:v:0','-map','0:a?', '-vf',r'scale=w=trunc(min(1280\,iw)/2)*2:h=-2','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-y',str(temp)],capture_output=True,timeout=1800);assert p.returncode==0,p.stderr.decode(errors='replace')
        os.replace(temp,dst)
    p=subprocess.run([str(FF),'-v','error','-xerror','-i',str(dst),'-f','null','-'],capture_output=True,timeout=1800);assert p.returncode==0;assert sha(src)==h
    return dict(source_path=str(src),source_sha256=h,asset_ids=ids,preview_path=str(dst),preview_sha256=sha(dst),status='MP4_PREVIEW_FULL_DECODE_VALIDATED_PRESERVATION_UNCHANGED')
def run():
    db=sqlite3.connect(f'file:{(BACK/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True);groups=collections.defaultdict(list)
    for aid,p in db.execute("SELECT asset_id,converted_path FROM assets WHERE lower(converted_path) LIKE '%.ogv'"):groups[p].append(aid)
    db.close();out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(convert,groups.items()):out.append(result);log('LEGACY MP4 PREVIEW',len(out),'/',len(groups))
    previews={aid:pathlib.Path(x['preview_path']).relative_to(L).as_posix() for x in out for aid in x['asset_ids']};(L/'Gallery/preview_map.js').write_text('window.FSN_PREVIEWS='+json.dumps(previews,separators=(',',':'))+';',encoding='utf-8');jsonwrite(L/'Reports/FUC_LEGACY_VIDEO_PREVIEWS.json',out)
if __name__=='__main__':run()
