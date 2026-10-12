from fuc_common import *
ROOT=STAGE_ROOT
def motions(rows):
    out=[];failures=[]
    for r in rows:
        if not r['name'].endswith('.mot'):continue
        b=pathlib.Path(r['physical_path']).read_bytes()
        try:
            flags,count,table,total=struct.unpack_from('>4I',b);assert table==16 and total==len(b) and 0<count<4096 and table+4*count<=len(b)
            offsets=list(struct.unpack_from('>'+str(count)+'I',b,table));boundaries=sorted({x for x in offsets if x})+[len(b)]
            assert all(table+4*count<=x<len(b) for x in offsets if x)
            ends={x:y for x,y in zip(boundaries,boundaries[1:])}
            for i,o in enumerate(offsets):
                payload=b[o:ends[o]] if o else b''
                out.append(dict(animation_id=f"MOT_{r['sha256'][:12]}_{i:04d}",asset_id='',source_name=r['name'],source_container=r['container'],source_path=r['physical_path'],source_sha256=r['sha256'],motion_table_index=i,offset=o,size=len(payload),clip_sha256=hashlib.sha256(payload).hexdigest() if o else '',model_id='',character_code=r['name'].split('/')[1] if r['name'].startswith('chr/') else '',clip_name=f'motion_{i:04d}',semantic_role='unknown',frame_count='',fps='',duration='',bone_count='',animated_bones='',loop='',linked_effects='',linked_sound='',linked_model='',status='OFFSET_TABLE_VALIDATED_CLIP_PAYLOAD_UNPARSED' if o else 'EMPTY_TABLE_SLOT',notes='Big-endian table header and all offsets bounded against actual file. These are candidate clip slices; motion channels, skeleton bindings and playback not yet decoded. Shared archive is not proof of binding.'))
        except Exception as e:failures.append(dict(source_name=r['name'],source_path=r['physical_path'],error=str(e)))
    csvwrite(ROOT/'ANIMATION_INDEX.csv',out,['animation_id','asset_id','source_name','source_container','source_path','source_sha256','motion_table_index','offset','size','clip_sha256','model_id','character_code','clip_name','semantic_role','frame_count','fps','duration','bone_count','animated_bones','loop','linked_effects','linked_sound','linked_model','status','notes']);jsonwrite(ROOT/'MOTION_TABLE_FAILURES.json',failures)
    jsonwrite(ROOT/'MOTION_SUMMARY.json',dict(mot_files=sum(r['name'].endswith('.mot') for r in rows),parsed_offset_tables=sum(r['name'].endswith('.mot') for r in rows)-len(failures),table_slots=len(out),nonempty_candidate_clip_slices=sum(r['offset']>0 for r in out),motion_channels_decoded=0,playback_validated=0,amo_files=sum(r['name'].endswith('.amo') for r in rows),fan_files=sum(r['name'].endswith('.fan') for r in rows),status='RAW_RECOVERED_SEMANTICS_UNRESOLVED'))
def relationships(rows):
    chars=[];effects=[];stages=[];unknown=[];clusters=collections.defaultdict(list)
    unresolved={'.seq','.fan','.bpo','.amo','.mot','.bam','.tuv','.mil','.par','.pbd','.phd','.pef','.col'}
    for r in rows:
        parts=r['name'].lstrip('/').split('/');ext=pathlib.Path(r['name']).suffix
        if len(parts)>2 and parts[0] in {'chr','eft','snd'}:
            code=parts[1] if parts[0]=='chr' else parts[2] if parts[0]=='eft' and parts[1]=='chr' else ''
            if code:chars.append(dict(character_code=code,character='unknown',asset_name=r['name'],container=r['container'],physical_path=r['physical_path'],sha256=r['sha256'],evidence='explicit internal chr/<code>/ path; character name not inferred',costume_id='',palette_id='',variant=''))
        if parts[0]=='eft':effects.append(dict(effect_resource=r['name'],format_extension=ext,source_container=r['container'],physical_path=r['physical_path'],sha256=r['sha256'],linked_textures='',linked_model='',linked_animation='',linked_sound='',trigger_move='',character='',notes='Explicit eft/ archive path; timing and bindings unparsed'))
        if parts[0] in {'stg','stage'}:stages.append(dict(stage_code=parts[1],resource=r['name'],source_container=r['container'],physical_path=r['physical_path'],sha256=r['sha256'],evidence='explicit internal stage path',stage_name='unknown'))
        if ext in unresolved and r['size']:
            sample=pathlib.Path(r['physical_path']).open('rb').read(65536);c=collections.Counter(sample);entropy=-sum(v/len(sample)*math.log2(v/len(sample)) for v in c.values())
            magic=r['magic'];item=dict(asset=r['name'],container=r['container'],size=r['size'],sha256=r['sha256'],magic=magic,first_64_bytes=r['first_64_bytes'],entropy=entropy,probable_format=ext,cluster=ext+':'+magic[:8],status='UNKNOWN_PRESERVED_WORK_ONLY',notes='Raw bytes retained; filename extension is a clue, not a decoded specification')
            unknown.append(item);clusters[item['cluster']].append(item)
    csvwrite(ROOT/'CHARACTER_ASSET_MAP.csv',chars,['character_code','character','asset_name','container','physical_path','sha256','evidence','costume_id','palette_id','variant']);csvwrite(ROOT/'EFFECT_INDEX.csv',effects,['effect_resource','format_extension','source_container','physical_path','sha256','linked_textures','linked_model','linked_animation','linked_sound','trigger_move','character','notes']);csvwrite(ROOT/'STAGE_INDEX.csv',stages,['stage_code','resource','source_container','physical_path','sha256','evidence','stage_name']);csvwrite(ROOT/'FUC_UNKNOWN_FORMATS.csv',unknown)
    csvwrite(ROOT/'UNKNOWN_CLUSTERS.csv',sorted([dict(cluster=k,count=len(v),bytes=sum(r['size'] for r in v),example=v[0]['asset']) for k,v in clusters.items()],key=lambda r:r['bytes'],reverse=True))
def strings():
    p=ROOT/'CompleteFilesystemExtents/PSP_GAME/SYSDIR/BOOT.BIN';b=p.read_bytes();assert b[:4]==b'\x7fELF';out=[]
    for m in re.finditer(rb'[\x20-\x7e]{5,}',b):
        text=m[0].decode('ascii')
        if re.search(r'(?i)fpack|\.fpk|\.gmo|\.mot|\.ttd|\.vag|\.seq|\.amo|\.fan|\.pmf|\.at3|chr/|eft/|stg/|stage|command|saber|archer|lancer|rider',text):out.append(dict(source_file=str(p),offset=m.start(),encoding='ASCII',text=text,semantic_role='resource/string_candidate',evidence='actual JP BOOT.BIN bytes; no EU offsets reused'))
    csvwrite(ROOT/'FUC_GAME_DATA_INDEX.csv',out,['source_file','offset','encoding','text','semantic_role','evidence']);jsonwrite(ROOT/'GAME_DATA_SUMMARY.json',dict(boot_elf_sha256=sha(p),indexed_ascii_candidate_strings=len(out),move_command_tables_decoded=0,notes='JP BOOT.BIN is a plain ELF. No EBOOT decryption or emulator launch was necessary for these string offsets.'))
def run():
    rows=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');motions(rows);relationships(rows);strings();log('MOTION',readjson(ROOT/'MOTION_SUMMARY.json'));log('GAME DATA',readjson(ROOT/'GAME_DATA_SUMMARY.json'))
if __name__=='__main__':run()
