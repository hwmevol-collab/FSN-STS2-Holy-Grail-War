"""Inspect a saved read-only PSP RAM snapshot; preserve address provenance."""
from fuc_battle_common import *
import argparse,struct
BASE=0x08800000
def main():
    p=argparse.ArgumentParser();p.add_argument('name');a=p.parse_args();folder=BR/'Snapshots'/a.name;b=(folder/'user_ram.bin').read_bytes()
    def u(addr):return struct.unpack_from('<I',b,addr-BASE)[0]
    def string(addr):return b[addr-BASE:addr-BASE+64].split(b'\0')[0].decode('ascii','replace')
    result={'globals':{hex(x):hex(u(x)) for x in [0x08a01998,0x08a0199c,0x08a019a0,0x08a019a4,0x08a019b4,0x08a019b8,0x08a019bc,0x08a019c4,0x08a019c8,0x08a019cc]},'models':[],'resources':[]}
    # Model registry nodes use payload, self, next, previous words. A sentinel payload is 1.
    head=u(0x08a019a4);cur=head;seen=set()
    while BASE<=cur<BASE+len(b)-16 and cur not in seen and len(seen)<4096:
        seen.add(cur);model=u(cur)
        if model==1:cur=u(cur+8);continue
        if BASE<=model<BASE+len(b)-0x340:
            resource=u(model+0x34);nodes=u(model+0x58);row={'address':hex(model),'record':hex(cur),'flags':hex(u(model)),'node_count':nodes,'resource':hex(resource),'sdk':hex(u(model+0x38)),'parent':hex(u(model+0x30)),'model_words':{hex(o):hex(u(model+o)) for o in range(0,0x60,4)}}
            if BASE<=resource<BASE+len(b)-64:row['path']=string(resource+0x10)
            result['models'].append(row)
        cur=u(cur+8)
    for m in re.finditer(rb'(?:eft/)?chr/(?:lan|rin|sir)/[0-9]{4}\.gmo\x00',b):
        addr=BASE+m.start();resource=addr-0x10
        if BASE<=resource<BASE+len(b)-0x50:result['resources'].append({'path':m.group()[:-1].decode(),'name_address':hex(addr),'candidate_resource':hex(resource),'words':[hex(u(resource+o)) for o in range(0,0x50,4)]})
    jsonwrite(folder/'OBJECT_MAP.json',result);print(json.dumps({'globals':result['globals'],'registered_models':len(result['models']),'body_equipment_models':[r for r in result['models'] if re.match(r'chr/(lan|rin|sir)/000[01]\.gmo',r.get('path',''))]},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
