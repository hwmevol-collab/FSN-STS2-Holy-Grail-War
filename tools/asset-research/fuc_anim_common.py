"""Animation research uses existing assets; never runs extraction/index allocation."""
from fuc_common import *
EU=L/'FateUnlimitedCodesPortable_Europe'
AMD=EU/'Metadata/AnimationValidation'
AW=W/'fuc/AnimationValidation'
AB=W/'backups/fuc-animation-pre-validation'
def frozen():
    p=AB/'BASELINE.json'
    if not p.exists():raise RuntimeError('Animation frozen baseline required')
    b=readjson(p)
    if b['asset_total']!=268504 or b['fuc_asset_count']!=21899:raise RuntimeError('Unexpected frozen asset count')
    return b
