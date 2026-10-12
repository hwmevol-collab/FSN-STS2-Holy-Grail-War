from common import *
import sqlite3, re, subprocess, zipfile, math, zlib
FUC=L/'FateUnlimitedCodesPortable'
FW=W/'fuc'
STAGE_ROOT=pathlib.Path(os.environ.get('FUC_STAGE_ROOT',str(FW/'source_diagnostic')))
SOURCE_VERSION=os.environ.get('FUC_SOURCE_VERSION','FateUnlimitedCodesPortable_Japan_Recovery')
BACK=W/'backups/fuc-pre-integration'
SRC=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材/Fate-Unlimited Codes Portable (Japan).zip')
FF=pathlib.Path('D:/DDplay/ffmpeg/ffmpeg.exe')
FP=pathlib.Path('D:/DDplay/ffmpeg/ffprobe.exe')
def readjson(p):return json.loads(pathlib.Path(p).read_text('utf-8'))
def readrows(p):
    with pathlib.Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def rowsjson(p):return [json.loads(x) for x in pathlib.Path(p).open(encoding='utf-8')]
def writejsonl(p,rows):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
def log(*a):print(*a,flush=True)
