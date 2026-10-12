from fuc_common import *
from fuc_europe_inventory import EU_SRC,EU
def run():
    state=readjson(EU/'SOURCE_IDENTITY.json');assert state['PARAM_SFO']['DISC_ID']=='NPEH00007' and state['all_file_extents_in_source_bounds'] and sha(EU_SRC)==state['sha256']
    root=FW/'Europe';root.mkdir(exist_ok=True);rs=readjson(EU/'SOURCE_INVENTORY.json')
    mapped=[dict(r,declared_size=r['size'],available_size=r['size'],complete_extent=True,source_status='COMPLETE_EUROPE_ISO_EXTENT_HASHED') for r in rs]
    jsonwrite(root/'PARTIAL_ISO_FILESYSTEM_INVENTORY.json',mapped)
    jsonwrite(root/'SOURCE_IDENTITY.json',dict(state,source_version='FateUnlimitedCodesPortable_Europe',source_edition='Europe',source_complete=True,work_root=str(root)))
    csvwrite(root/'SOURCE_INVENTORY.csv',rs);jsonwrite(root/'SOURCE_INVENTORY.json',rs)
    log('EUROPE STAGING PREPARED',len(rs))
if __name__=='__main__':run()
