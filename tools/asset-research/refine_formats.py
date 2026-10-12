from common import *
from convert_assets import convert
import re
def run():
    p=W/'reports/BASE_ASSETS.jsonl';rows=[json.loads(s) for s in p.open(encoding='utf-8')]
    append=[]
    for r in rows:
        if r['extension']=='.ico':
            r['detected_format']='ICO';r['category']='Icons';cv=convert(r);append.append(cv)
        if r['extension']=='.asd':
            r['category']='Scripts';append.append(convert(r))
        if r['extension']=='.tft':
            r['detected_format']='KIRIKIRI_PRERENDERED_FONT';r['category']='Fonts'
            append.append({'sha256':r['sha256'],'detected_format':'KIRIKIRI_PRERENDERED_FONT','conversion_status':'preserved_font','converted_path':''})
        if r['source_container']=='Loose' and r['filename']=='smash_dont_delete.bin':r['detected_format']='ZERO_FILLED_MARKER';r['category']='Metadata';append.append({'sha256':r['sha256'],'detected_format':'ZERO_FILLED_MARKER','conversion_status':'preserved_marker','converted_path':''})
    with p.open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    with (W/'reports/CONVERSION_RESULTS.jsonl').open('a',encoding='utf-8') as f:
        for r in append:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    pep=W/'reports/PE_CONVERSION_RESULTS.jsonl';pe=[json.loads(s) for s in pep.open(encoding='utf-8')];byhash={r['sha256']:r for r in rows if r['source_container'].startswith('PE:')}
    for r in pe:
        if r['detected_format']=='UNKNOWN':
            base=byhash.get(r['sha256'],{});m=re.search('PE resource type ([^;]+)',base.get('notes',''))
            if m:r['detected_format']='PE_RESOURCE_'+m.group(1);r['conversion_status']='preserved_resource_metadata'
    with pep.open('w',encoding='utf-8') as f:
        for r in pe:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print('REFINED',len(append),'PE records',len(pe),flush=True)
if __name__=='__main__':run()
