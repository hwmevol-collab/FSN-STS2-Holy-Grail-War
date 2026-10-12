"""Acceptance and report for the additive semantic layer. No emulator or core writes."""
from fuc_semantic_common import *
import zipfile
from urllib.parse import urljoin, urlparse, unquote
from html.parser import HTMLParser

OUT=pathlib.Path(r'C:\Users\Murasame\Documents\Codex\2026-10-06\files-pasted-by-the-user-fate-2\outputs')

def main():
    b=semantic_frozen();s=readjson(SM/'FUC_SEMANTIC_MAPPING_SUMMARY.json')
    stable=readjson(SW/'STABILITY_FINAL.json')
    # Repeat all frozen file hashes after the additive Gallery build.
    changed=[r['path'] for r in b['files'] if not pathlib.Path(r['path']).is_file() or sha(pathlib.Path(r['path']))!=r['sha256']]
    assert not changed,changed
    con=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite').replace('\\','/')+'?mode=ro',uri=True)
    ids={r[0] for r in con.execute('select asset_id from assets')}
    assert len(ids)==268504 and max(ids)=='FSN268504'
    assert con.execute('pragma integrity_check').fetchone()[0]=='ok'
    con.close()
    rows={p.stem:readrows(p) for p in SM.glob('*.csv')}
    chars=rows['FUC_CHARACTER_SEMANTIC_INDEX'];commands=rows['FUC_COMMAND_INDEX'];anims=rows['FUC_MOVE_ANIMATION_MAP'];moves=rows['FUC_MOVE_INDEX'];graph=rows['FUC_MOVE_RESOURCE_GRAPH']
    keys={r['move_id'] for r in moves};assert len(keys)==len(moves)
    assert all(not r.get('target_asset_id') or r['target_asset_id'] in ids for r in graph)
    assert all(r['move_id'] in keys for r in graph)
    # Verify captured returned bank tables against preserved source bytes, using the
    # existing normalization rule. This does not run or extend the MOT evaluator.
    bank_checks=[]
    for r in anims:
        if r['mapping_status']!='confirmed_runtime':continue
        p=pathlib.Path(r['evidence']);a=readjson(p);ret=a['selector_return'];folder=p.parent
        assert ret['clip_number']==a['state_id']==int(r['clip'])
        assert ret['bank_index']==int(r['bank']) and len(ret['source_matches'])==1
        src=pathlib.Path(ret['source_matches'][0]['source']);raw=src.read_bytes()
        assert sha(src)==ret['source_matches'][0]['sha256']
        h=(folder/'selected_bank_header.bin').read_bytes();tab=(folder/'selected_bank_table.bin').read_bytes()
        base,count=struct.unpack_from('<HH',h,4);bank=int(ret['bank_pointer'],16)
        relative=[x-bank if x else 0 for x in struct.unpack('<'+'I'*count,tab)]
        assert len(raw)==struct.unpack_from('<I',h,12)[0]
        assert count==struct.unpack_from('>I',raw,4)[0]
        assert relative==list(struct.unpack_from('>'+'I'*count,raw,16))
        assert relative[int(r['clip'])-base]==ret['selected_offset']
        bank_checks.append(dict(move_id=r['move_id'],source=str(src),sha256=sha(src),offset_slots=count,selected_offset=ret['selected_offset'],status='PASS'))
    cleanup=readjson(SW/'RUNTIME_CLEANUP.json')
    assert cleanup['Closed'] and cleanup['CpuBreakpointsRemaining']==cleanup['MemoryBreakpointsRemaining']==0
    checks={
        'A_character_schema':set(r['internal_code'] for r in chars if r['status']=='confirmed_runtime')=={'lan','sir','rin'},
        'B_move_state_schema':s['ROM_state_rows']==352 and s['normal_command_rows']==178 and s['conditional_programs']==783,
        'C_command_to_state':len([r for r in commands if r['schema']=='natural_input_selector_anchor' and r['status']=='confirmed_runtime'])>=3,
        'D_actual_bank_clip_mapping':len(bank_checks)>=3 and any(r['move_id']=='lan:state:145' for r in bank_checks),
        'E_game_UI_names':len([r for r in moves if r['name_mapping_status']=='confirmed_ui'])>=3,
        'F_complete_cross_resource_chain':all(any(r['move_id']=='lan:state:145' and r['relation_type']==rel and r['status']=='confirmed_runtime' for r in graph) for rel in ['observed_command','body_model','animation_clip','effect_sequence','effect_model','observed_voice_payload']),
        'G_stability':stable['status']=='PASS' and not changed and len(ids)==268504,
    }
    assert all(checks.values()),checks
    jsonwrite(SW/'FINAL_ACCEPTANCE.json',dict(timestamp=now(),criteria=checks,bank_source_checks=bank_checks,changed_frozen_files=changed,graph_asset_references='all exist in unchanged catalog',runtime_cleanup=cleanup))
    s.update(status='FUC_MOVE_COMMAND_SEMANTIC_MAPPING_PASS',acceptance_criteria=checks,final_hash_recheck=now(),final_changed_frozen_files=changed,runtime_cleanup=cleanup,recommended_next_step='FUC_FINAL_FREEZE_AND_AUDIT',gallery_validation=readjson(SW/'GALLERY_VALIDATION.json'))
    jsonwrite(SM/'FUC_SEMANTIC_MAPPING_SUMMARY.json',s)
    # Preserve evidence within the semantic sidecar, without a large trace/source copy.
    evidence=SM/'Evidence/Anchors';evidence.mkdir(parents=True,exist_ok=True)
    bounded=['ANCHOR.json','actor.bin','s2.bin','s5.bin','command_fields.bin','player_after.bin','selected_bank_header.bin','selected_bank_table.bin']
    for p in (SW/'Anchors').glob('*/ANCHOR.json'):
        dst=evidence/p.parent.name;dst.mkdir(exist_ok=True)
        for n in bounded:
            if (p.parent/n).is_file():shutil.copy2(p.parent/n,dst/n)
    for n in ['STABILITY_FINAL.json','FINAL_ACCEPTANCE.json','RUNTIME_CLEANUP.json','GALLERY_VALIDATION.json']:
        shutil.copy2(SW/n,SM/'Evidence'/n)
    shutil.copy2(SW/'Parsed/PARSE_FAILURES.json',SM/'Evidence/PARSE_FAILURES.json')
    report=(SW/'FINAL_REPORT_TEMPLATE.md').read_text('utf-8')
    catalog_lines=[]
    for n in ['ASSET_CATALOG.csv','ASSET_CATALOG.jsonl','ASSET_CATALOG.sqlite']:
        entry=next(r for r in b['files'] if pathlib.Path(r['path'])==L/'Metadata'/n)
        catalog_lines.append(f"| {n} | `{entry['sha256']}` | unchanged |")
    report=report.replace('CATALOG_HASH_ROWS','\n'.join(catalog_lines)).replace('FINAL_TIMESTAMP',s['final_hash_recheck'])
    target=L/'Reports/FUC_MOVE_COMMAND_SEMANTIC_MAPPING_REPORT.md';target.write_text(report,'utf-8')
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ('href','src') and value and not value.startswith('#'):self.links.append(value)
    links=Links();links.feed((L/'Gallery/FUC_SEMANTIC_MOVES.html').read_text('utf-8'))
    for ref in links.links:
        assert not urlparse(ref).scheme,ref
        assert (L/'Gallery'/unquote(ref)).resolve().is_file(),ref
    assert len(list(SM.glob('*.csv')))==11
    OUT.mkdir(parents=True,exist_ok=True);shutil.copy2(target,OUT/target.name)
    readme='''# FUC Semantic Mapping delivery

Status: FUC_MOVE_COMMAND_SEMANTIC_MAPPING_PASS
Source: FateUnlimitedCodesPortable_Europe; no new FSN asset IDs.

Canonical sidecars: E:\\FSN_MASTER_ASSET_LIBRARY\\FateUnlimitedCodesPortable_Europe\\Metadata\\SemanticMapping
Canonical Gallery: E:\\FSN_MASTER_ASSET_LIBRARY\\Gallery\\FUC_SEMANTIC_MOVES.html
Canonical report: E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\FUC_MOVE_COMMAND_SEMANTIC_MAPPING_REPORT.md

Semantic keys are qualified relationship identities, not asset IDs. Numeric ROM
state IDs and unbound UI entries remain distinct. Empty fields mean unknown.
There are 3 actual returned-bank mappings and 5 source-bank candidates. A name
being decoded does not confirm its state/animation association.

Rebuild in the existing workspace (requires retained fuc_anim_common and other
pre-existing tools): run fuc_semantic_parse.py, fuc_semantic_build.py, then
fuc_semantic_gallery.py with the existing workspace Python. Dynamic anchor
scripts are optional evidence collection tools; do not run them during a rebuild.
fuc_semantic_finalize.py checks the frozen baseline, captured bank fingerprints,
and sidecar references before issuing the report. No original Catalog writes.
Do not rerun fuc_semantic_baseline.py to replace the original baseline.

The evidence bundle contains limited selector and source-pointer captures,
original UI screenshots, and checksums. Original ROM bytes, models, audio,
large runtime traces and the whole RawExtracted tree are not duplicated.

Next step: FUC_FINAL_FREEZE_AND_AUDIT. Low-level runtime remains CLOSED FOR MOD DEVELOPMENT.
'''
    (SM/'README.md').write_text(readme,'utf-8')
    manifest=[]
    for p in sorted(SM.rglob('*')):
        if p.is_file() and p.name!='FUC_SEMANTIC_DELIVERY_MANIFEST.json':manifest.append(dict(path=p.relative_to(SM).as_posix(),size=p.stat().st_size,sha256=sha(p)))
    scripts=list((W/'scripts').glob('fuc_semantic*.*'))
    jsonwrite(SM/'FUC_SEMANTIC_DELIVERY_MANIFEST.json',dict(timestamp=now(),files=manifest,scripts=[dict(path=str(p),sha256=sha(p)) for p in scripts],catalog_baseline=str(SB/'BASELINE.json'),gallery_sha256=sha(L/'Gallery/FUC_SEMANTIC_MOVES.html'),report_sha256=sha(target)))
    # An output copy works offline on this machine and resolves canonical resource links.
    html=(L/'Gallery/FUC_SEMANTIC_MOVES.html').read_text('utf-8')
    (OUT/'FUC_SEMANTIC_MOVES.html').write_text(html.replace('<meta charset="utf-8">','<meta charset="utf-8"><base href="file:///E:/FSN_MASTER_ASSET_LIBRARY/Gallery/">',1),'utf-8')
    bundle=OUT/'FUC_SEMANTIC_MAPPING.zip'
    with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SM.rglob('*')):
            if p.is_file():z.write(p,'SemanticMapping/'+p.relative_to(SM).as_posix())
        for p in scripts:z.write(p,'tools/'+p.name)
        z.write(target,target.name);z.write(OUT/'FUC_SEMANTIC_MOVES.html','FUC_SEMANTIC_MOVES.html');z.write(SW/'FINAL_REPORT_TEMPLATE.md','tools/FINAL_REPORT_TEMPLATE.md')
    with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
    print(json.dumps(dict(status=s['status'],criteria=checks,bundle=str(bundle),bundle_bytes=bundle.stat().st_size,frozen_hashes=len(b['files']),new_asset_ids=0),ensure_ascii=False))
if __name__=='__main__':main()
