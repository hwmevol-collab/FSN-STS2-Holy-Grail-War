from common import *
import urllib.request,zipfile,time,subprocess
def get(url,path=None):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FSN-Asset-Library'}),timeout=120) as r:
                if path:
                    with open(path,'wb') as f:shutil.copyfileobj(r,f)
                    return
                return json.loads(r.read())
        except Exception as e:
            print(url,attempt,repr(e),flush=True)
            if attempt==4:raise
            time.sleep(2)
manifest=[]
for repo in ['vn-tools/arc_unpacker','kurikomoe/FSNr_tools','DaZombieKiller/FatePackageManager','Jannabie/FSN-Remastered-Decompiler']:
    target=W/'repos'/repo.split('/')[-1]
    info=get('https://api.github.com/repos/'+repo); commit=get('https://api.github.com/repos/'+repo+'/commits/'+info['default_branch'])['sha']
    if not (target/'.git').exists():
        z=W/'tools'/(target.name+'-source.zip');get('https://codeload.github.com/'+repo+'/zip/'+commit,z)
        with zipfile.ZipFile(z) as f:
            prefix=f.namelist()[0].split('/')[0]+'/'
            for item in f.infolist():
                rel=item.filename[len(prefix):]
                if not rel:continue
                out=target/rel
                if item.is_dir():out.mkdir(parents=True,exist_ok=True)
                else:out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(f.read(item))
    else:commit=subprocess.check_output(['git','-C',str(target),'rev-parse','HEAD'],text=True).strip()
    manifest.append({'repository':'https://github.com/'+repo,'commit':commit,'archived':info['archived'],'path':str(target)})
    print(repo,commit,'archived',info['archived'],flush=True)
jsonwrite(W/'reports/TOOL_SOURCES.json',manifest)
releases=get('https://api.github.com/repos/vn-tools/arc_unpacker/releases')
jsonwrite(W/'reports/ARC_RELEASES.json',releases)
for r in releases[:3]:
    print('RELEASE',r['tag_name'],[(a['name'],a['browser_download_url']) for a in r['assets']],flush=True)
    if r['assets']:
        a=next((a for a in r['assets'] if 'win' in a['name'].lower()),r['assets'][0]);p=W/'tools'/a['name'];get(a['browser_download_url'],p)
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as f:f.extractall(W/'tools/arc_unpacker')
        jsonwrite(W/'reports/ARC_BINARY.json',{'release':r['tag_name'],'url':a['browser_download_url'],'sha256':sha(p),'path':str(p)});break
