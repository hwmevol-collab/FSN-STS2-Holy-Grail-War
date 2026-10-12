from common import *
import re,sqlite3,io
def attrs(s):return {m[0]:(m[1] or m[2] or m[3]) for m in re.findall(r'([\w]+)\s*=\s*(?:"([^"]*)"|\x27([^\x27]*)\x27|([^\s\]]+))',s)}
def run():
    cat=L/'Metadata/ASSET_CATALOG.jsonl'
    rows=[json.loads(s) for s in (cat if cat.exists() else W/'reports/BASE_ASSETS.jsonl').open(encoding='utf-8')]
    if not cat.exists():
        results={r['sha256']:r for r in map(json.loads,(W/'reports/CONVERSION_RESULTS.jsonl').open(encoding='utf-8'))}
        for r in rows:r.update({k:v for k,v in results.get(r['sha256'],{}).items() if k!='sha256'})
    lookup=collections.defaultdict(list);epks=collections.defaultdict(list)
    for r in rows:
        name=pathlib.Path(r['filename']).stem.casefold();base=re.sub(r'@\d+$','',name)
        lookup[(r['source_version'],base)].append(r)
        if r['extension']=='.epk' and r['converted_path']:epks[(r['source_container'],r['script_mapping'])].append(r)
    scripts=[];voice_refs=collections.Counter();refs_count=voice_count=0;typed_voice=set()
    ref_fields=['script_id','source_version','route','scene','locale','line','command','reference_type','reference_name','target_asset_id','target_path','resolution_status']
    voice_fields=['voice_asset_id','voice_file','speaker','route','scene','dialogue','locale','duration','script_id','line','mapping_evidence','placeholder']
    ref_file=(L/'Metadata/ASSET_REFERENCES.csv').open('w',encoding='utf-8-sig',newline='');ref_writer=csv.DictWriter(ref_file,fieldnames=ref_fields);ref_writer.writeheader()
    voice_file=(L/'Metadata/VOICE_DIALOGUE_MAPPING.csv').open('w',encoding='utf-8-sig',newline='');voice_writer=csv.DictWriter(voice_file,fieldnames=voice_fields);voice_writer.writeheader()
    def targets(ver,storage,typ):
        stem=pathlib.Path(storage.replace('\\','/')).stem.casefold();stem=re.sub(r'@\d+$','',stem);candidates=lookup.get((ver,stem),[])
        if typ in {'voice','bgm','se'}:candidates=[r for r in candidates if r['detected_format'] in {'FCD','OGG','WAV','MP3','FLAC'}]
        elif typ=='image':candidates=[r for r in candidates if r.get('thumbnail_path')]
        return candidates
    for n,r in enumerate(rows):
        if r['extension'] not in {'.ks','.tjs','.ksc','.epk','.tl','.fcf','.asd'} or not r['converted_path']:continue
        text=pathlib.Path(r['converted_path']).read_text('utf-8');lines=text.splitlines();scene=r['script_mapping'] if r['extension']=='.epk' else pathlib.Path(r['filename']).stem
        locales={}
        if r['extension']=='.ks' and r['source_version']=='Remastered':
            for e in epks.get((r['source_container'],scene),[]):
                data={}
                for line in pathlib.Path(e['converted_path']).read_text('utf-8').splitlines()[2:]:
                    parts=line.split('::')
                    if len(parts)>=3:data[parts[1].strip()]=parts[2]
                locales[e['locale']]=data
        counts=collections.Counter();chars=set();route_context=''
        for i,line in enumerate(lines):
            commands=[]
            if line.lstrip().startswith('@'):commands=[line.lstrip()[1:]]
            else:commands=re.findall(r'\[([a-zA-Z_][^\]]*)\]',line)
            for full in commands:
                cmd=full.split()[0].lower() if full.split() else '';a=attrs(full)
                if cmd=='resetvoice':route_context=a.get('route','')
                typ=''
                if cmd in {'say','voice','playvoice','wv'}:typ='voice'
                elif cmd in {'play','bgm','playbgm','fadeinbgm'}:typ='bgm'
                elif cmd in {'se','seloop','playse','sound'}:typ='se'
                elif cmd in {'bg','image','fg','chgfg','load','loadimage','movefg','staffrollappearimage'}:typ='image'
                storage=a.get('storage') or a.get('file') or a.get('name')
                if typ and storage and not storage.startswith('&'):
                    found=targets(r['source_version'],storage,typ);counts[typ]+=1
                    selected=found or [None]
                    for target in selected:
                        ref_writer.writerow(dict(script_id=r['asset_id'],source_version=r['source_version'],route=r['route'],scene=scene,locale=r['locale'],line=i+1,command=cmd,reference_type=typ,reference_name=storage,target_asset_id=target['asset_id'] if target else '',target_path=target['extracted_path'] if target else '',resolution_status='exact_name_multiple_preserved_candidates' if len(found)>1 else 'exact_name' if found else 'unresolved_name'))
                        refs_count+=1
                    if typ=='voice':
                        following=[]
                        for nextline in lines[i+1:i+15]:
                            if nextline.startswith('@') or nextline.startswith('*'):break
                            if nextline.strip():following.append(nextline)
                        placeholders=re.findall(r'\$\$\$([^$]+)\$\$\$','\n'.join(following));raw='\n'.join(following)
                        dialogue_by_locale={}
                        if placeholders and locales:
                            for loc,table in locales.items():
                                value='\n'.join(table.get(key,'') for key in placeholders)
                                if value:dialogue_by_locale[loc]=value
                        elif raw and not placeholders:dialogue_by_locale[r['locale']]=raw
                        for target in found:
                            typed_voice.add(target['asset_id'])
                            for loc,dialogue in dialogue_by_locale.items():
                                voice_writer.writerow(dict(voice_asset_id=target['asset_id'],voice_file=target['extracted_path'],speaker=a.get('speaker',''),route=r['route'],scene=scene,dialogue=dialogue,locale=loc,duration=target['duration'],script_id=r['asset_id'],line=i+1,mapping_evidence='@say/storage exact base name; @number suffix retained as separate variant' if '@' in target['filename'] else cmd+'/storage exact basename',placeholder=';'.join(placeholders)))
                                voice_refs[target['asset_id']]+=1;voice_count+=1
                if a.get('speaker'):chars.add(a['speaker'])
        scripts.append(dict(script_id=r['asset_id'],source_version=r['source_version'],route=r['route'],scene=scene,original_filename=r['filename'],locale=r['locale'],character_names=';'.join(sorted(chars)),line_count=len(lines),choice_count=len(re.findall(r'(?:@(?:select|choice)\b|\[(?:link|choice|select)\b)',text,re.I)),bgm_refs=counts['bgm'],se_refs=counts['se'],image_refs=counts['image'],voice_refs=counts['voice'],text_path=r['converted_path'],script_mapping=r['script_mapping'],notes='Static command parsing; state expressions retained in source; speaker left blank unless explicitly present'))
        if len(scripts)%500==0:print('SCRIPT_INDEX',len(scripts),'references',refs_count,'voice_dialogues',voice_count,flush=True)
    ref_file.close();voice_file.close();csvwrite(L/'Metadata/SCRIPT_INDEX.csv',scripts)
    voice_rows=[]
    for r in rows:
        if r['category']=='Voice' or r['asset_id'] in typed_voice or (r['detected_format']=='FCD' and '@' in r['filename']):
            voice_rows.append(dict(voice_file=r['extracted_path'],asset_id=r['asset_id'],speaker='',route=r['route'],scene='',dialogue='',locale=r['locale'],duration=r['duration'],working_path=r['converted_path'],dialogue_mapping_count=voice_refs[r['asset_id']],notes='Detailed mappings are in VOICE_DIALOGUE_MAPPING.csv; speaker requires explicit evidence'))
    csvwrite(L/'Metadata/VOICE_INDEX.csv',voice_rows)
    csvwrite(L/'Metadata/DATABASE_INDEX.csv',[dict(asset_id=r['asset_id'],source_container=r['source_container'],logical_path=r['source_logical_path'],locale=r['locale'],route=r['route'],text_path=r['converted_path'],decrypted_path=r['decrypted_path'],type=r['detected_format']) for r in rows if r['category']=='Database'])
    jsonwrite(W/'reports/SCRIPT_SUMMARY.json',{'scripts':len(scripts),'asset_references':refs_count,'voice_assets':len(voice_rows),'mapped_voice_assets':len(voice_refs),'voice_dialogue_rows':voice_count,'explicit_voice_asset_ids':sorted(typed_voice)})
    print('SCRIPTS DONE',len(scripts),refs_count,voice_count,flush=True)
if __name__=='__main__':run()
