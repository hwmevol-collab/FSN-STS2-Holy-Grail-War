"""Independent media header/first-frame checks of existing Gallery representatives."""
from fuc_battle_common import *
def main():
 c=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;rows=[]
 for aid in ['FSN042450','FSN042476','FSN215096','FSN255896']:
  r=dict(c.execute('select * from assets where asset_id=?',(aid,)).fetchone());p=pathlib.Path((r['converted_path'] or r['extracted_path']).replace('\\\\','\\'));args=[str(FP),'-v','error','-show_entries','format=duration:stream=codec_name,codec_type,width,height,sample_rate,channels','-of','json',str(p)];pr=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE);dm=subprocess.run([str(FF),'-v','error','-i',str(p),'-frames:v','1','-f','null','NUL'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);rows.append(dict(asset_id=aid,path=str(p),exists=p.is_file(),ffprobe_exit=pr.returncode,first_frame_decode_exit=dm.returncode,metadata=json.loads(pr.stdout) if not pr.returncode else {},error=dm.stderr.decode('utf-8','replace'),scope='one decoded video frame; not whole-video or Chrome playback'))
 c.close();jsonwrite(BR/'GALLERY_MEDIA_CHECKS.json',rows);print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
