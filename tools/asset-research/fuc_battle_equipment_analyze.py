"""Compare runtime equipment attachment matrices with captured body matrices, without offset trials."""
from fuc_battle_common import *
import argparse,numpy as np
BASE=0x08800000
def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();folder=BR/'Snapshots'/a.name;b=(folder/'user_ram.bin').read_bytes();obj=readjson(folder/'OBJECT_MAP.json')
    def u(addr):return struct.unpack_from('<I',b,addr-BASE)[0]
    def mat(addr):return np.array(struct.unpack_from('<16f',b,addr-BASE),dtype=np.float64).reshape((4,4),order='F')
    body=next(r for r in obj['models'] if r.get('path')=='chr/lan/0000.gmo');weapon=next(r for r in obj['models'] if r.get('path')=='chr/lan/0001.gmo');bp=int(body['address'],16);wp=int(weapon['address'],16);target=mat(u(u(int(weapon['sdk'],16)+0x18)+4)+0xb0);sdk=int(body['sdk'],16);ptrs=[u(u(sdk+0x18)+i*4) for i in range(body['node_count'])];comparisons=[]
    for i,n in enumerate(ptrs):
        for off,label in [(0xb0,'local'),(0xf0,'world')]:comparisons.append({'body_ordinal':i,'sdk_node':hex(n),'matrix_field':label,'max_abs':float(np.max(np.abs(mat(n+off)-target))),'frobenius':float(np.linalg.norm(mat(n+off)-target))})
    result={'snapshot':a.name,'body':body,'equipment':weapon,'attachment_matrix':target.tolist(),'nearest_body_matrices':sorted(comparisons,key=lambda x:x['max_abs'])[:12],'equipment_wrapper_matrices':{hex(o):mat(wp+o).tolist() for o in [0x60,0xa0,0xe0,0x120]},'equipment_nodes':[]}
    wsdk=int(weapon['sdk'],16);wnodes=u(wp+0x5c)
    for i in range(weapon['node_count']):
        n=u(u(wsdk+0x18)+i*4);result['equipment_nodes'].append({'ordinal':i,'sdk_node':hex(n),'sdk_parent_field':hex(u(n+0x3c)),'flags':hex(u(wnodes+i*0x140)),'translation':struct.unpack_from('<4f',b,wnodes+i*0x140+0x20-BASE),'rotation_storage':struct.unpack_from('<4f',b,wnodes+i*0x140+0x50-BASE),'scale':struct.unpack_from('<4f',b,wnodes+i*0x140+0x30-BASE),'local':mat(n+0xb0).tolist(),'world':mat(n+0xf0).tolist()})
    jsonwrite(folder/'EQUIPMENT_ANALYSIS.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('body','equipment','equipment_wrapper_matrices','equipment_nodes')},indent=2))
if __name__=='__main__':main()
