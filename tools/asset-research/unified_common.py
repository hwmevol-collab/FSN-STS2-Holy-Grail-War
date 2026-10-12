"""FSN semantic sidecar: source files are read-only; identifiers are content anchored."""
from pathlib import Path
import csv, json, hashlib, sqlite3, unicodedata, datetime, os
L = Path(r'E:\FSN_MASTER_ASSET_LIBRARY')
W = Path(r'E:\FSN_MASTER_ASSET_WORK\unified-semantic')
S = L/'SemanticCatalog'
B = Path(r'E:\FSN_MASTER_ASSET_WORK\backups\unified-semantic-pre')
DB = S/'Database/FSN_SEMANTIC.sqlite'
F = L/'FateUnlimitedCodesPortable_Europe/Metadata'
O = L/'ReferenceBooks/Metadata'
A = L/'AnimationReferences/Metadata'
FAMILIES = ['Original','Remastered','HollowAtaraxia','FateUnlimitedCodesPortable_Europe','OfficialMaterial','AnimationReference']
TYPES = ['Character','CharacterVariant','Weapon','NoblePhantasm','Magecraft','Ability','Item','Location','Faction','Organization','Route','Event','Concept','Term','Move','Command','Costume','MediaWork','Other']
PREDICATES = ['has_asset','appears_in','mentioned_in','depicted_in','candidate_depiction','uses_weapon','has_noble_phantasm','uses_magecraft','wears_costume','associated_with','has_move','has_command','move_uses_animation','move_uses_effect','move_uses_audio','spoken_by','located_at','belongs_to','related_to','variant_of','higher_resolution_candidate','same_visual_candidate','exact_payload','has_equipment_model','script_uses_asset','has_replay','has_ui_move_label','has_route_script','has_observed_voice_sample']
SCOPES = {'FSN_CORE':'Original / Remastered / official FSN setting references; relevance, not canon.', 'FSN_ADAPTATION':'Local works explicitly identified as FSN adaptations or FSN game opening references.', 'FSN_DIRECT_EXTENSION':'FHA / FUC and their direct local references.', 'FATE_RELATED_REFERENCE':'Explicitly identified related Fate works; no shared character identity inferred.', 'PARODY_COMEDY':'Explicit Carnival parody identity.', 'DAILY_LIFE_REFERENCE':'Emiya Gohan local work identity; daily-life reference.', 'OTHER':'Insufficient scope evidence or mixed event material.'}
WORK_SCOPES = {'CARNIVAL_PHANTASM':'PARODY_COMEDY','CARNIVAL_SPECIAL_SEASON':'PARODY_COMEDY','EMIYA_GOHAN':'DAILY_LIFE_REFERENCE','FATE_ZERO':'FATE_RELATED_REFERENCE','FATE_PROTOTYPE':'FATE_RELATED_REFERENCE','FHA_VITA_OP':'FSN_DIRECT_EXTENSION','CURTAIN_RAISER':'OTHER','SHINJI_DIARY':'OTHER','TMFES':'OTHER'}
def now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def dump(p, obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:
        yield from csv.DictReader(f)
def js(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def norm(x):
    x=unicodedata.normalize('NFKC',str(x or '')).casefold()
    out=[];latin=False
    for c in unicodedata.normalize('NFD',x):
        if unicodedata.category(c).startswith('M'):
            if not latin:out.append(c)
        else:
            out.append(c);latin='LATIN' in unicodedata.name(c,'')
    return unicodedata.normalize('NFC',''.join(out))
def ident(prefix,*parts): return prefix+'-'+hashlib.sha256(js(parts).encode('utf-8')).hexdigest()[:24].upper()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for buf in iter(lambda:f.read(4*1024*1024),b''):h.update(buf)
    return h.hexdigest()
def ro(p): return sqlite3.connect(Path(p).as_uri()+'?mode=ro',uri=True)
def family(version):
    if version in FAMILIES:return version
    if version.startswith('CompleteMaterial') or version.startswith('CM_') or version in ('SideMaterial','SIDE'):return 'OfficialMaterial'
    return 'AnimationReference'
def scope(version):
    f=family(version)
    if f=='AnimationReference':return WORK_SCOPES.get(version,'FSN_ADAPTATION')
    if f in ('HollowAtaraxia','FateUnlimitedCodesPortable_Europe'):return 'FSN_DIRECT_EXTENSION'
    return 'FSN_CORE'
def grade(status,kind):
    s=str(status).lower()
    if s=='rejected':return 0
    if 'candidate' in s:return 1
    if 'unknown' in s or s in ('unreviewed','unresolved',''):return 0
    if 'runtime' in s or kind in ('runtime_confirmed','exact_hash'):return 5
    if 'ui' in s or kind in ('ui_confirmed','manual_visual','manual_review'):return 4
    if 'table' in s or kind in ('script_reference','table_confirmed'):return 3
    if 'section' in s or 'alias' in kind or 'search' in s:return 2
    if 'text' in s or kind in ('subtitle_exact','source_text_exact','official_page_text'):return 4
    return 2
def display_status(status,predicate=''):
    s=str(status).lower()
    if s=='rejected':return 'Rejected'
    if 'candidate' in s:return 'Strong Candidate' if 'strong' in s else 'Candidate'
    if 'unknown' in s or s in ('unreviewed','unresolved',''):return 'Unknown'
    if predicate=='mentioned_in' or 'mention' in s or 'text_reference' in s:return 'Mention Only'
    return 'Confirmed'
