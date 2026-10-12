"""Conservative image-role sidecar. Container buckets are not visual guesses."""
from fha_prepare import *
def run():
    rows=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')];images={r['asset_id']:r for r in rows if r['thumbnail_path']};evidence=collections.defaultdict(list)
    with (FHA/'Metadata/ASSET_REFERENCES.csv').open(encoding='utf-8-sig',newline='') as f:
        for ref in csv.DictReader(f):
            if ref['reference_type']=='image' and ref['target_asset_id'] in images and (ref['command'].lower() in {'bg','hfbg'} or ref.get('attribute') in {'bg','background'}):
                evidence[ref['target_asset_id']].append(('Background','KAG background rendering command; does not rule out event CG content',ref['script_id'],ref['line']))
    gallery=next((r for r in rows if r['filename']=='galleryimagelayer.tjs' and r.get('converted_path')),None)
    if gallery:
        text=pathlib.Path(gallery['converted_path']).read_text('utf-8');prefixes=re.findall(r'var\s+(?:real_extension|guest_extension)\s*=\s*"([^"]+)"',text)
        for r in images.values():
            if any(r['filename'].startswith(p) for p in prefixes):evidence[r['asset_id']].append(('CG','Explicit Gallery wallpaper image storage prefix (wallpaper art, not automatically EventCG)',gallery['asset_id'],''))
    out=[]
    for r in images.values():
        if '/bgimage.xp3' in r['source_container']:evidence[r['asset_id']].append(('Background','Named bgimage archive: background rendering bucket; includes possible EventCG content','',''))
        if '/fgimage.xp3' in r['source_container'] and r['category']=='Characters':evidence[r['asset_id']].append(('Foreground','Named fgimage archive; original character-layer resource, identity tagged separately','',''))
        if re.search(r'(?:^|/)(?:effects?|エフェクト)/',r['source_logical_path'],re.I):evidence[r['asset_id']].append(('Effect','Explicit source directory label','',''))
        es=evidence[r['asset_id']]
        if not es:out.append(dict(asset_id=r['asset_id'],semantic_class='unknown',container_category=r['category'],logical_path=r['source_logical_path'],evidence='',script_id='',line='',status='UNCLASSIFIED_NO_VISUAL_GUESS'))
        else:
            seen=set()
            for cls,why,sid,line in es:
                key=(cls,why)
                if key in seen:continue
                seen.add(key);out.append(dict(asset_id=r['asset_id'],semantic_class=cls,container_category=r['category'],logical_path=r['source_logical_path'],evidence=why,script_id=sid,line=line,status='SOURCE_EVIDENCE_ROLE'))
    csvwrite(FHA/'Metadata/IMAGE_ROLES.csv',out);counts={cls:len({r['asset_id'] for r in out if r['semantic_class']==cls}) for cls in ['CG','Background','Foreground','EventCG','Effect','unknown']}
    jsonwrite(FHA/'Metadata/IMAGE_ROLE_SUMMARY.json',dict(created_at=now(),logical_images=len(images),unique_asset_counts=counts,limitations='Roles can overlap. CG wallpaper art is explicit gallery use. Background is a rendering role, not a claim about depicted content. EventCG and effects stay unknown without explicit source evidence. Existing Catalog category buckets are retained.'))
    print('IMAGE ROLES',counts,flush=True)
if __name__=='__main__':run()
