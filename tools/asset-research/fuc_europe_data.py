from fuc_common import *
from fuc_motion_data_stage import relationships
ROOT=STAGE_ROOT
def run():
    payloads=readjson(ROOT/'FPK_EXTRACTED_INDEX.json');loose=readjson(ROOT/'SOURCE_INVENTORY.json');relationships(payloads)
    strings=[];path=ROOT/'Executable/EBOOT_DECRYPTED.bin';b=path.read_bytes();assert b[:4]==b'\x7fELF'
    for m in re.finditer(rb'[\x20-\x7e]{5,}',b):
        value=m[0].decode('ascii');strings.append(dict(source_file=str(path),offset=m.start(),encoding='ASCII',text=value,semantic_role='unclassified_executable_string',evidence='Actual decrypted NPEH00007 EBOOT ELF bytes; no Japanese executable offsets reused'))
    for r in loose+payloads:
        name=r.get('logical_path',r.get('name',''));ext=pathlib.Path(name).suffix.lower()
        if ext not in {'.txt','.lst','.seq','.ttd','.mil','.pef','.bpo','.amo','.fan'}:continue
        data=pathlib.Path(r['physical_path']).read_bytes()
        for m in re.finditer(rb'[\x20-\x7e]{6,}',data):
            value=m[0].decode('ascii')
            if ext in {'.txt','.lst'} or re.search(r'(?i)\.tm2|\.gmo|\.mot|\.fpk|chr/|eft/|saber|archer|command|mission|font|stage|rider|lancer',value):strings.append(dict(source_file=r['physical_path'],offset=m.start(),encoding='ASCII',text=value,semantic_role='resource_or_text_candidate',evidence='Actual full Europe payload string; no guessed move/command table decoding'))
    csvwrite(ROOT/'FUC_GAME_DATA_INDEX.csv',strings,['source_file','offset','encoding','text','semantic_role','evidence'])
    jsonwrite(ROOT/'GAME_DATA_SUMMARY.json',dict(eboot_elf_sha256=sha(path),indexed_strings=len(strings),move_command_tables_decoded=0,character_table_verified=False,status='ACTUAL_EXECUTABLE_AND_PAYLOAD_STRINGS_INDEXED_TABLE_SEMANTICS_UNRESOLVED'))
    fonts=[dict(source=r.get('logical_path',r.get('name','')),path=r['physical_path'],sha256=r['sha256'],status='NAME_CANDIDATE_PRESERVED',notes='Filename candidate only; glyph layout not yet decoded') for r in loose+payloads if re.search(r'(?i)(font|glyph|\.pgf$)',r.get('logical_path',r.get('name','')))]
    csvwrite(ROOT/'FONT_INDEX.csv',fonts,['source','path','sha256','status','notes'])
    weapons=[dict(source=r['name'],container=r['container'],source_sha256=r['sha256'],status='PATH_CANDIDATE_UNCONFIRMED',evidence='Explicit weapon-like resource path; no Fate lore naming') for r in payloads if re.search(r'(?i)(wep/|weapon/|sword|excal|bolg|bakuya|kanshou)',r['name'])]
    csvwrite(ROOT/'WEAPON_MODEL_INDEX.csv',weapons,['source','container','source_sha256','status','evidence'])
    # Compare matching logical identities without allocating Japan recovery asset IDs.
    jp=FW/'Japan_Recovery';comparisons=[]
    for scope,jrows,erows in [('ISO',readjson(jp/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json'),loose),('FPK',readjson(jp/'FPK_EXTRACTED_INDEX.json'),payloads)]:
        def key(r):return (r.get('container','ISO9660'),r.get('logical_path',r.get('name','')),r.get('entry_index',''))
        jmap={key(r):r for r in jrows if r.get('complete_extent',True)};emap={key(r):r for r in erows}
        for k in sorted(set(jmap)|set(emap),key=str):
            j,e=jmap.get(k),emap.get(k);relation=('exact_payload' if j['sha256']==e['sha256'] else 'different_payload') if j and e else 'Japan_recovery_only' if j else 'Europe_only'
            comparisons.append(dict(scope=scope,container=k[0],logical_path=k[1],entry_index=k[2],Japan_recovery_sha256=j.get('sha256','') if j else '',Europe_sha256=e.get('sha256','') if e else '',relation=relation,notes='Europe_only means not recovered from the currently truncated Japan source; it does not establish a European regional exclusive. Japan rows receive no master asset_id.'))
    csvwrite(ROOT/'JAPAN_RECOVERY_VS_EUROPE.csv',comparisons);jsonwrite(ROOT/'JAPAN_RECOVERY_COMPARISON_SUMMARY.json',dict(counts=dict(collections.Counter(r['relation'] for r in comparisons)),Europe_only_definition='当前截断日版中未恢复到；不是欧版独占',Japan_catalog_ids_allocated=0))
    # Source containers and custom BIN files are explicitly inventoried, even if unparsed.
    csvwrite(ROOT/'NON_FPK_CONTAINER_INVESTIGATION.csv',[dict(r,investigation='No known container magic; retained as unknown executable/data' if r['extension']=='.bin' else 'PSP PRX module preserved; decrypted EBOOT separately indexed') for r in loose if r['extension'] in {'.bin','.prx'}])
    log('GAME DATA',len(strings),'FONT CANDIDATES',len(fonts),'JP/EU',dict(collections.Counter(r['relation'] for r in comparisons)))
if __name__=='__main__':run()
