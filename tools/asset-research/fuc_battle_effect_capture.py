"""Read a naturally selected effect context, its threads, models and owner. No RAM writes."""
from fuc_battle_debugger import *
import argparse
def valid(p):return 0x08800000<=p<0x09fff000
def effect_snapshot(d,p,out,label):
 out.mkdir(parents=True,exist_ok=True);b=d.read(p,0x98);(out/f'{label}_context.bin').write_bytes(b)
 def u(o):return struct.unpack_from('<I',b,o)[0]
 r=dict(pointer=hex(p),timestamp=now(),flags=hex(u(0)),state=u(4),owner=hex(u(8)),context_id=u(12),thread_count=u(0x38),model_count=u(0x64),bytecode_base=hex(u(0x74)),context_words=list(struct.unpack('<38I',b)),threads=[],models=[])
 for i in range(min(u(0x38),10)):
  t=u(0x10+4*i)
  if not valid(t):continue
  tb=d.read(t,0x84);(out/f'{label}_thread_{i}.bin').write_bytes(tb);r['threads'].append(dict(index=i,pointer=hex(t),words=list(struct.unpack('<33I',tb))))
 for i in range(min(u(0x64),10)):
  rec=u(0x3c+4*i)
  if not valid(rec):continue
  rb=d.read(rec,0xb0);(out/f'{label}_model_record_{i}.bin').write_bytes(rb);m=struct.unpack_from('<I',rb,4)[0]
  item=dict(index=i,record=hex(rec),record_words=list(struct.unpack('<44I',rb)),model=hex(m));r['models'].append(item)
  dc=struct.unpack_from('<I',rb,0xc)[0]
  item['node_commands']=[]
  for k in range(min(dc,12)):
   dp=struct.unpack_from('<I',rb,0x10+k*4)[0]
   if valid(dp):
    db=d.read(dp,0x3c);(out/f'{label}_model_{i}_node_command_{k}.bin').write_bytes(db);item['node_commands'].append(dict(pointer=hex(dp),words=list(struct.unpack('<15I',db))))
  if not valid(m):continue
  mb=d.read(m,0x340);(out/f'{label}_model_{i}.bin').write_bytes(mb);res=struct.unpack_from('<I',mb,0x34)[0];sdk=struct.unpack_from('<I',mb,0x38)[0];n=struct.unpack_from('<I',mb,0x58)[0]
  item.update(path=cstring(d,res+0x10),flags=hex(struct.unpack_from('<I',mb)[0]),node_count=n,resource=hex(res),sdk=hex(sdk))
  if 0<n<1000 and valid(sdk):
   sh=d.read(sdk,0x40);np=struct.unpack_from('<I',sh,0x18)[0];ptrs=struct.unpack('<'+'I'*n,d.read(np,n*4));item['sdk_nodes']=[hex(x) for x in ptrs]
   (out/f'{label}_model_{i}_sdk_nodes.bin').write_bytes(b''.join(d.read(x,0x180) for x in ptrs));d.dump(struct.unpack_from('<I',mb,0x5c)[0],n*0x140,out/f'{label}_model_{i}_runtime_nodes.bin')
 owner=u(8)
 if valid(owner):
  cb=d.read(owner,0x800);(out/f'{label}_owner.bin').write_bytes(cb);body,player=struct.unpack_from('<2I',cb,0x3c);r['owner_body']=hex(body);r['owner_player']=hex(player)
  if valid(body):
   bm=d.read(body,0x60);r['owner_model_path']=cstring(d,struct.unpack_from('<I',bm,0x34)[0]+0x10);bs=struct.unpack_from('<I',bm,0x38)[0];bn=struct.unpack_from('<I',bm,0x58)[0]
   if valid(bs) and 0<bn<1000:
    np=struct.unpack_from('<I',d.read(bs,0x1c),0x18)[0];ps=struct.unpack('<'+'I'*bn,d.read(np,bn*4));r['owner_sdk_nodes']=[hex(x) for x in ps];(out/f'{label}_owner_sdk_nodes.bin').write_bytes(b''.join(d.read(x,0x180) for x in ps))
  if valid(player):d.dump(player,0x100,out/f'{label}_owner_player.bin')
 base=u(0x74)
 if valid(base):d.dump(base,256,out/f'{label}_bytecode_prefix.bin')
 jsonwrite(out/f'{label}_effect.json',r);return r
def main():
 p=argparse.ArgumentParser();p.add_argument('pointer',type=lambda x:int(x,0));p.add_argument('--folder',required=True);p.add_argument('--label',default='snapshot');a=p.parse_args();d=BattleDebugger()
 try:d.pause();r=effect_snapshot(d,a.pointer,BR/a.folder,a.label);print(json.dumps({k:v for k,v in r.items() if k not in ('threads','models','context_words')}));print([(x.get('path'),x.get('flags')) for x in r['models']])
 finally:d.close()
if __name__=='__main__':main()
