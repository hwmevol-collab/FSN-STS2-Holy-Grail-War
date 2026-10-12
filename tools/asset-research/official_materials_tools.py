"""Acquire the official Tesseract release as a portable E: tool, no installer execution."""
import pathlib,urllib.request,json,hashlib,subprocess,shutil,datetime
W=pathlib.Path('E:/FSN_MASTER_ASSET_WORK');D=W/'tools/official-tesseract';D.mkdir(parents=True,exist_ok=True)
if (D/'TOOLS_MANIFEST.json').exists():
    print('Reusing frozen E: Tesseract tool/model manifest; no version drift.');raise SystemExit(0)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FSN-official-reference-pipeline'}),timeout=90)
release=json.load(get('https://api.github.com/repos/tesseract-ocr/tesseract/releases/latest'))
a=next(a for a in release['assets'] if a['name'].endswith('.exe') and 'w64' in a['name'])
p=D/a['name']
if not p.exists():
    with get(a['browser_download_url']) as src,p.open('wb') as out:shutil.copyfileobj(src,out)
h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
assert h==a['digest'].split(':')[1]
binroot=D/'portable';binroot.mkdir(exist_ok=True)
if not list(binroot.rglob('tesseract.exe')):
    s=subprocess.run(['D:/7-Zip/7z.exe','x','-y','-bsp0','-o'+str(binroot),str(p)],capture_output=True)
    assert s.returncode==0,s.stdout[-1000:]
exe=next(binroot.rglob('tesseract.exe'));data=D/'tessdata';data.mkdir(exist_ok=True)
for folder in ['configs','tessconfigs']:
    if (exe.parent/'tessdata'/folder).exists():shutil.copytree(exe.parent/'tessdata'/folder,data/folder,dirs_exist_ok=True)
commit=json.load(get('https://api.github.com/repos/tesseract-ocr/tessdata_fast/commits/main'))['sha']
models=[]
for lang in ['jpn','jpn_vert','eng','osd']:
    q=data/(lang+'.traineddata');url='https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/'+commit+'/'+q.name
    if not q.exists():
        with get(url) as src,q.open('wb') as out:shutil.copyfileobj(src,out)
    models.append({'language':lang,'model':'tessdata_fast','commit':commit,'path':str(q),'sha256':hashlib.file_digest(q.open('rb'),'sha256').hexdigest(),'source':url})
version=subprocess.run([str(exe),'--version'],capture_output=True,text=True).stdout
manifest={'tool':'Tesseract','version':version,'executable':str(exe),'tessdata':str(data),'models':models,'installer_source':a['browser_download_url'],'installer_sha256':h,'release':release['html_url'],'method':'7-Zip extraction, installer never executed','alternatives_reviewed':{'PaddleOCR':'Japanese supported; larger inference environment, not needed for auxiliary layer','EasyOCR':'Japanese/Latin supported; larger Torch environment, not needed for auxiliary layer'},'documentation':['https://tesseract-ocr.github.io/tessdoc/Data-Files.html','https://tesseract-ocr.github.io/tessdoc/Data-Files-in-tessdata_fast.html']}
(D/'TOOLS_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False,indent=2))
