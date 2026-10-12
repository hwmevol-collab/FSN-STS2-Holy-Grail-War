from fuc_general_debugger import *
from fuc_general_effect_capture import effect_snapshot
import argparse
p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();out=BR/a.folder;e=readjson(out/'000_entry.json');d=BattleDebugger()
try:
 d.pause();dest=e['registers']['a0']-0x30;d.dump(dest,64,out/'external_matrix.bin');r=effect_snapshot(d,e['registers']['s0'],out,'verified');print('matrix',hex(dest),'owner',r.get('owner_model_path'),'base',r['bytecode_base']);d.dump(int(r['bytecode_base'],16),30608,out/'runtime_seq.bin')
finally:d.close()
