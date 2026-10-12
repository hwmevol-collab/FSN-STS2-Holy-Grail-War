from fuc_common import *
ROOT=STAGE_ROOT
def run():
    rows=readjson(ROOT/'SOURCE_INVENTORY.json');out=[]
    for r in rows:
        if r['extension']!='.pmf':continue
        h=r['sha256'];dest=ROOT/'Videos'/f'{h}.mp4';dest.parent.mkdir(exist_ok=True)
        item=dict(source_logical_path=r['logical_path'],source_path=r['physical_path'],sha256=h,status='FAILED',working_path='')
        try:
            p=subprocess.run([str(FP),'-v','error','-show_format','-show_streams','-of','json',r['physical_path']],capture_output=True,timeout=60);assert p.returncode==0;original=json.loads(p.stdout)
            if not dest.exists():
                p=subprocess.run([str(FF),'-nostdin','-v','warning','-xerror','-i',r['physical_path'],'-map','0:v:0','-map','0:a?','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-y',str(dest)],capture_output=True,timeout=900)
                (ROOT/'Videos'/f'{h}.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode('utf-8','replace')[-1000:]
            p=subprocess.run([str(FP),'-v','error','-show_format','-show_streams','-of','json',str(dest)],capture_output=True);converted=json.loads(p.stdout)
            p=subprocess.run([str(FF),'-v','error','-xerror','-i',str(dest),'-f','null','-'],capture_output=True,timeout=900);assert p.returncode==0
            video=next(s for s in original['streams'] if s['codec_type']=='video');audio=[s for s in original['streams'] if s['codec_type']=='audio']
            item.update(status='CONVERTED_MP4_FULL_DECODE_VERIFIED',working_path=str(dest),working_sha256=sha(dest),width=video['width'],height=video['height'],fps=video.get('avg_frame_rate'),duration=float(converted['format']['duration']),codec=video['codec_name'],audio_tracks=len(audio),source_streams=original['streams'],working_streams=converted['streams'])
        except Exception as e:item['error']=str(e)
        out.append(item);log('VIDEO',r['logical_path'],item['status'])
    jsonwrite(ROOT/'VIDEO_INDEX.json',out);csvwrite(ROOT/'VIDEO_INDEX.csv',out);jsonwrite(ROOT/'VIDEO_SUMMARY.json',dict(files=len(out),converted=sum(r['status'].startswith('CONVERTED') for r in out),failed=sum(r['status']=='FAILED' for r in out)))
if __name__=='__main__':run()
