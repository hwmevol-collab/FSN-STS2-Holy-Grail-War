from fuc_common import *
ROOT=STAGE_ROOT
def run():
    old=collections.defaultdict(list)
    db=sqlite3.connect(f'file:{(L/"Metadata/ASSET_CATALOG.sqlite").as_posix()}?mode=ro',uri=True)
    for aid,source,h,wh in db.execute('SELECT asset_id,source_version,sha256,working_sha256 FROM assets'):
        old[h].append((aid,source,'preservation'))
        if wh:old[wh].append((aid,source,'working'))
    model_count=db.execute("SELECT COUNT(*) FROM assets WHERE lower(detected_format)='gmo' OR lower(extension)='.gmo'").fetchone()[0];db.close()
    rows=[];assets=readjson(ROOT/'FPK_EXTRACTED_INDEX.json')
    for r in assets:
        ext=pathlib.Path(r['name']).suffix
        if not r['size']:continue
        if r['sha256'] in old:
            for aid,source,kind in old[r['sha256']]:rows.append(dict(fuc_asset_id='',fuc_source=r['name'],fuc_container=r['container'],fuc_sha256=r['sha256'],other_asset_id=aid,other_source=source,relation='exact_payload',evidence='SHA256 equals existing '+kind+' payload; FUC ROM CRC not verified'))
        elif ext=='.gmo' and model_count==0:rows.append(dict(fuc_asset_id='',fuc_source=r['name'],fuc_container=r['container'],fuc_sha256=r['sha256'],other_asset_id='',other_source='Original/Remastered/HollowAtaraxia',relation='FUC_unique',evidence='Actual GMO magic; existing catalog has no GMO model assets. WORK recovery only.'))
    csvwrite(ROOT/'FSN_VS_FUC.csv',rows,['fuc_asset_id','fuc_source','fuc_container','fuc_sha256','other_asset_id','other_source','relation','evidence'])
    jsonwrite(ROOT/'CROSS_SOURCE_SUMMARY.json',dict(existing_catalog_rows=246605,existing_gmo_models=model_count,recovered_fpk_payloads_compared=len(assets),exact_payload_relations=sum(r['relation']=='exact_payload' for r in rows),fuc_unique_model_rows=sum(r['relation']=='FUC_unique' for r in rows),perceptual_image_or_reused_audio_search='NOT_PERFORMED_PENDING_COMPLETE_ROM',status='WORK_ONLY_NO_FINAL_FUC_ASSET_IDS'))
    log('CROSS SOURCE',readjson(ROOT/'CROSS_SOURCE_SUMMARY.json'))
if __name__=='__main__':run()
