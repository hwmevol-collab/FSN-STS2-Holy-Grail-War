"""Hash the previously observed SAS sample ranges and match preserved bank payloads."""
from fuc_battle_debugger import *
import numpy as np

def main():
 out=BR/'AudioSetVoiceNatural';d=BattleDebugger();rows=[]
 try:
  d.pause()
  for f in sorted(out.glob('*_entry.json')):
   j=readjson(f);r=j['registers'];p=r['a1'];size=r['a2'];assert 0<size<1000000
   data=d.read(p,size);prefix=(out/f'{f.stem}_a1.bin').read_bytes();assert data[:len(prefix)]==prefix,'sample memory changed since natural capture'
   path=out/f'{f.stem}_adpcm.bin';path.write_bytes(data);rows.append(dict(sample=f.stem,voice_slot=r['a0'],pointer=hex(p),size=size,loop=r['a3'],sha256=sha(path),actor=j['actor'],prefix_still_equal=True))
 finally:d.close()
 banks=readjson(W/'fuc/Europe/SOUND_BANK_INDEX.json')
 for r in rows:
  hits=[x for x in banks if x.get('payload_sha256')==r['sha256'] or x.get('sha256')==r['sha256'] or x.get('payload_hash')==r['sha256']]
  r['matches']=hits
 jsonwrite(out/'ADPCM_MATCHES.json',rows);print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
