"""Build a body/equipment-only viewer from preserved GLBs and explicit runtime attachment evidence."""
from fuc_battle_common import *
import numpy as np
def main():
 battle_frozen();out=EU/'Converted/BattleScenes/lan_attachment';out.mkdir(parents=True,exist_ok=True)
 rows=readjson(BR/'Snapshots/PracticeInitial/EQUIPMENT_ANALYSIS.json')
 ref={'status':'confirmed_runtime_attachment_subset','body_asset':'FSN248769','equipment_asset':'FSN248770','body_bone_id':153,'body_gmo_ordinal':32,'body_glb_node':42,'equipment_bone_id':0,'equipment_gmo_ordinal':1,'equipment_glb_node':2,'frames':[],'notes':'Three frozen validated body clips with a confirmed constant attachment rule. No effect/audio/gameplay choreography is supplied.'}
 ref['frames'].append(dict(label='PracticeInitial',parent_matrix=np.asarray(rows['attachment_matrix']).T.reshape(-1).tolist(),equipment_world=[np.asarray(x['world']).T.reshape(-1).tolist() for x in rows['equipment_nodes']]))
 for i in range(2):
  p=BR/'WeaponParentMatrixCopy';src=list(struct.unpack('<16f',(p/f'{i:03d}_entry_a1.bin').read_bytes()[:64]));dst=list(struct.unpack('<16f',(p/f'{i:03d}_post_a0.bin').read_bytes()[:64]));assert src==dst
  ref['frames'].append(dict(label=f'WeaponParentMatrixCopy/{i:03d}',parent_matrix=src,attachment_matrix=dst))
 jsonwrite(out/'attachment_reference.json',ref)
 html=pathlib.Path(__file__).with_name('fuc_battle_viewer.html').read_text(encoding='utf-8');(out/'index.html').write_text(html,encoding='utf-8');log('EQUIPMENT VIEWER',out)
if __name__=='__main__':main()
