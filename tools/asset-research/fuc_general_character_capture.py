from fuc_general_debugger import *
from fuc_general_function_probe import snap
import argparse,struct
p=argparse.ArgumentParser();p.add_argument('character',type=lambda x:int(x,0));p.add_argument('--folder',required=True);a=p.parse_args();out=BR/a.folder;out.mkdir(parents=True,exist_ok=True);d=BattleDebugger()
try:
 d.pause();rr=regs(d);rr['a0']=a.character;s=snap(d,rr,out,'capture',True);b=d.read(a.character,0x800);u=lambda o:struct.unpack_from('<I',b,o)[0];rows=[]
 for kind,off,num in [('FAN',0x44,64),('BPO',0x144,8),('AMO',0x164,8)]:
  for i in range(num):
   res=u(off+i*4)
   if 0x08800000<res<0x09fff000:
    rb=d.read(res,0x4c);payload=struct.unpack_from('<I',rb,0x34)[0];path=cstring(d,res+0x10);size=128 if kind!='FAN' else 2048
    if 0x08800000<payload<0x09fff000:(out/f'{kind}_{i:02d}.bin').write_bytes(d.read(payload,size));rows.append(dict(kind=kind,slot=i,resource=hex(res),payload=hex(payload),path=path))
 # Eight attachment records extend beyond the first 0x800 bytes.
 eb=d.read(a.character+0x5dc,8*0xc8);(out/'equipment_records.bin').write_bytes(eb)
 pb=d.read(u(0x40),0x100);(out/'player.bin').write_bytes(pb)
 bankptr,bankcount=struct.unpack_from('<2I',pb,0x2c);banks=[]
 if 0x08800000<bankptr<0x09fff000 and 0<bankcount<=16:
  ba=d.read(bankptr,bankcount*4);(out/'bank_array.bin').write_bytes(ba)
  for i,res in enumerate(struct.unpack('<'+'I'*bankcount,ba)):
   if 0x08800000<res<0x09fff000:
    rb=d.read(res,0x10);(out/f'bank_{i:02d}_header.bin').write_bytes(rb)
    count=struct.unpack_from('<H',rb,6)[0];table,size=struct.unpack_from('<2I',rb,8)
    item=dict(slot=i,runtime_data_base=hex(res),offset_slot_count=count,relocated_table=hex(table),size=size)
    if 0<count<4096 and 0x08800000<table<0x09fff000:(out/f'bank_{i:02d}_offsets.bin').write_bytes(d.read(table,count*4))
    banks.append(item)
 equipments=[]
 for i in range(8):
  rec=eb[i*0xc8:(i+1)*0xc8];m=struct.unpack_from('<I',rec,4)[0];item=dict(slot=i,flags=struct.unpack_from('<I',rec)[0],model=hex(m),equipment_bones=list(struct.unpack_from('<4i',rec,8)),body_bones=list(struct.unpack_from('<4i',rec,0x18)),local_translation=list(struct.unpack_from('<3f',rec,0x2c)),local_euler=list(struct.unpack_from('<3f',rec,0x60)),local_scale=list(struct.unpack_from('<3f',rec,0x94)))
  if 0x08800000<m<0x09fff000:
   mb=d.read(m,0x60);item['path']=cstring(d,struct.unpack_from('<I',mb,0x34)[0]+0x10);(out/f'equipment_{i:02d}_model.bin').write_bytes(mb)
  equipments.append(item)
 jsonwrite(out/'CHARACTER_RUNTIME.json',dict(character=hex(a.character),body=s['body_model'],model_path=s['model_path'],player=hex(u(0x40)),bank_array=hex(bankptr),bank_capacity=bankcount,banks=banks,equipment=equipments))
 jsonwrite(out/'TABLES.json',rows)
 print(s['model_path'],hex(a.character),s['body_model'],[(r['kind'],r['slot'],r['path']) for r in rows[:4]])
finally:d.close()
