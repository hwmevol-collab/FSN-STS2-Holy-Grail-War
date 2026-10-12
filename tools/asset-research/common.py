import os, sys, json, csv, hashlib, datetime, collections, shutil, struct, pathlib
W=pathlib.Path(os.environ.get('FSN_WORK_ROOT','E:/FSN_MASTER_ASSET_WORK'))
L=pathlib.Path(os.environ.get('FSN_LIBRARY_ROOT','E:/FSN_MASTER_ASSET_LIBRARY'))
os.environ.update(TEMP=str(W/'tmp'),TMP=str(W/'tmp'),PIP_CACHE_DIR=str(W/'tmp/pip'),PYTHONPYCACHEPREFIX=str(W/'tmp/pycache'))
SOURCES={'Original':pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate stay night/Fate stay night'),'Remastered':pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate stay night REMASTERED/Fate stay night REMASTERED')}
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def csvwrite(p,rows,fields=None):
    p=pathlib.Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields or list(rows[0]) if rows else fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
def jsonwrite(p,data):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def signature(b,ext=''):
    if b.startswith(b'XP3\r\n \n\x1a\x8bg\x01'):return 'XP3'
    for magic,name in [(b'\x89PNG\r\n\x1a\n','PNG'),(b'OggS','OGG'),(b'RIFF','RIFF'),(b'BM','BMP'),(b'TLG','TLG'),(b'\xff\xd8\xff','JPEG'),(b'DDS ','DDS'),(b'FPD','FPD'),(b'FCD','FCD'),(b'FDT','FDT'),(b'EPK','EPK'),(b'PK\x03\x04','ZIP'),(b'7z\xbc\xaf\x27\x1c','7Z'),(b'MZ','PE'),(b'fLaC','FLAC'),(b'OTTO','OTF'),(b'\x00\x01\x00\x00','TTF'),(b'ttcf','TTC'),(b'\x00\x00\x01\xba','MPEG'),(b'\x30\x26\xb2\x75','ASF'),(b'\x1aE\xdf\xa3','MATROSKA')]:
        if b.startswith(magic):
            if name=='RIFF':return {b'WAVE':'WAV',b'WEBP':'WEBP',b'AVI ':'AVI'}.get(b[8:12],'RIFF')
            return name
    if b[4:8]==b'ftyp':return 'MP4'
    if b[:2] in [b'\xff\xfe',b'\xfe\xff']:return 'TEXT_UTF16'
    if b.startswith(b'\xef\xbb\xbf'):return 'TEXT_UTF8'
    if b.startswith(b'\xfe\xfe'):return 'KIRIKIRI_ENCRYPTED_TEXT'
    if ext.lower() in {'.ks','.tjs','.txt','.ini','.json','.csv','.xml','.ksc','.log','.md5','.fate'} and b'\x00' not in b:return 'TEXT_CANDIDATE'
    return 'UNKNOWN'
