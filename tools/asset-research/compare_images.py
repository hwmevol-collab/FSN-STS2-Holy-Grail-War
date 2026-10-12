from common import *
import re
class BK:
    def __init__(self):self.root=None
    def add(self,value,index):
        if self.root is None:self.root=[value,[index],{}];return
        node=self.root
        while True:
            d=(value^node[0]).bit_count()
            if d==0:node[1].append(index);return
            if d not in node[2]:node[2][d]=[value,[index],{}];return
            node=node[2][d]
    def query(self,value,limit):
        nodes=[self.root] if self.root else [];out=[]
        while nodes:
            node=nodes.pop();d=(value^node[0]).bit_count()
            if d<=limit:out.extend((d,i) for i in node[1][:8])
            nodes.extend(child for k,child in node[2].items() if d-limit<=k<=d+limit)
        return out
def run():
    rows=[json.loads(s) for s in (L/'Metadata/ASSET_CATALOG.jsonl').open(encoding='utf-8')];images=[r for r in rows if r['phash']];unique={r['sha256']:r for r in reversed(images)};values=list(unique.values());tree=BK();similar=[];hash_groups=collections.defaultdict(list)
    for i,r in enumerate(values):
        value=int(r['phash'],16);hash_groups[(r['phash'],r['dhash'])].append(r)
        cand=sorted(tree.query(value,4))[:6]
        for d,j in cand:
            b=values[j];dh=(int(r['dhash'],16)^int(b['dhash'],16)).bit_count()
            if dh>12:continue
            similar.append(dict(asset_a=b['asset_id'],asset_b=r['asset_id'],file_a=b['extracted_path'],file_b=r['extracted_path'],phash_distance=d,dhash_distance=dh,visual_similarity=round(1-d/64,4),same_bytes=False,notes='Candidate only; perceptual hashes cannot prove equality, especially solid-color and cropped images'))
        tree.add(value,i)
        if i%1000==0:print('IMAGE_COMPARE',i,'/',len(values),flush=True)
    csvwrite(L/'Metadata/IMAGE_SIMILARITY.csv',similar,['asset_a','asset_b','file_a','file_b','phash_distance','dhash_distance','visual_similarity','same_bytes','notes'])
    csvwrite(L/'Metadata/IMAGE_HASH_GROUPS.csv',[dict(phash=k[0],dhash=k[1],asset_id=r['asset_id'],sha256=r['sha256'],file=r['extracted_path']) for k,v in hash_groups.items() if len(v)>1 for r in v],['phash','dhash','asset_id','sha256','file'])
    originals=[r for r in images if r['source_version']=='Original'];remastered=[r for r in images if r['source_version']=='Remastered'];byhash=collections.defaultdict(list);byname=collections.defaultdict(list)
    def name(r):return pathlib.Path(r['filename']).stem.casefold()
    for r in remastered:byhash[r['sha256']].append(r);byname[name(r)].append(r)
    comparison=[];matched=set();counts=collections.Counter()
    for a in originals:
        candidates=byhash.get(a['sha256'],[]) or byname.get(name(a),[]);chosen=None;dist=None;equal=False;kind='original_unmatched'
        if candidates:
            chosen=min(candidates,key=lambda b:(int(a['phash'],16)^int(b['phash'],16)).bit_count());dist=(int(a['phash'],16)^int(chosen['phash'],16)).bit_count();equal=a['sha256']==chosen['sha256']
            if equal:kind='exact_bytes'
            elif dist<=8 and chosen['width']*chosen['height']>a['width']*a['height']:kind='higher_resolution_candidate'
            elif dist<=8:kind='same_composition_candidate'
            else:kind='same_name_visual_change_candidate'
            matched.add(chosen['asset_id'])
        counts[kind]+=1
        comparison.append(dict(original_file=a['extracted_path'],remastered_file=chosen['extracted_path'] if chosen else '',original_asset_id=a['asset_id'],remastered_asset_id=chosen['asset_id'] if chosen else '',match_type=kind,original_resolution=f"{a['width']}x{a['height']}",remastered_resolution=f"{chosen['width']}x{chosen['height']}" if chosen else '',hash_equal=equal,visual_similarity=round(1-dist/64,4) if dist is not None else '',notes='Candidates require visual review; unmatched does not prove absence in the other version'))
    for b in remastered:
        if b['asset_id'] not in matched:
            comparison.append(dict(original_file='',remastered_file=b['extracted_path'],original_asset_id='',remastered_asset_id=b['asset_id'],match_type='remastered_unmatched',original_resolution='',remastered_resolution=f"{b['width']}x{b['height']}",hash_equal=False,visual_similarity='',notes='No matching candidate selected; may be a variant or renamed asset, not proven new'))
            counts['remastered_unmatched']+=1
    csvwrite(L/'Metadata/ORIGINAL_VS_REMASTERED.csv',comparison)
    # Exact inheritance across all types, including scripts, audio and fonts.
    byte_matches=[];allgroup=collections.defaultdict(list)
    for r in rows:allgroup[r['sha256']].append(r)
    for h,items in allgroup.items():
        if len({r['source_version'] for r in items})==2:
            for r in items:byte_matches.append(dict(sha256=h,asset_id=r['asset_id'],source_version=r['source_version'],file=r['extracted_path'],category=r['category']))
    csvwrite(L/'Metadata/CROSS_VERSION_EXACT.csv',byte_matches,['sha256','asset_id','source_version','file','category'])
    jsonwrite(W/'reports/COMPARISON_SUMMARY.json',{'image_candidates':len(similar),'image_unique':len(values),'cross_version_image_rows':len(comparison),'match_types':dict(counts),'cross_version_exact_asset_records':len(byte_matches),'method':'SHA256 exact across all types; same-basename pHash candidate matching for images; global near pHash radius4/dHash12 top6; no deletion; unmatched is not proven version-exclusive'})
    print('COMPARE DONE',dict(counts),flush=True)
if __name__=='__main__':run()
