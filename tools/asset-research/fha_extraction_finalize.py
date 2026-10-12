from common import *
from fha_prepare import ROOT,FHA,FW
from fha_extract import payload
from verify_xp3 import index
import zlib
def run():
    rows=[json.loads(s) for s in (FHA/'Metadata/RAW_ASSETS.jsonl').open(encoding='utf-8')]
    # Declared-unencrypted warning entries must retain their original readable bytes,
    # even when their producer stored an unrelated checksum.
    for r in rows:
        if r.get('flags')==0 and not r.get('adler32_verified',True) and r['source_container'].endswith('/inner.xp3'):
            if r['source_container'].startswith('language_'):p=next((FHA/'RawExtracted/Molebox/language_SChinese.xp3').glob('*.xp3'))
            elif r['source_container'].startswith('FateFD.exe/extra'):p=FHA/'RawExtracted/Molebox/FateFD.exe/extra/FateFD_embedded.xp3'
            else:continue
            b=payload(p,r);pathlib.Path(r['extracted_path']).write_bytes(b)
            r.update(sha256=hashlib.sha256(b).hexdigest(),detected_format='TEXT_CANDIDATE',adler32_mode='unfiltered_payload',notes='Producer checksum exception on declared-unencrypted warning text; readable original bytes preserved')
    with (FHA/'Metadata/RAW_ASSETS.jsonl').open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    inventory=json.loads((FHA/'Metadata/SOURCE_INVENTORY.json').read_text('utf-8'))
    for r in inventory:
        if r['filename'] in ['language_SChinese.xp3','voice.xp3','voice2.xp3']:
            r.update(detected_format='MOLEBOX_NEWDES_QUICKBOX',probable_container=True,notes='NewDES QUICKBOX signature verified; directory CRC32 and every payload block CRC16 verified; nested XP3 expanded')
        if r['filename']=='FateFD.exe':r.update(detected_format='PE_MOLEBOX_KIRIKIRI',probable_container=True,notes='Molebox wrapped PE: embedded TPM and NewDES encrypted extra area containing XP3; statically expanded, never executed')
    csvwrite(FHA/'Metadata/SOURCE_INVENTORY.csv',inventory);jsonwrite(FHA/'Metadata/SOURCE_INVENTORY.json',inventory)
    logs=json.loads((FHA/'Metadata/EXTRACTION_LOG.json').read_text('utf-8'))
    csvwrite(FHA/'Metadata/EXTRACTION_LOG.csv',logs,['source','source_container','kind','tool','plugin','command','expected_entries','verified_entries','files_extracted','blocks_verified','status','errors'])
    s=json.loads((FHA/'Metadata/SOURCE_SUMMARY.json').read_text('utf-8'));s.update(containers=15,source_format_counts=dict(collections.Counter(r['detected_format'] for r in inventory)),physical_containers=15,nested_containers=4,extraction_attempts=len(logs));jsonwrite(FHA/'Metadata/SOURCE_SUMMARY.json',s)
    jsonwrite(FHA/'Metadata/EXTRACTION_SUMMARY.json',dict(physical_containers=15,nested_containers=4,attempted=len(logs),statuses=dict(collections.Counter(x['status'] for x in logs)),raw_logical_assets=len(rows),checksum_exceptions=[{k:r.get(k) for k in ['source_container','source_logical_path','flags','size','adler32','adler32_mode','notes']} for r in rows if r.get('adler32_verified') is False]))
if __name__=='__main__':run()
