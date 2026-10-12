from common import *
from fha_prepare import FHA,FW,BACK
import re,math
def run():
    new=[json.loads(s) for s in (FHA/'Metadata/ASSETS.jsonl').open(encoding='utf-8')]
    oldby=collections.defaultdict(list);pictures={}
    for line in (BACK/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8'):
        r=json.loads(line);oldby[r['sha256']].append(r)
        if r['thumbnail_path'] and r['phash']:pictures.setdefault(r['sha256'],r)
    bands=collections.defaultdict(set);names=collections.defaultdict(set)
    for h,r in pictures.items():
        p=int(r['phash'],16);names[pathlib.Path(r['filename']).stem.casefold()].add(h)
        for i in range(8):bands[i,(p>>(i*8))&255].add(h)
    out=[];counts=collections.Counter()
    fields=['fha_asset_id','fsn_asset_id','fsn_source_version','match_type','fha_sha256','fsn_sha256','phash_distance','dhash_distance','fha_width','fha_height','fsn_width','fsn_height','evidence','confirmed']
    for j,r in enumerate(new):
        h=r['sha256'];found=oldby.get(h,[])
        if found:
            for o in found:out.append(dict(fha_asset_id=r['asset_id'],fsn_asset_id=o['asset_id'],fsn_source_version=o['source_version'],match_type='exact_payload',fha_sha256=h,fsn_sha256=h,evidence='Identical preserved payload SHA-256; every logical origin remains in catalog',confirmed=True))
            counts['exact_payload_assets']+=1;continue
        candidates=[]
        if r['thumbnail_path'] and r['phash']:
            p=int(r['phash'],16);d=int(r['dhash'],16);possible=set(names.get(pathlib.Path(r['filename']).stem.casefold(),()))
            for i in range(8):possible.update(bands.get((i,(p>>(i*8))&255),()))
            for oh in possible:
                o=pictures[oh];pd=(p^int(o['phash'],16)).bit_count();dd=(d^int(o['dhash'],16)).bit_count()
                same_name=pathlib.Path(r['filename']).stem.casefold()==pathlib.Path(o['filename']).stem.casefold()
                if (pd<=6 and dd<=10) or same_name:
                    candidates.append((pd+dd,pd,dd,o,same_name))
            candidates.sort(key=lambda x:(x[0],x[3]['asset_id']))
        if candidates:
            best=candidates[0][0]
            for score,pd,dd,o,same_name in candidates[:8]:
                if score>best+4:continue
                if pd<=3 and dd<=3:
                    larger=float(r['width'] or 0)*float(r['height'] or 0)>float(o['width'] or 0)*float(o['height'] or 0)
                    kind='higher_resolution_candidate' if larger else 'same_visual_candidate'
                else:kind='modified_candidate'
                out.append(dict(fha_asset_id=r['asset_id'],fsn_asset_id=o['asset_id'],fsn_source_version=o['source_version'],match_type=kind,fha_sha256=h,fsn_sha256=o['sha256'],phash_distance=pd,dhash_distance=dd,fha_width=r['width'],fha_height=r['height'],fsn_width=o['width'],fsn_height=o['height'],evidence='Decoded-image pHash/dHash'+('; exact basename' if same_name else '')+'; candidate requires review',confirmed=False));counts[kind]+=1
        else:out.append(dict(fha_asset_id=r['asset_id'],match_type='FHA_unique_candidate',fha_sha256=h,evidence='No existing exact payload or qualifying visual/name candidate found; no deletion or identity claim',confirmed=False));counts['FHA_unique_candidate']+=1
        if j%5000==0:print('COMPARE',j,flush=True)
    csvwrite(FHA/'Metadata/FSN_VS_FHA.csv',out,fields);jsonwrite(FHA/'Metadata/COMPARISON_SUMMARY.json',dict(rows=len(out),old_unique_images=len(pictures),counts=dict(counts),method='SHA256 all payloads; 8-band pHash candidates; Hamming distance and dHash; every non-SHA relationship is explicitly unconfirmed'))
    print('COMPARE DONE',len(out),dict(counts),flush=True)
if __name__=='__main__':run()
