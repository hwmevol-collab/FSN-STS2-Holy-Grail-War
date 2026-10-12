"""Additive semantic sidecars. Existing extraction and runtime results are read-only."""
from fuc_anim_common import *
SW=W/'fuc/SemanticMapping'
SM=EU/'Metadata/SemanticMapping'
SB=W/'backups/fuc-semantic-mapping-pre'
ELF=EU/'Converted/Executable/EBOOT_DECRYPTED.bin'
def semantic_frozen():
    b=readjson(SB/'BASELINE.json')
    assert b['asset_total']==268504 and b['max_asset_id']=='FSN268504'
    return b
