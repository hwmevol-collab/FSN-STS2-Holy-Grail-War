"""Evidence-based FHA tags, script references, and voice/dialogue relations."""
from common import *
from fha_prepare import FHA,FW,BACK
from index_scripts import attrs
import re,math
EXTRA=['scene','day','time_slot','location','loop_phase','costume','expression','variant','pose','distance','tag_evidence']
JP_EN={'バゼット':'Bazett Fraga McRemitz','カレン':'Caren Hortensia','アヴェンジャー':'Avenger / Angra Mainyu','アンリ':'Avenger / Angra Mainyu','セイバー':'Saber','セイバーオルタ':'Saber Alter','凛':'Rin','アーチャー':'Archer','士郎':'Shirou','桜':'Sakura','イリヤ':'Illya','ランサー':'Lancer','ライダー':'Rider','キャスター':'Caster / Medea','小次郎':'Assassin / Kojiro','アサシン':'Assassin','ハサン':'Hassan','バーサーカー':'Berserker','ギルガメッシュ':'Gilgamesh','言峰':'Kirei','藤ねえ':'Taiga'}

def text_of(r):
    p=pathlib.Path(r['converted_path'])
    return p.read_text('utf-8') if p.suffix in {'.txt','.json'} and p.exists() else ''
def clean_dialogue(s):return re.sub(r'\[[^\]]*\]','',s).strip()
UNKNOWN_SPEAKERS={'**','？？？','???','unknown'}
def known_speaker(s):return '' if s in UNKNOWN_SPEAKERS else s
def run():
    rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')]
    for r in rows:
        for f in EXTRA:r.setdefault(f,'')
        if r['conversion_status']=='utf8_text' and r['detected_format']=='UNKNOWN':r['detected_format']='TEXT'
    dic=next(r for r in rows if r['filename']=='voicename2key.dic');mapping={k.lower():v for v,k in re.findall(r'"([^"]+)"\s*=>\s*string\s*"([^"]+)"',text_of(dic))}
    csvwrite(FHA/'Metadata/CHARACTER_VOICE_CODES.csv',[dict(code=k,original_character=v,character=JP_EN.get(v,v) if known_speaker(v) else 'unknown',evidence_asset_id=dic['asset_id'],evidence_path=dic['source_logical_path']) for k,v in mapping.items()])
    names=set(mapping.values())|set(JP_EN);ordered=sorted(names,key=len,reverse=True)
    lookup=collections.defaultdict(list)
    for r in rows:
        lookup[pathlib.Path(r['filename']).stem.casefold()].append(r)
        if r['category']=='Voice':
            parts=pathlib.Path(r['filename']).stem.split('_');code=parts[1].lower() if len(parts)==3 else parts[0].lower()
            r['character']='unknown'
            if code in mapping:r.update(character=JP_EN.get(mapping[code],mapping[code]) if known_speaker(mapping[code]) else 'unknown',tag_evidence='voicename2key.dic '+dic['asset_id']+'; init.tjs filename speaker rule; ambiguous speaker placeholders retained as unknown')
        elif r.get('thumbnail_path'):
            stem=pathlib.Path(r['filename']).stem
            char=next((n for n in ordered if stem.startswith(n)),None)
            if char:
                r['character']=JP_EN.get(char,char);r['tag_evidence']='Explicit filename prefix: '+char
                remain=stem[len(char):];m=re.match(r'([^\d]+)?(\d+)([a-zA-Z]*)(?:\(([^)]+)\))?',remain)
                if m:
                    costume,pose,variant,distance=m.groups();r.update(pose=pose or '',variant=variant or '',distance=distance or '')
                    if costume and costume in {'私服','制服','甲冑','水着','神主','エプロン','メイド','和服','浴衣','パジャマ','バイト','戦闘服'}:r['costume']=costume
                # Letter suffixes are variants, not invented emotional labels.
            tm=re.search(r'\((昼|夜|夕|朝|夕方)\)',stem)
            if tm:r['time_slot']=tm[1];r['tag_evidence']+='; filename time marker'
    def targets(storage,typ):
        stem=pathlib.Path(storage.replace('\\','/')).stem.casefold();found=lookup.get(stem,[])
        if typ in ('voice','bgm','se'):return [x for x in found if x['conversion_status']=='native_audio']
        if typ=='image':return [x for x in found if x.get('thumbnail_path')]
        if typ=='movie':return [x for x in found if x['category']=='Movies']
        return found
    scripts=[];refs=[];voices=[];scenes=[];vc=collections.Counter();evidence=[]
    for r in rows:
        if 'シーン一覧' in r['filename']:
            for i,line in enumerate(text_of(r).splitlines()):
                fs=line.split('\t')
                if len(fs)>=5:scenes.append(dict(asset_id=r['asset_id'],line=i+1,day=fs[0],location=fs[1],scene_title=fs[2],script=fs[3],page=fs[4],evidence='tab-separated source scene table'))
    scene_lookup={(s['script'],s['page']):s for s in scenes}
    ref_types={'say':'voice','hfsay':'voice','voice':'voice','playvoice':'voice','play':'bgm','bgm':'bgm','playbgm':'bgm','se':'se','seloop':'se','playse':'se','sound':'se','movie':'movie','openvideo':'movie','playmovie':'movie','video':'movie'}
    image_commands={'bg','fg','image','chgfg','load','loadimage','movefg','move','dash','displayedon','rep','fadein','fadeout','find','hffacechg','hfchara','hfbg','irimage','staffrollappearimage'}
    script_ext={'.ks','.tjs','.ksc','.fcf','.asd','.dic','.csv','.po','.mo','.txt'}
    for r in rows:
        if r['extension'] not in script_ext:continue
        text=text_of(r)
        if not text:continue
        lines=text.splitlines();scene=pathlib.Path(r['filename']).stem;counts=collections.Counter();chars=set();time='';scene_day='';location='';page=''
        for i,line in enumerate(lines):
            if line.lstrip().startswith(';'):continue
            if line.startswith('*'):
                page=line[1:].split('|')[0]
                record=scene_lookup.get((scene,re.sub(r'^page','',page)))
                if record:scene_day=record['day'];location=record['location']
            tokens=[]
            if line.lstrip().startswith('@'):
                full=line.lstrip()[1:];tokens=[(full,0,len(line))]
            else:tokens=[(m[1],m.start(),m.end()) for m in re.finditer(r'\[([a-zA-Z_][^\]]*)\]',line)]
            for full,start,end in tokens:
                cmd=full.split()[0].lower() if full.split() else '';a=attrs(full)
                if cmd=='setnighttime':time='night'
                elif cmd=='setdaytime':time='day'
                if cmd=='resetvoice' and a.get('day') and a['day'].isdigit():scene_day=a['day']
                typ=ref_types.get(cmd,'image' if cmd in image_commands else '')
                storages=[]
                if typ:
                    for key in ('storage','file','storages','bg','base'):
                        if a.get(key):storages.extend((key,s.strip()) for s in a[key].split(',') if s.strip())
                for key,storage in storages:
                    if key in ('bg','base') and typ!='image':continue
                    found=[] if storage.startswith('&') else targets(storage,typ)
                    counts[typ]+=1
                    for target in found or [None]:
                        refs.append(dict(script_id=r['asset_id'],source_version='HollowAtaraxia',route=r['route'],scene=scene,locale=r['locale'],line=i+1,command=cmd,reference_type=typ,reference_name=storage,target_asset_id=target['asset_id'] if target else '',target_path=target['extracted_path'] if target else '',resolution_status='exact_name_multiple_preserved_candidates' if len(found)>1 else 'exact_name' if found else 'dynamic_expression' if storage.startswith('&') else 'unresolved_name',scene_page=page,attribute=key))
                    if typ=='voice' and found:
                        speaker=a.get('speaker') or a.get('name') or ''
                        parts=storage.split('_');code=parts[1].lower() if len(parts)==3 else parts[0].lower()
                        if not speaker:speaker=mapping.get(code,'')
                        speaker=known_speaker(speaker)
                        if speaker:chars.add(speaker)
                        # Inline voices bind only to their following segment. KAG line voices
                        # bind to the dialogue before the next voice/page/label command.
                        tail=line[end:] if not line.lstrip().startswith('@') else ''
                        tail=re.split(r'\[(?:hfsay|say)\b',tail,maxsplit=1)[0]
                        collected=[tail] if tail else []
                        if not tail:
                            for nl in lines[i+1:i+40]:
                                if nl.startswith('*') or re.match(r'\s*@(?:say|hfsay|pg|r|return|jump|call)\b',nl):break
                                if nl.lstrip().startswith(('@',';')):continue
                                if nl.strip():collected.append(nl)
                        dialogue=clean_dialogue('\n'.join(collected))
                        if dialogue:
                            for target in found:
                                voices.append(dict(voice_asset_id=target['asset_id'],voice_file=target['extracted_path'],speaker=speaker,route=r['route'],scene=scene,dialogue=dialogue,locale=r['locale'],duration=target['duration'],script_id=r['asset_id'],line=i+1,mapping_evidence=cmd+'/'+key+' exact filename; speaker from explicit name or voicename2key.dic',placeholder='',language=r['locale'],scene_page=page,day=scene_day,time_slot=time,source_version='HollowAtaraxia'));vc[target['asset_id']]+=1
                if a.get('chara'):chars.add(a['chara'])
            # Explicit Hanafuda victory/dialogue array rows: character, translated
            # string literals, and an exact voice filename. No TJS evaluation.
            if line.lstrip().startswith('['):
                literals=re.findall(r'"((?:\\.|[^"\\])*)"',line)
                if literals:
                    found=targets(literals[-1],'voice')
                    if found:
                        speaker=known_speaker(literals[0]);dialogue='\n'.join(literals[1:-1]);
                        if speaker:chars.add(speaker)
                        for target in found:
                            refs.append(dict(script_id=r['asset_id'],source_version='HollowAtaraxia',route=r['route'],scene=scene,locale=r['locale'],line=i+1,command='explicit_dialogue_array',reference_type='voice',reference_name=literals[-1],target_asset_id=target['asset_id'],target_path=target['extracted_path'],resolution_status='exact_name',scene_page=page,attribute='array voice column'))
                            if dialogue:
                                voices.append(dict(voice_asset_id=target['asset_id'],voice_file=target['extracted_path'],speaker=speaker,route=r['route'],scene=scene,dialogue=dialogue,locale=r['locale'],duration=target['duration'],script_id=r['asset_id'],line=i+1,mapping_evidence='Explicit Hanafuda array: character + dialogue strings + exact voice filename',placeholder='',language=r['locale'],scene_page=page,day=scene_day,time_slot=time,source_version='HollowAtaraxia'));vc[target['asset_id']]+=1
        r['scene']=scene
        if scene_day:r['day']=scene_day
        if time:r['time_slot']=time
        scripts.append(dict(script_id=r['asset_id'],asset_id=r['asset_id'],source_version='HollowAtaraxia',route=r['route'],scene=scene,original_filename=r['filename'],locale=r['locale'],character_names=';'.join(sorted(chars)),line_count=len(lines),choice_count=len(re.findall(r'(?:@(?:select|choice)\b|\[(?:link|choice|select)\b)',text,re.I)),image_refs=counts['image'],voice_refs=counts['voice'],bgm_refs=counts['bgm'],se_refs=counts['se'],movie_refs=counts['movie'],text_path=r['converted_path'],script_mapping=r['script_mapping'],day=scene_day,time_slot=time,location=location,loop_phase='',notes='Static explicit KAG commands; all patch candidates preserved; dynamic expressions unresolved; no visual guesses'))
    # Literal table references extend the index without pretending to evaluate arbitrary TJS.
    tables=[r for r in rows if r['category']=='Database' or r['extension'] in ('.fcf','.dic','.csv','.po','.mo')]
    csvwrite(FHA/'Metadata/SCRIPT_INDEX.csv',scripts)
    csvwrite(FHA/'Metadata/SCENE_TABLE.csv',scenes,['asset_id','line','day','location','scene_title','script','page','evidence'])
    csvwrite(FHA/'Metadata/ASSET_REFERENCES.csv',refs)
    csvwrite(FHA/'Metadata/VOICE_DIALOGUE_RELATIONS.csv',voices)
    csvwrite(FHA/'Metadata/VOICE_INDEX.csv',[dict(voice_file=r['extracted_path'],asset_id=r['asset_id'],speaker=r['character'] if r['character']!='unknown' else '',route=r['route'],scene='',dialogue='',locale=r['locale'],duration=r['duration'],working_path=r['converted_path'],dialogue_mapping_count=vc[r['asset_id']],notes='Speaker identity supported by voicename2key.dic; detailed relations in VOICE_DIALOGUE_RELATIONS.csv',codec=r['codec'],sample_rate=r['sample_rate'],channels=r['channels'],bitrate=r['bitrate'],sha256=r['sha256'],source_version='HollowAtaraxia') for r in rows if r['category']=='Voice'])
    csvwrite(FHA/'Metadata/DATABASE_INDEX.csv',[dict(asset_id=r['asset_id'],source_container=r['source_container'],logical_path=r['source_logical_path'],locale=r['locale'],route=r['route'],text_path=r['converted_path'],decrypted_path=r['decrypted_path'],type=r['detected_format']) for r in tables])
    groups=collections.defaultdict(list)
    for r in rows:groups[r['source_logical_path'].casefold()].append(r)
    overrides=[]
    for path,rs in groups.items():
        if len(rs)<2:continue
        kind='same_logical_path_same_hash' if len({r['sha256'] for r in rs})==1 else 'same_logical_path_different_hash'
        group=hashlib.sha256(path.encode()).hexdigest()[:16]
        for r in rs:r['override_group']=group;overrides.append(dict(override_group=group,relationship=kind,asset_id=r['asset_id'],logical_path=r['source_logical_path'],source_container=r['source_container'],sha256=r['sha256']))
    csvwrite(FHA/'Metadata/OVERRIDE_MAP.csv',overrides)
    csvwrite(FHA/'Metadata/TAG_EVIDENCE.csv',[{k:r.get(k,'') for k in ['asset_id','filename','character']+EXTRA} for r in rows if r['tag_evidence']])
    with (FHA/'Metadata/ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    jsonwrite(FHA/'Metadata/INDEX_SUMMARY.json',dict(scripts=len(scripts),references=len(refs),resolved_references=sum(bool(r['target_asset_id']) for r in refs),unresolved_references=sum(not r['target_asset_id'] for r in refs),voice_assets=sum(r['category']=='Voice' for r in rows),voice_dialogue_rows=len(voices),mapped_voice_assets=len(vc),explicit_character_codes=len(mapping),character_tagged_assets=sum(r['character']!='unknown' for r in rows),costume_tagged_assets=sum(bool(r['costume']) for r in rows),scene_table_rows=len(scenes),database_tables=len(tables),override_rows=len(overrides)))
    print('FHA INDEX',len(scripts),len(refs),len(voices),'voices mapped',len(vc),flush=True)
if __name__=='__main__':run()
