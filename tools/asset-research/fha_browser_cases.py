from fha_prepare import *
import sqlite3,subprocess
def run():
    db=sqlite3.connect(L/'Metadata/ASSET_CATALOG.sqlite');db.row_factory=sqlite3.Row;cases=[]
    for v in ['Original','Remastered','HollowAtaraxia']:
        selectors={'image':"thumbnail_path <> '' AND width >= 600",'audio':"category IN ('Voice','BGM') AND converted_path <> ''",'video':"converted_path LIKE '%.mp4'"}
        for kind,condition in selectors.items():
            row=db.execute('SELECT * FROM assets WHERE source_version=? AND '+condition+' ORDER BY asset_id LIMIT 1',(v,)).fetchone()
            if row:cases.append(dict(test=v+'_'+kind,asset_id=row['asset_id'],filename=row['filename'],path=row['converted_path'],category=row['category']))
    for category in ['Voice','BGM']:
        row=db.execute('SELECT * FROM assets WHERE source_version=? AND category=? ORDER BY asset_id LIMIT 1',('HollowAtaraxia',category)).fetchone()
        cases.append(dict(test='FHA_'+category,asset_id=row['asset_id'],filename=row['filename'],path=row['converted_path'],category=row['category']))
    for name in ['Bazett Fraga McRemitz','Caren Hortensia','Avenger / Angra Mainyu']:
        row=db.execute("SELECT * FROM assets WHERE source_version='HollowAtaraxia' AND character=? AND thumbnail_path <> '' ORDER BY asset_id LIMIT 1",(name,)).fetchone()
        if row:cases.append(dict(test=name,asset_id=row['asset_id'],filename=row['filename'],path=row['converted_path'],category=row['category']))
    db.close();jsonwrite(FW/'BROWSER_TEST_CASES.json',cases);print(json.dumps(cases,ensure_ascii=False,indent=2))
    evidence=[]
    for name in ['se245.wav','se247.wav']:
        rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')];r=next(r for r in rows if r['filename']==name and r['source_container'].endswith('sound.xp3'))
        p=subprocess.run(['D:/DDplay/ffmpeg/ffmpeg.exe','-v','error','-i',r['extracted_path'],'-f','null','-'],capture_output=True,text=True)
        evidence.append(dict(asset_id=r['asset_id'],path=r['extracted_path'],decode_exit_code=p.returncode,stderr=p.stderr,checksum_mismatch_retained=True))
    jsonwrite(FHA/'Metadata/CHECKSUM_EXCEPTION_MEDIA_VALIDATION.json',evidence);assert all(r['decode_exit_code']==0 for r in evidence)
if __name__=='__main__':run()
