from fuc_common import *
from fuc_fpk_extract import strict_prs
from fuc_europe_index import EU
def run():
    rows=readjson(STAGE_ROOT/'FPK_EXTRACTED_INDEX.json');files={r['logical_path']:r for r in readjson(STAGE_ROOT/'SOURCE_INVENTORY.json')};groups=collections.defaultdict(list)
    for r in rows:groups[r['container']].append(r)
    errors=[];verified=0
    for i,(name,entries) in enumerate(groups.items()):
        b=pathlib.Path(files[name]['physical_path']).read_bytes()
        for r in entries:
            try:
                part=b[r['offset']:r['offset']+r['compressed_size']];decoded=part if r['compressed_size']==r['uncompressed_size'] else strict_prs(part,r['uncompressed_size']);assert len(decoded)==r['size'] and hashlib.sha256(decoded).hexdigest()==r['sha256'];verified+=1
            except Exception as e:errors.append(dict(container=name,entry_index=r['entry_index'],name=r['name'],error=str(e)))
        if i%100==0:log('INDEPENDENT FPK CHECK',i+1,'/',len(groups),verified)
    summary=dict(containers=len(groups),entries=len(rows),strict_independent_entries_verified=verified,failures=errors,method='Independent strict PRS or literal raw branch; exact decoded length and SHA256 match for every entry',source_version='FateUnlimitedCodesPortable_Europe');jsonwrite(EU/'Metadata/FPK_FULL_INDEPENDENT_VERIFICATION.json',summary);assert not errors;log('ALL FPK ENTRY BYTES INDEPENDENTLY VERIFIED',verified)
if __name__=='__main__':run()
