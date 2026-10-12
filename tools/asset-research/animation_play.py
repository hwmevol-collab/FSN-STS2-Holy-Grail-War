from animation_common import *
import argparse
def resolve(media_id=None,shot_id=None,seconds=None):
    db=sqlite3.connect('file:'+str(M/'ANIMATION_REFERENCE.sqlite')+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    if shot_id:
        shot=db.execute('SELECT * FROM shots WHERE shot_id=?',(shot_id,)).fetchone()
        if shot is None:raise ValueError('Unknown shot ID')
        media_id=shot['media_asset_id'];seconds=shot['start_ms']/1000
    if media_id is None:raise ValueError('Specify media_asset_id or shot_id')
    r=db.execute('SELECT * FROM media WHERE media_asset_id=?',(media_id,)).fetchone();db.close()
    if r is None:raise ValueError('Unknown media ID')
    r=dict(r);seconds=float(seconds or 0);assert 0<=seconds<r['duration'];p=pathlib.Path(r['source_path']);assert p.is_relative_to(S) and p.exists();st=p.stat();assert st.st_size==r['size'] and st.st_mtime_ns==r['mtime_ns'],'Source stat changed; verify before playback';return r,seconds
def launch(media_id=None,shot_id=None,seconds=None,duration=None,mute=False,clock=False):
    r,seconds=resolve(media_id,shot_id,seconds);args=[PLAY,'-hide_banner','-loglevel','info','-ss',f'{seconds:.6f}','-window_title',f'FSN Animation QA / {r["media_asset_id"]} / {tc(seconds*1000)}','-x','960','-y','540']
    if duration:args+=['-t',str(duration),'-autoexit']
    if mute:args+=['-an']
    seek_filter=f"select='gte(t,{seconds+r['container_start_time']:.9f})'"
    if clock:seek_filter+=",showinfo,scale=960:-2,drawtext=fontfile='C\\:/Windows/Fonts/consola.ttf':text='%{pts\\:hms}':x=15:y=15:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.7"
    args+=['-vf',seek_filter]
    args+=[r['source_path']];ld=T/'playback-logs';ld.mkdir(exist_ok=True);lp=ld/(r['media_asset_id']+'-'+str(round(seconds*1000))+'-'+('qa' if clock else 'play')+'-'+str(time.time_ns())+'.log');f=lp.open('w',encoding='utf-8');p=subprocess.Popen([str(x) for x in args],stdout=f,stderr=f,creationflags=0x08000000);f.close();result={'pid':p.pid,'media_asset_id':r['media_asset_id'],'shot_id':shot_id,'seek_seconds':seconds,'requested_timecode':tc(seconds*1000),'source_path':r['source_path'],'command':[str(x) for x in args],'log':str(lp),'created_at':now()};save(T/'LAST_PLAYBACK.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--media');p.add_argument('--shot');p.add_argument('--seconds',type=float);p.add_argument('--duration',type=float);p.add_argument('--mute',action='store_true');p.add_argument('--clock',action='store_true');p.add_argument('--resolve',action='store_true');a=p.parse_args()
    print(json.dumps(resolve(a.media,a.shot,a.seconds) if a.resolve else launch(a.media,a.shot,a.seconds,a.duration,a.mute,a.clock),ensure_ascii=False))
