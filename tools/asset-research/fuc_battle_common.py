"""Battle-runtime research is an additive layer over the frozen animation chain."""
from fuc_anim_common import *
BR=W/'fuc/BattleRuntimeMapping'
BMD=EU/'Metadata/BattleRuntimeMapping'
BB=W/'backups/fuc-battle-runtime-pre'
def battle_frozen():
    p=BB/'BASELINE.json'
    if not p.exists():raise RuntimeError('Battle golden baseline must be frozen first')
    b=readjson(p)
    assert b['asset_total']==268504 and b['max_asset_id']=='FSN268504'
    assert b['golden']['models']==3 and b['golden']['clips']==9
    return b
