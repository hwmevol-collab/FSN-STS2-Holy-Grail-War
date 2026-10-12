"""Read existing FAN/AMO payloads; no extraction or ID allocation."""
from fuc_battle_common import *
def main():
    battle_frozen();db=sqlite3.connect((L/'Metadata/ASSET_CATALOG.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    rows=[dict(r) for r in db.execute("select * from assets where source_version='FateUnlimitedCodesPortable_Europe' and (lower(extension) in ('.fan','.amo') or source_logical_path like 'chr/lan/%')")];db.close();out={};samples={}
    for ext in ['.fan','.amo']:
        items=[]
        for r in rows:
            if r['extension'].lower()!=ext:continue
            p=pathlib.Path(r['extracted_path']);b=p.read_bytes();assert sha(p)==r['sha256'];ss=[m.group().decode('ascii') for m in re.finditer(rb'[ -~]{5,}',b)];paths=[s for s in ss if re.search(r'(?i)\.gmo|\.mot|\.fan|\.amo|\.fpk|chr/|eft/|snd/',s)]
            item=dict(asset_id=r['asset_id'],source_path=r['extracted_path'],logical_path=r['source_logical_path'],parent_fpk=r['source_container'],size=len(b),sha256=r['sha256'],magic=b[:16].hex(),header_words_le=list(struct.unpack('<'+'I'*(min(64,len(b))//4),b[:min(64,len(b))//4*4])),header_words_be=list(struct.unpack('>'+'I'*(min(64,len(b))//4),b[:min(64,len(b))//4*4])),strings=ss,referenced_paths=paths,status='unknown',notes='Actual bytes and strings only; loader/consumer unverified')
            items.append(item)
            if r['source_logical_path'].startswith(('chr/sir/','chr/rin/','chr/lan/')) and '/0000.fpk' in r['source_container']:samples.setdefault(ext,[]).append(item)
        out[ext]=items
        jsonwrite(BR/('FAN_SOURCE_INVENTORY.json' if ext=='.fan' else 'AMO_SOURCE_INVENTORY.json'),items)
        log(ext,'logical',len(items),'unique',len({r['sha256'] for r in items}),'headers',collections.Counter(r['magic'][:8] for r in items))
    jsonwrite(BR/'PRIORITY_SOURCE_SAMPLES.json',samples)
    lan=[r for r in rows if r['source_logical_path'].startswith('chr/lan/') and '/0000.fpk' in r['source_container']]
    jsonwrite(BR/'LANCER_PACKAGE_EXISTING_ASSETS.json',lan)
    log('PRIORITY FAN/AMO',[(k,len(v)) for k,v in samples.items()]);log('LAN PACKAGE',[(r['asset_id'],r['source_logical_path'],r['size']) for r in lan])
if __name__=='__main__':main()
