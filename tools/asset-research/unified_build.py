"""Consume frozen indexes and decoded text only. No extraction, OCR, detector or runtime."""
from unified_common import *
import re, collections, shutil, sys

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS revisions(revision TEXT PRIMARY KEY,input_fingerprint TEXT,created_at TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS entities(entity_id TEXT PRIMARY KEY,entity_type TEXT,preferred_label TEXT,preferred_language TEXT,scope TEXT,status TEXT,created_from TEXT,notes TEXT);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,source_family TEXT,source_version TEXT,evidence_type TEXT,source_id TEXT,source_path TEXT,source_locator TEXT,raw_text TEXT,normalized_text TEXT,language TEXT,confidence TEXT,status TEXT,provenance TEXT,notes TEXT,semantic_strength INTEGER,original_evidence_type TEXT,original_status TEXT,revision TEXT REFERENCES revisions(revision));
CREATE TABLE IF NOT EXISTS aliases(alias_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),alias TEXT,language TEXT,alias_type TEXT,source TEXT,evidence_id TEXT REFERENCES evidence(evidence_id),status TEXT,normalized_alias TEXT);
CREATE TABLE IF NOT EXISTS source_subjects(semantic_subject_id TEXT PRIMARY KEY,subject_type TEXT,native_id TEXT,source_family TEXT,source_version TEXT,scope TEXT,label TEXT,source_path TEXT,thumbnail TEXT,media_asset_id TEXT,page_asset_id TEXT,locator TEXT,payload TEXT,UNIQUE(subject_type,native_id,source_version));
CREATE TABLE IF NOT EXISTS relations(relation_id TEXT PRIMARY KEY,subject_entity_id TEXT REFERENCES entities(entity_id),subject_subject_id TEXT REFERENCES source_subjects(semantic_subject_id),predicate TEXT,object_type TEXT,object_id TEXT,object_subject_id TEXT REFERENCES source_subjects(semantic_subject_id),object_entity_id TEXT REFERENCES entities(entity_id),status TEXT,evidence_count INTEGER,best_evidence_grade INTEGER,notes TEXT,CHECK((subject_entity_id IS NULL)!=(subject_subject_id IS NULL)),CHECK((object_subject_id IS NULL)!=(object_entity_id IS NULL)));
CREATE TABLE IF NOT EXISTS relation_evidence(relation_id TEXT REFERENCES relations(relation_id),evidence_id TEXT REFERENCES evidence(evidence_id),PRIMARY KEY(relation_id,evidence_id));
CREATE TABLE IF NOT EXISTS relation_history(history_id TEXT PRIMARY KEY,relation_id TEXT REFERENCES relations(relation_id),revision TEXT REFERENCES revisions(revision),status TEXT,evidence_id TEXT REFERENCES evidence(evidence_id));
CREATE TABLE IF NOT EXISTS entity_asset_links(link_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),asset_id TEXT,role TEXT,status TEXT,evidence_id TEXT REFERENCES evidence(evidence_id),source_version TEXT,quality_metadata TEXT,notes TEXT,subject_id TEXT REFERENCES source_subjects(semantic_subject_id));
CREATE TABLE IF NOT EXISTS entity_shot_links(link_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),shot_id TEXT,media_asset_id TEXT,role TEXT,status TEXT,evidence_id TEXT REFERENCES evidence(evidence_id),subject_id TEXT REFERENCES source_subjects(semantic_subject_id),notes TEXT);
CREATE TABLE IF NOT EXISTS entity_page_links(link_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),page_id TEXT,page_asset_id TEXT,role TEXT,status TEXT,evidence_id TEXT REFERENCES evidence(evidence_id),subject_id TEXT REFERENCES source_subjects(semantic_subject_id),notes TEXT);
CREATE TABLE IF NOT EXISTS scopes(scope TEXT PRIMARY KEY,definition TEXT);
CREATE TABLE IF NOT EXISTS usage_candidates(usage_candidate_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),usage_type TEXT,source_id TEXT,source_type TEXT,subject_id TEXT REFERENCES source_subjects(semantic_subject_id),candidate_rank REAL,reason TEXT,evidence_status TEXT,technical_quality TEXT,notes TEXT,relation_id TEXT REFERENCES relations(relation_id));
CREATE TABLE IF NOT EXISTS review_queue(review_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),subject_id TEXT REFERENCES source_subjects(semantic_subject_id),source_family TEXT,status TEXT,priority TEXT,reason TEXT,source_path TEXT,source_locator TEXT,original_record TEXT);
CREATE TABLE IF NOT EXISTS conflicts(conflict_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),conflict_type TEXT,status TEXT,source TEXT,details TEXT);
CREATE TABLE IF NOT EXISTS cross_source_links(cross_source_link_id TEXT PRIMARY KEY,entity_id TEXT REFERENCES entities(entity_id),source_family TEXT,source_key TEXT,evidence_id TEXT REFERENCES evidence(evidence_id),status TEXT,notes TEXT);
CREATE INDEX IF NOT EXISTS aliases_norm ON aliases(normalized_alias);
CREATE INDEX IF NOT EXISTS relations_entity ON relations(subject_entity_id);
CREATE INDEX IF NOT EXISTS relations_object ON relations(object_subject_id);
CREATE INDEX IF NOT EXISTS relations_source ON relations(subject_subject_id);
CREATE INDEX IF NOT EXISTS subjects_native ON source_subjects(native_id);
CREATE INDEX IF NOT EXISTS usage_entity ON usage_candidates(entity_id,usage_type);
CREATE INDEX IF NOT EXISTS usage_relation ON usage_candidates(relation_id,usage_type);
CREATE INDEX IF NOT EXISTS evidence_source ON evidence(source_family,source_id);
CREATE VIRTUAL TABLE IF NOT EXISTS entity_fts USING fts5(entity_id UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS alias_fts USING fts5(alias_id UNINDEXED,entity_id UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_text_fts USING fts5(evidence_id UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS source_text_fts USING fts5(subject_id UNINDEXED,text,tokenize='unicode61 remove_diacritics 2');
'''

class Build:
    def __init__(self,revision='v1'):
        for p in [W,S/'Metadata',S/'Database',S/'Browser',S/'Reports',S/'Exports',S/'Revisions']:p.mkdir(parents=True,exist_ok=True)
        self.revision=revision; self.registry_path=S/'Metadata/IMMUTABLE_ID_REGISTRY.json'
        self.registry=read(self.registry_path) if self.registry_path.exists() else {'entity_keys':{},'created_at':now(),'algorithm':'SHA256 source-key immutable mapping; 96-bit opaque identifiers'}
        self.stage=W/'FSN_SEMANTIC.build.sqlite'
        if DB.exists():shutil.copy2(DB,self.stage)
        elif self.stage.exists():self.stage.unlink()
        self.c=sqlite3.connect(self.stage);self.c.row_factory=sqlite3.Row;self.c.executescript(SCHEMA)
        self.c.execute('pragma synchronous=NORMAL');self.c.execute('pragma temp_store=MEMORY');self.c.execute('pragma cache_size=-262144')
        b=read(B/'BASELINE.json');inputs=[(r['path'],sha(r['path'])) for r in b['metadata_files']]
        manual=S/'Metadata/MANUAL_REVIEW_ADDITIONS.jsonl'
        if manual.exists() and manual.stat().st_size:inputs.append((str(manual),sha(manual)))
        fingerprint=ident('INPUT',inputs)
        existing=self.c.execute('select input_fingerprint from revisions where revision=?',(revision,)).fetchone()
        if existing and existing[0]!=fingerprint:raise RuntimeError('Frozen inputs changed: use a new revision; preserve previous revision.')
        self.c.execute('insert or ignore into revisions values(?,?,?,?)',(revision,fingerprint,now(),'Read-only source-index refresh; absent historical records retained.'))
        self.c.executemany('insert or ignore into scopes values(?,?)',SCOPES.items())
        self.asset={};self.subjects={};self.entities={};self.lookup=collections.defaultdict(set);self.source_codes={};self.stats={};self.skipped=collections.Counter()
        for r in self.c.execute('select * from entities'):self.entities[norm(r['preferred_label'])]=r['entity_id']
        for r in self.c.execute('select entity_id,normalized_alias from aliases'):self.lookup[r['normalized_alias']].add(r['entity_id'])
    def ev(self,path,key,record,version,kind,status,raw=None,language='',confidence='',notes=''):
        raw=js(record) if raw is None else str(raw);eid=ident('EVD',str(path),key,record,kind,status)
        provenance=js({'adapter':'unified_build.py','source_index':str(path),'record_key':key,'record_sha256':hashlib.sha256(js(record).encode()).hexdigest(),'record':record,'source_era':version if version=='SideMaterial' else record.get('book_id',version),'revision':self.revision})
        self.c.execute('insert or ignore into evidence values('+','.join('?'*18)+')',(eid,family(version),version,kind,str(key),str(path),js({'record_key':key,'locator':record.get('source_region',record.get('line',record.get('timecode',record.get('evidence',''))))}),raw,norm(raw),language,str(confidence or ''),status,provenance,notes,grade(status,kind),str(record.get('evidence_type',kind)),status,self.revision));return eid
    def entity(self,label,etype,path,key,status='source_indexed',sc='FSN_CORE',language=''):
        n=norm(label);regkey='seed:'+etype+':'+n
        # Labels resolve through existing alias evidence. Ambiguous aliases are never silently merged.
        choices={e for e in self.lookup[n] if self.c.execute('select entity_type from entities where entity_id=?',(e,)).fetchone()[0]==etype}
        if len(choices)==1:return next(iter(choices))
        eid=self.registry['entity_keys'].setdefault(regkey,ident('ENT',str(path),str(key),etype))
        self.c.execute('insert or ignore into entities values(?,?,?,?,?,?,?,?)',(eid,etype,label,language or ('ja' if re.search('[\u3040-\u30ff\u4e00-\u9fff]',label) else 'en'),sc,status,str(path)+'#'+str(key),'Source-index entity. Canonical display labels are separate from raw-source aliases.'))
        self.entities[n]=eid;self.lookup[n].add(eid);return eid
    def alias(self,eid,label,evidence,path,status,atype='source_spelling',language=''):
        if not label:return
        aid=ident('ALS',eid,label,str(path),evidence,atype)
        self.c.execute('insert or ignore into aliases values(?,?,?,?,?,?,?,?,?)',(aid,eid,label,language or ('ja' if re.search('[\u3040-\u30ff]',label) else 'und'),atype,str(path),evidence,status,norm(label)))
        self.lookup[norm(label)].add(eid)
        self.c.execute('insert or ignore into cross_source_links values(?,?,?,?,?,?,?)',(ident('XSL',eid,evidence,label),eid,self.c.execute('select source_family from evidence where evidence_id=?',(evidence,)).fetchone()[0],label,evidence,status,'Exact existing alias/code mapping; no inferred visual identity.'))
    def resolve(self,label):
        choices=self.lookup.get(norm(label),set())
        return next(iter(choices)) if len(choices)==1 else None
    def subj(self,typ,native,version,label,path='',thumb='',media='',pageasset='',locator='',payload=None):
        sid=ident('SUB',typ,native,version);self.subjects[(typ,native,version)]=sid
        self.c.execute('insert or ignore into source_subjects values(?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid,typ,native,family(version),version,scope(version),label,path or '',thumb or '',media or '',pageasset or '',str(locator),js(payload or {})));return sid
    def relation(self,sub,pred,obj,evidence,status,notes='',entity=True,objentity=False):
        if not sub or not obj:self.skipped['unresolved_relation']+=1;return None
        target=self.c.execute('select native_id,subject_type from source_subjects where semantic_subject_id=?',(obj,)).fetchone() if not objentity else None
        oid=obj if objentity else target['native_id'];otype='entity' if objentity else target['subject_type']
        rid=ident('REL',sub,pred,obj);g=self.c.execute('select semantic_strength from evidence where evidence_id=?',(evidence,)).fetchone()[0]
        self.c.execute('insert or ignore into relations values(?,?,?,?,?,?,?,?,?,?,?,?)',(rid,sub if entity else None,None if entity else sub,pred,otype,oid,None if objentity else obj,obj if objentity else None,status,0,g,notes))
        new_evidence=self.c.execute('insert or ignore into relation_evidence values(?,?)',(rid,evidence)).rowcount
        if new_evidence:self.c.execute('insert or ignore into relation_history values(?,?,?,?,?)',(ident('HIS',rid,self.revision,evidence,status),rid,self.revision,status,evidence))
        return rid
    def assetlink(self,eid,aid,evidence,status,role='',predicate='has_asset',notes=''):
        if aid not in self.asset:self.skipped['unknown_asset_reference']+=1;return
        a=self.asset[aid];role=role or self.role(a);sid=self.subjects[('asset',aid,a['source_version'])]
        rid=self.relation(eid,predicate,sid,evidence,status,notes)
        self.c.execute('insert or ignore into entity_asset_links values(?,?,?,?,?,?,?,?,?,?)',(ident('LNK',eid,aid,evidence,role),eid,aid,role,status,evidence,a['source_version'],js(a),notes,sid));return rid
    def role(self,a):
        x=((a.get('asset_kind') or '')+' '+(a.get('category') or '')+' '+(a.get('detected_format') or '')).lower()
        if 'anim' in x or 'mot' in x:return 'animation'
        if 'voice' in x:return 'voice'
        if 'bgm' in x:return 'BGM'
        if 'sound' in x or 'audio' in x:return 'sound'
        if 'effect' in x or 'fan' in x:return 'effect'
        if 'model' in x or 'gmo' in x:return 'model'
        if 'script' in x or 'text' in x:return 'script'
        if 'background' in x:return 'background'
        if 'character' in x or 'foreground' in x:return 'portrait'
        if 'cg' in x:return 'CG'
        if a.get('width') and a.get('height'):return 'image'
        return 'other'
    def review(self,path,key,r,version,status='candidate',sid=None,eid=None,reason=''):
        self.c.execute('insert or ignore into review_queue values(?,?,?,?,?,?,?,?,?,?)',(ident('REV',str(path),key,r),eid,sid,family(version),status,str(r.get('priority','')),reason or r.get('notes','') or js(r),str(path),str(key),js(r)))
    def seeds(self):
        tagtype={}
        for name,field,typ in [('CHARACTER','tag','Character'),('NOBLE_PHANTASM','name','NoblePhantasm'),('MAGIC','name','Magecraft'),('TERM','term','Term')]:
            for r in rows(O/f'OFFICIAL_MATERIAL_{name}_INDEX.csv'):tagtype.setdefault(norm(r[field]),typ)
        for r in rows(O/'OFFICIAL_MATERIAL_WEAPON_INDEX.csv'):
            if 'applicability not asserted' not in r.get('classification',''):tagtype[norm(r['weapon_name'])]='Weapon'
        # Location / organization labels are typed only from local tag identity; otherwise retain Term.
        for i,r in enumerate(rows(O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv'),1):
            pages=json.loads(r['source_pages']);supported=pages or r['status']!='search_alias_only'
            if not supported:continue
            label=r['entity'];eid=self.entity(label,tagtype.get(norm(label),'Term'),O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv',label)
            ev=self.ev(O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv',ident('ROW',r),r,'OfficialMaterial','source_text_alias',r['status'])
            self.alias(eid,label,ev,O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv',r['status'],'search_alias')
            self.alias(eid,r['alias'],ev,O/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv',r['status'],'source_spelling' if pages else 'search_alias')
        hitlabels={norm(r['canonical_alias']) for r in rows(A/'ANIMATION_TERM_HITS.csv')}
        for r in rows(A/'ANIMATION_SEARCH_VOCABULARY.csv'):
            label=r['canonical_alias'];eid=self.resolve(label)
            if not eid and norm(label) not in hitlabels:continue
            if not eid:eid=self.entity(label,'Character' if r['tag_type']=='character_mentioned' else 'Term',A/'ANIMATION_SEARCH_VOCABULARY.csv',label,status='text_vocabulary_only')
            ev=self.ev(A/'ANIMATION_SEARCH_VOCABULARY.csv',ident('ROW',r),r,'AnimationReference','source_text_alias',r['vocabulary_status'])
            self.alias(eid,r['matched_term'],ev,A/'ANIMATION_SEARCH_VOCABULARY.csv',r['vocabulary_status'],'search_alias')
        for r in rows(F/'SemanticMapping/FUC_CHARACTER_CODE_MAP.csv'):
            if r['internal_code']=='cmn':continue
            eid=self.resolve(r['display_name']) or self.entity(r['display_name'],'CharacterVariant' if r['internal_name']=='SABER_ALTER' else 'Character',F/'SemanticMapping/FUC_CHARACTER_CODE_MAP.csv',r['character_id'],sc='FSN_DIRECT_EXTENSION')
            kind='ui_confirmed' if r['display_name_source']=='actual_game_UI_and_runtime' else 'table_confirmed'
            ev=self.ev(F/'SemanticMapping/FUC_CHARACTER_CODE_MAP.csv',r['character_id'],r,'FateUnlimitedCodesPortable_Europe',kind,r['status'])
            for label in [r['display_name'],r['internal_name'],r['internal_code']]:self.alias(eid,label,ev,F/'SemanticMapping/FUC_CHARACTER_CODE_MAP.csv',r['status'],'internal_code' if label==r['internal_code'] else 'source_spelling')
            self.source_codes[r['internal_code']]=eid
        for r in rows(L/'HollowAtaraxia/Metadata/CHARACTER_VOICE_CODES.csv'):
            if r['character']=='unknown' or 'と' in r['original_character']:continue
            eid=self.resolve(r['original_character']) or self.resolve(r['character'])
            if not eid and '/' in r['character']:
                # Slash components are explicit names in the existing dictionary mapping, not encyclopedia guesses.
                hits={self.resolve(x.strip()) for x in r['character'].split('/')}-{None}
                eid=next(iter(hits)) if len(hits)==1 else None
            if not eid:eid=self.entity(r['original_character'],'Other',L/'HollowAtaraxia/Metadata/CHARACTER_VOICE_CODES.csv',r['code'],status='source_local_speaker_label',sc='FSN_DIRECT_EXTENSION')
            ev=self.ev(L/'HollowAtaraxia/Metadata/CHARACTER_VOICE_CODES.csv',r['code'],r,'HollowAtaraxia','table_confirmed','confirmed_dictionary_mapping')
            for label in [r['original_character'],r['character']]:self.alias(eid,label,ev,L/'HollowAtaraxia/Metadata/CHARACTER_VOICE_CODES.csv','confirmed_dictionary_mapping','source_spelling')
            self.source_codes['FHA:'+r['code']]=eid
        self.c.commit();print('Entity and alias seeds',self.c.execute('select count(*) from entities').fetchone()[0],flush=True)
    def subjects(self):pass
    def import_subjects(self):
        c=ro(L/'Metadata/ASSET_CATALOG.sqlite');c.row_factory=sqlite3.Row
        fields=['asset_id','source_version','filename','source_logical_path','category','asset_kind','detected_format','character','tag_evidence','character_evidence','character_code','route','converted_path','decrypted_path','extracted_path','thumbnail_path','width','height','duration','alpha','codec','metadata_path']
        for r in c.execute('select '+','.join(fields)+' from assets'):
            a={k:(v if v is not None else '') for k,v in dict(r).items()};self.asset[a['asset_id']]=a
            path=a['converted_path'] or a['decrypted_path'] or a['extracted_path']
            self.subj('asset',a['asset_id'],a['source_version'],a['filename'],path,a['thumbnail_path'],payload=a)
        c.close()
        self.pages={}
        for r in rows(O/'OFFICIAL_MATERIAL_PAGE_INDEX.csv'):
            self.pages[r['page_id']]=r
            self.subj('page',r['page_id'],r['book_id'],r['book_title']+' / '+r['page_id'],r['page_path'],r['thumbnail'],pageasset=r['page_asset_id'],locator=r['scan_page'],payload=r)
        media={r['media_asset_id']:r for r in rows(A/'ANIMATION_MEDIA_INDEX.csv')};self.shots={}
        for r in rows(A/'ANIMATION_SHOT_INDEX.csv'):
            self.shots[r['shot_id']]=r;m=media[r['media_asset_id']]
            payload=dict(r,source_path=m['source_path'],source_filename=m['filename'],width=m['width'],height=m['height'],codec=m['codec'],episode_label=m['episode_label'])
            self.subj('shot',r['shot_id'],r['work_id'],r['work_id']+' / '+r['start_time'],m['source_path'],r['thumbnail'],media=r['media_asset_id'],locator=r['start_time'],payload=payload)
        for r in rows(A/'ANIMATION_SUBTITLE_LINES.csv'):
            m=media[r['media_asset_id']];self.subj('subtitle',r['line_id'],m['work_id'],r['plain_text'],str(A/'ANIMATION_SUBTITLE_LINES.csv'),media=r['media_asset_id'],locator=r['start_time'],payload=r)
        for r in rows(A/'ANIMATION_WORK_INDEX.csv'):
            eid=self.entity(r['canonical_local_title'],'MediaWork',A/'ANIMATION_WORK_INDEX.csv',r['work_id'],sc=scope(r['work_id']))
            ev=self.ev(A/'ANIMATION_WORK_INDEX.csv',r['work_id'],r,r['work_id'],'source_path',r['status']);self.alias(eid,r['work_id'],ev,A/'ANIMATION_WORK_INDEX.csv',r['status'],'internal_code')
        self.c.commit();print('Native asset/page/shot/subtitle subjects registered',flush=True)
    def official(self):
        p=O/'OFFICIAL_MATERIAL_TAG_EVIDENCE.csv'
        for r in rows(p):
            if r['tag_type'] not in ('character','weapon','np','magic','term'):continue
            eid=self.resolve(r['tag']);page=self.pages.get(r['page_id'])
            if not eid or not page:self.skipped['official_unresolved_tag']+=1;continue
            sid=self.subjects[('page',r['page_id'],page['book_id'])];ev=self.ev(p,ident('ROW',r),r,page['book_id'],'official_page_text' if r['evidence_type']!='toc_context' else 'official_page_section',r['status'],raw=r['source_text'],language='ja',confidence=r['confidence'],notes='Text/section reference only; visual depiction not established.')
            self.relation(eid,'mentioned_in',sid,ev,r['status'],'Printed/OCR textual reference only. SideMaterial historical text preserved.')
            self.c.execute('insert or ignore into entity_page_links values(?,?,?,?,?,?,?,?,?)',(ident('PGL',eid,sid,ev),eid,r['page_id'],page['page_asset_id'],'text_mention',r['status'],ev,sid,'No visual assertion.'))
            if 'candidate' in r['status']:self.review(p,ident('ROW',r),r,page['book_id'],r['status'],sid,eid,'Review OCR/name ambiguity on existing page.')
        self.c.commit();print('Official references imported without depiction inference',flush=True)
    def animation(self):
        p=A/'ANIMATION_TERM_HITS.csv'
        for r in rows(p):
            eid=self.resolve(r['canonical_alias']);shot=self.shots.get(r['shot_id'])
            if not eid or not shot:self.skipped['animation_unresolved_hit']+=1;continue
            sid=self.subjects[('shot',r['shot_id'],shot['work_id'])]
            ev=self.ev(p,r['hit_id'],r,shot['work_id'],'subtitle_exact' if r['evidence_type']=='subtitle_exact' else 'source_text_alias',r['status'],raw=r['raw_subtitle'],language=r['language'],notes='Original '+r['evidence_type']+'; name/class referent may be ambiguous in related works. No presence/action assertion.')
            self.relation(eid,'mentioned_in',sid,ev,r['status'],'Subtitle mention only; vocabulary matches do not establish on-screen identity.')
            self.c.execute('insert or ignore into entity_shot_links values(?,?,?,?,?,?,?,?,?)',(ident('SHL',eid,sid,ev),eid,r['shot_id'],r['media_asset_id'],'subtitle_mention',r['status'],ev,sid,'No depicted character/action assertion.'))
            sub=self.subjects.get(('subtitle',r['subtitle_line_id'],shot['work_id']))
            if sub:self.relation(sid,'has_subtitle_mention',sub,ev,r['status'],entity=False)
        p=A/'ANIMATION_REVIEW_QUEUE.csv'
        for r in rows(p):
            sid=self.subjects.get(('shot',r['reference_id'],r['work_id']))
            self.review(p,r['reference_id'],r,r['work_id'],r['status'],sid,reason=r['reasons']+'; motion remains technical feature, not confirmed Battle/Attack/NP.')
        self.c.commit();print('Animation text hits and on-demand review queue imported',flush=True)
    def games(self):
        for a in self.asset.values():
            if a['source_version']!='HollowAtaraxia' or a['character'] in ('unknown','Unknown',''):continue
            eid=self.resolve(a['character'])
            if not eid or not a['tag_evidence']:continue
            p=L/'HollowAtaraxia/Metadata/TAG_EVIDENCE.csv'
            ev=self.ev(p,a['asset_id'],a,'HollowAtaraxia','source_filename','confirmed_filename_reference',raw=a['filename']+'\n'+a['tag_evidence'])
            self.assetlink(eid,a['asset_id'],ev,'confirmed_filename_reference',notes='Reuse existing dictionary/explicit filename convention. Asset association; no new visual classification.')
        p=L/'Metadata/VOICE_DIALOGUE_MAPPING.csv'
        for r in rows(p):
            a=self.asset.get(r['voice_asset_id']);eid=self.resolve(r['speaker'])
            if not a or not eid or not r['speaker'] or not r['mapping_evidence']:continue
            # Emotion-only speaker fields and empty speakers remain unlinked; no listening inference.
            ev=self.ev(p,ident('ROW',r),r,a['source_version'],'script_reference','confirmed_script_speaker',raw=r['speaker']+'\n'+r['dialogue'],language=r['locale'])
            self.assetlink(eid,a['asset_id'],ev,'confirmed_script_speaker','voice',notes=r['mapping_evidence'])
        # Existing decoded script text is searchable exact mention evidence, never a depiction claim.
        aliases={}
        for n,ids in self.lookup.items():
            if len(ids)!=1 or len(n)<2:continue
            eid=next(iter(ids));etype=self.c.execute('select entity_type from entities where entity_id=?',(eid,)).fetchone()[0]
            if etype in ('MediaWork','Move','Command'):continue
            if re.fullmatch('[a-z0-9_]{1,3}',n):continue
            aliases[n]=eid
        pattern=re.compile('|'.join(re.escape(n) if re.search('[^a-z0-9 _-]',n) else r'(?<!\w)'+re.escape(n)+r'(?!\w)' for n in sorted(aliases,key=len,reverse=True)))
        p=L/'Metadata/SCRIPT_INDEX.csv';scripts={r['script_id']:r for r in rows(p)}
        for idx,r in enumerate(scripts.values()):
            version=r['source_version'];textpath=Path(r['text_path'])
            if not textpath.is_file():self.skipped['missing_script_text']+=1;continue
            text=textpath.read_text(encoding='utf-8-sig',errors='replace')
            for line_no,line in enumerate(text.splitlines(),1):
                n=norm(line);mentions={aliases[m.group()] for m in pattern.finditer(n)}
                if not mentions:continue
                native=r['script_id']+':L'+str(line_no);sid=self.subj('script_reference',native,version,r['scene']+' / line '+str(line_no),str(textpath),locator=line_no,payload={'script_id':r['script_id'],'line':line_no,'raw_text':line,'route':r['route'],'scene':r['scene'],'source_index':str(p)})
                record={'script_id':r['script_id'],'text_path':str(textpath),'line':line_no,'raw_text':line,'script_index':r}
                ev=self.ev(p,native,record,version,'source_text_exact','confirmed_text_mention',raw=line,language=r['locale'],notes='Exact normalized alias in existing decoded source line; mention only. No speaker/identity inference.')
                for eid in mentions:self.relation(eid,'mentioned_in',sid,ev,'confirmed_text_mention','Existing decoded script line; named text only.')
            if idx%300==0:self.c.commit();print('Indexed existing script text',idx,'/',len(scripts),flush=True)
        p=L/'Metadata/ASSET_REFERENCES.csv'
        for r in rows(p):
            target=self.asset.get(r['target_asset_id'])
            if not target:continue
            native=r['script_id']+':L'+r['line'];sid=self.subjects.get(('script_reference',native,r['source_version']))
            if not sid:
                # Retain all existing resolved script→asset references, with no automatic character tag.
                sid=self.subj('script_reference',native,r['source_version'],r['scene']+' / line '+r['line'],str(L/'Metadata/ASSET_REFERENCES.csv'),locator=r['line'],payload=r)
            ev=self.ev(p,ident('ROW',r),r,r['source_version'],'script_reference',r['resolution_status'])
            self.relation(sid,'script_uses_asset',self.subjects[('asset',r['target_asset_id'],target['source_version'])],ev,r['resolution_status'],entity=False,notes='Original resolved reference status retained; no inferred character identity.')
        self.c.commit();print('Game indexes / mapped speakers / script-resource graph imported',flush=True)
    def fuc(self):
        version='FateUnlimitedCodesPortable_Europe';move_subjects={};commands={}
        p=F/'SemanticMapping/FUC_MOVE_INDEX.csv'
        for r in rows(p):
            eid=self.source_codes.get(r['character_code']);label=(self.c.execute('select preferred_label from entities where entity_id=?',(eid,)).fetchone()[0] if eid else r['character_code'])+' state'+r['state_number']
            sid=self.subj('fuc_move',r['move_id'],version,r['display_name'] or label,str(p),locator=r['move_id'],payload=r);move_subjects[r['move_id']]=sid
            ev=self.ev(p,r['move_id'],r,version,'runtime_confirmed' if r['semantic_status']=='confirmed_runtime' else 'table_confirmed',r['semantic_status'],notes='Unnamed states remain source-local subjects; labels are derived context, never official Move names.')
            if eid:self.relation(eid,'has_move',sid,ev,r['semantic_status'],r['notes'])
            if r['display_name'] and r['display_name']!='Unique Move' and r['name_mapping_status'].startswith('confirmed'):
                mid=self.entity(r['display_name'],'Move',p,r['move_id'],sc='FSN_DIRECT_EXTENSION');self.alias(mid,r['display_name'],ev,p,r['semantic_status'],'official_name');self.relation(mid,'source_move_state',sid,ev,r['semantic_status'])
                if eid:self.relation(eid,'has_move',mid,ev,r['semantic_status'],objentity=True)
        p=F/'SemanticMapping/FUC_COMMAND_INDEX.csv'
        for r in rows(p):
            sid=self.subj('fuc_command',r['command_id'],version,r['display_text'] or r['command_id'],str(p),locator=r['source_offset'],payload=r);commands[r['command_id']]=sid
            ev=self.ev(p,r['command_id'],r,version,'runtime_confirmed' if 'runtime' in r['status'] else 'table_confirmed',r['status']);eid=self.source_codes.get(r['character'])
            if eid:self.relation(eid,'has_command',sid,ev,r['status'],r['notes'])
        # Preserve UI entries that lack state bindings as independent subjects; no made-up bound moves.
        p=F/'SemanticMapping/FUC_MOVE_NAME_INDEX.csv'
        for r in rows(p):
            sid=self.subj('fuc_ui_entry',r['ui_entry_id'],version,r['display_name'],str(p),locator=r['source_offset'],payload=r)
            ev=self.ev(p,ident('ROW',r),r,version,'source_text_exact',r['status'],raw=r['display_name'],language='en');eid=self.source_codes.get(r['character'])
            if eid:self.relation(eid,'has_ui_move_label',sid,ev,r['status'],'State binding: '+r['state_binding_status'])
            if r['state_binding_status']=='unknown':self.review(p,ident('ROW',r),r,version,'unknown',sid,eid,'UI label observed; state binding unknown. On-demand only.')
        p=F/'SemanticMapping/FUC_CHARACTER_SEMANTIC_INDEX.csv'
        for r in rows(p):
            eid=self.source_codes.get(r['internal_code'])
            if not eid:continue
            for field in ['body_model_asset','mot_asset']:
                if not r[field]:continue
                status=r['body_model_status'] if field=='body_model_asset' else r['resource_sets_status']
                if status=='path_membership_only':status='candidate_path_membership'
                ev=self.ev(p,r['character_id']+':'+field,r,version,'source_path',status)
                self.assetlink(eid,r[field],ev,status,notes=r['evidence']+'; resource association limited to original '+field+' evidence.')
        p=F/'CHARACTER_ASSET_MAP.csv'
        for r in rows(p):
            eid=self.source_codes.get(r['character_code'])
            if not eid:continue
            ev=self.ev(p,r['asset_id'],r,version,'source_path','candidate_path_membership')
            self.assetlink(eid,r['asset_id'],ev,'candidate_path_membership',notes='Existing chr/<code> structural association. Original name unknown retained; no runtime ownership inferred.')
        for rel in ['BattleRuntimeMapping/FUC_EQUIPMENT_BINDINGS.csv','BattleGeneralization/FUC_EQUIPMENT_GENERALIZATION.csv']:
            p=F/rel
            for r in rows(p):
                eid=self.source_codes.get(r['character']);ev=self.ev(p,ident('ROW',r),r,version,'runtime_confirmed',r['status'])
                if eid:self.assetlink(eid,r['equipment_asset'],ev,r['status'],'weapon_model','has_equipment_model',r['notes']+'; named weapon identity not asserted.')
        p=F/'AnimationValidation/FUC_VALIDATED_ANIMATIONS.csv'
        for r in rows(p):
            eid=self.resolve(r['character']);ev=self.ev(p,r['animation_asset_id'],r,version,'runtime_confirmed','confirmed_runtime',notes=r['semantic_status'])
            if eid:self.assetlink(eid,r['animation_asset_id'],ev,'confirmed_runtime','animation',notes=r['notes']+'; '+r['semantic_status'])
            if r['animation_asset_id'] in self.asset:
                sid=self.subjects[('asset',r['animation_asset_id'],version)];payload=dict(self.asset[r['animation_asset_id']],validation=r)
                self.c.execute('update source_subjects set payload=? where semantic_subject_id=?',(js(payload),sid))
        p=F/'SemanticMapping/FUC_MOVE_RESOURCE_GRAPH.csv'
        pred={'animation_clip':'move_uses_animation','effect_model':'move_uses_effect','effect_sequence':'move_uses_effect','audio_payload':'move_uses_audio','weapon':'move_uses_equipment','body_model':'move_uses_model','command_table_result':'has_command','command_program_result':'has_command','observed_command':'has_command'}
        for r in rows(p):
            sid=move_subjects.get(r['move_id']);aid=r['target_asset_id'];target=None
            if aid in self.asset:target=self.subjects[('asset',aid,version)]
            elif r['target_id'] in commands:target=commands[r['target_id']]
            elif r['target_id']:
                # Qualified graph-only IDs are supported by the frozen graph record itself.
                target=self.subj('fuc_graph_node',r['target_id'],version,r['target_id'],str(p),locator=r['target_id'],payload=r)
            if not sid or not target:self.skipped['fuc_graph_unresolved']+=1;continue
            ev=self.ev(p,ident('ROW',r),r,version,'runtime_confirmed' if 'runtime' in r['status'] else 'table_confirmed',r['status'])
            self.relation(sid,pred.get(r['relation_type'],r['relation_type']),target,ev,r['status'],r.get('observed',''),entity=False)
            code=r['move_id'].split(':')[0];eid=self.source_codes.get(code)
            if aid and eid:self.assetlink(eid,aid,ev,r['status'],notes='Scoped resource of '+r['move_id']+' / '+r['relation_type']+'; '+r.get('observed',''))
        p=F/'SemanticMapping/FUC_MOVE_ANIMATION_MAP.csv'
        for r in rows(p):
            sid=move_subjects.get(r['move_id']);aid=r['clip_asset_id']
            if not sid or aid not in self.asset:continue
            ev=self.ev(p,r['move_id'],r,version,'runtime_confirmed' if r['mapping_status']=='confirmed_runtime' else 'visual_candidate',r['mapping_status'])
            self.relation(sid,'move_uses_animation',self.subjects[('asset',aid,version)],ev,r['mapping_status'],r['bank_resolution'],entity=False)
            if 'candidate' in r['mapping_status']:self.review(p,r['move_id'],r,version,r['mapping_status'],sid,self.source_codes.get(r['character']),'Selector status '+r['selector_status']+' does not promote bank-resolution candidate.')
        for rel,assetfield,predicate in [('FUC_MOVE_EFFECT_MAP.csv','effect_asset_id','move_uses_effect'),('FUC_MOVE_SOUND_MAP.csv','audio_asset','move_uses_audio')]:
            p=F/'SemanticMapping'/rel
            for r in rows(p):
                sid=move_subjects.get(r['move_id']);aid=r[assetfield];status=r.get('status',r.get('request_status','unknown'))
                ev=self.ev(p,r['move_id'],r,version,'runtime_confirmed',status)
                if sid and aid in self.asset:self.relation(sid,predicate,self.subjects[('asset',aid,version)],ev,status,r.get('notes',r.get('scope','')),entity=False)
        replay=F/'BattleReplay/FUC_LAN_CLIP145_REPLAY_MANIFEST.json';record=read(replay)
        sid=self.subj('fuc_replay','lan:clip145:replay',version,'Lancer state145 / clip145 replay',str(replay),payload=record)
        ev=self.ev(replay,'lan:clip145:replay',record,version,'runtime_confirmed','confirmed_runtime')
        self.relation(self.source_codes.get('lan'),'has_replay',sid,ev,'confirmed_runtime','M ATTACK context; unnamed state145 retained.')
        for r in rows(F/'SemanticMapping/FUC_SEMANTIC_CONFLICTS.csv'):
            self.c.execute('insert or ignore into conflicts values(?,?,?,?,?,?)',(ident('CNF',r),None,'source_record','retained',str(F/'SemanticMapping/FUC_SEMANTIC_CONFLICTS.csv'),js(r)))
        self.c.commit();print('Frozen FUC identities, states, commands, resource graph and replay imported',flush=True)
    def cross_source(self):
        configs=[('ORIGINAL_VS_REMASTERED.csv','original_asset_id','remastered_asset_id'),('FSN_VS_FHA.csv','fha_asset_id','fsn_asset_id'),('IMAGE_SIMILARITY.csv','asset_a','asset_b'),('FSN_VS_FUC.csv','fuc_asset_id','other_asset_id')]
        for filename,af,bf in configs:
            p=L/'Metadata'/filename
            for r in rows(p):
                a=self.asset.get(r.get(af,''));b=self.asset.get(r.get(bf,''))
                if not a or not b:
                    if r.get('match_type','').endswith('unmatched'):self.review(p,ident('ROW',r),r,a['source_version'] if a else 'Original','unknown',reason='Existing unmatched row retained; absence elsewhere not proven.')
                    continue
                exact=r.get('match_type')=='exact_payload' or r.get('hash_equal')=='True' or r.get('same_bytes')=='True'
                status='confirmed_exact_hash' if exact else 'candidate'
                pred='exact_payload' if exact else ('higher_resolution_candidate' if 'higher' in r.get('match_type','') else 'same_visual_candidate')
                ev=self.ev(p,ident('ROW',r),r,a['source_version'],'exact_hash' if exact else 'visual_similarity',status)
                sa=self.subjects[('asset',a['asset_id'],a['source_version'])];sb=self.subjects[('asset',b['asset_id'],b['source_version'])]
                self.relation(sa,pred,sb,ev,status,r.get('notes',r.get('evidence','')),entity=False)
                if not exact:self.review(p,ident('ROW',r),r,a['source_version'],status,sa,reason='Visual/structural candidate retained without promotion.')
        # Record label variation without declaring one historical spelling wrong.
        for r in self.c.execute('select entity_id,count(distinct alias) as n from aliases group by entity_id having n>1').fetchall():
            values=[dict(x) for x in self.c.execute('select distinct alias,source,status from aliases where entity_id=?',(r['entity_id'],))]
            self.c.execute('insert or ignore into conflicts values(?,?,?,?,?,?)',(ident('CNF','alias_variation',r['entity_id']),r['entity_id'],'alias_variation','retained','local_source_aliases',js(values)))
        self.c.commit();print('Existing exact-hash / candidate links and historical spellings retained',flush=True)
    def usage(self):
        cursor=self.c.execute('select r.*,s.* from relations r join source_subjects s on r.object_subject_id=s.semantic_subject_id where r.subject_entity_id is not null')
        for r in cursor:
            payload=json.loads(r['payload']);typ=r['subject_type'];role=self.role(payload) if typ=='asset' else typ
            if r['predicate']=='has_observed_voice_sample':role='voice'
            uses={'page':['lore_reference','UI_reference'],'shot':['effect_reference','battle_animation','card_art'],'script_reference':['lore_reference'],'fuc_move':['battle_animation'],'fuc_command':['battle_animation'],'fuc_ui_entry':['lore_reference'],'fuc_replay':['battle_animation']}.get(typ,[])
            if typ=='asset':uses={'animation':['battle_animation'],'voice':['voice'],'sound':['sound'],'BGM':['sound'],'effect':['effect_reference'],'model':['battle_animation'],'portrait':['portrait','card_art'],'CG':['card_art','event_art'],'image':['card_art','UI_reference'],'background':['background'],'script':['lore_reference']}.get(role,[])
            g=r['best_evidence_grade'];technical={k:payload.get(k,'') for k in ['width','height','alpha','duration','codec','motion_score']};technical['validated_animation']='validation' in payload
            for usage in uses:
                quality=0
                try:quality=min(10,float(technical['width'] or 0)*float(technical['height'] or 0)/1000000)
                except (ValueError,TypeError):pass
                rank=g*20+quality
                if usage=='battle_animation' and technical['validated_animation']:rank+=30
                if usage=='lore_reference' and typ=='page':rank+=20
                if r['scope'] in ('PARODY_COMEDY','DAILY_LIFE_REFERENCE') and usage in ('card_art','battle_animation'):rank-=25
                reason='Derived usage ranking: evidence strength S'+str(g)+'; '+role+'; scope '+r['scope']+'; existing technical metadata only.'
                if typ=='shot':reason+=' Unreviewed shot: mention only; battle/action and visual identity are unconfirmed.'
                self.c.execute('insert into usage_candidates values(?,?,?,?,?,?,?,?,?,?,?,?) on conflict(usage_candidate_id) do update set candidate_rank=excluded.candidate_rank,reason=excluded.reason,evidence_status=excluded.evidence_status,technical_quality=excluded.technical_quality',(ident('USE',r['subject_entity_id'],usage,r['relation_id']),r['subject_entity_id'],usage,r['native_id'],typ,r['semantic_subject_id'],rank,reason,r['status'],js(technical),'Recommendation is not source fact; compare within usage type only.',r['relation_id']))
        self.c.commit()
    def finish(self,incremental=False):
        print('Finalizing relation evidence aggregates',flush=True)
        self.c.execute('update relations set evidence_count=(select count(*) from relation_evidence re where re.relation_id=relations.relation_id),best_evidence_grade=(select max(e.semantic_strength) from relation_evidence re join evidence e on e.evidence_id=re.evidence_id where re.relation_id=relations.relation_id)')
        for fts,query in [('entity_fts','select entity_id,preferred_label||" "||entity_type from entities'),('alias_fts','select alias_id,entity_id,normalized_alias from aliases'),('evidence_text_fts','select evidence_id,normalized_text from evidence'),('source_text_fts','select semantic_subject_id,label||" "||native_id||" "||payload from source_subjects')]:
            print('Updating '+fts,flush=True)
            if incremental and fts!='entity_fts':
                key={'alias_fts':'alias_id','evidence_text_fts':'evidence_id','source_text_fts':'subject_id'}[fts]
                sourcekey={'alias_fts':'alias_id','evidence_text_fts':'evidence_id','source_text_fts':'semantic_subject_id'}[fts]
                self.c.execute('insert into '+fts+' '+query+' where '+sourcekey+' not in (select '+key+' from '+fts+')')
            else:
                self.c.execute('delete from '+fts);self.c.execute('insert into '+fts+' '+query)
        self.c.commit();self.c.execute('pragma optimize');print('Checking SQLite structure and references; final QA performs full integrity_check',flush=True);assert self.c.execute('pragma quick_check' if incremental else 'pragma integrity_check').fetchall()[0][0]=='ok';assert not self.c.execute('pragma foreign_key_check').fetchall()
        dump(self.registry_path,self.registry)
        exports={'ENTITY_INDEX':'entities','ENTITY_ALIASES':'aliases','RELATION_INDEX':'relations','EVIDENCE_INDEX':'evidence','RELATION_EVIDENCE':'relation_evidence','ENTITY_ASSET_LINKS':'entity_asset_links','ENTITY_SHOT_LINKS':'entity_shot_links','ENTITY_PAGE_LINKS':'entity_page_links','MOD_USAGE_CANDIDATES':'usage_candidates','SEMANTIC_REVIEW_QUEUE':'review_queue','SEMANTIC_CONFLICTS':'conflicts','CROSS_SOURCE_LINKS':'cross_source_links','SOURCE_SUBJECTS':'source_subjects','RELATION_HISTORY':'relation_history'}
        counts={}
        for name,table in exports.items():
            print('Exporting '+name,flush=True)
            cur=self.c.execute('select * from '+table+' order by 1');fields=[x[0] for x in cur.description];count=0
            with (S/'Metadata'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
                wr=csv.writer(f);wr.writerow(fields)
                for row in cur:wr.writerow(row);count+=1
            counts[table]=count
        with (S/'Metadata/ENTITY_INDEX.jsonl').open('w',encoding='utf-8') as f:
            for r in self.c.execute('select * from entities order by entity_id'):f.write(js(dict(r))+'\n')
        print('Aggregating six-source entity coverage',flush=True)
        all_stats=collections.defaultdict(dict)
        for eid,fam,n in self.c.execute('select r.subject_entity_id,s.source_family,count(distinct r.object_subject_id) from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id where r.subject_entity_id is not null group by r.subject_entity_id,s.source_family'):
            all_stats[eid][fam]=n
        mentions=dict(self.c.execute("select r.subject_entity_id,count(distinct r.object_subject_id) from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id where r.subject_entity_id is not null and s.subject_type='shot' and r.predicate='mentioned_in' group by r.subject_entity_id"))
        confirmed=dict(self.c.execute("select r.subject_entity_id,count(*) from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id where r.subject_entity_id is not null and s.subject_type='shot' and r.predicate in ('depicted_in','appears_in') group by r.subject_entity_id"))
        coverage=[]
        for e in self.c.execute('select * from entities').fetchall():
            stats=all_stats[e['entity_id']]
            row={'entity_id':e['entity_id'],'preferred_label':e['preferred_label'],**{x+'_count':stats.get(x,0) for x in FAMILIES}}
            row.update(FHA_count=stats.get('HollowAtaraxia',0),FUC_count=stats.get('FateUnlimitedCodesPortable_Europe',0),Official_count=stats.get('OfficialMaterial',0))
            row['Animation_mentions']=mentions.get(e['entity_id'],0)
            row['Animation_confirmed']=confirmed.get(e['entity_id'],0);coverage.append(row)
        with (S/'Metadata/ENTITY_SOURCE_COVERAGE.csv').open('w',encoding='utf-8-sig',newline='') as f:wr=csv.DictWriter(f,fieldnames=list(coverage[0]));wr.writeheader();wr.writerows(coverage)
        summary={'status':'IMPLEMENTED_AWAITING_QA','timestamp':now(),'semantic_catalog_revision':self.revision,'catalog_asset_count':270798,'max_asset_id':'FSN270798','new_FSN_IDs':0,'counts':counts,'source_families':FAMILIES,'entity_types':TYPES,'scopes':SCOPES,'animation_shot_count':67499,'official_page_count':1957,'fuc_frozen':True,'skipped':dict(self.skipped),'source_coverage':coverage,'known_limitations':['Unknown assets remain unknown. Subtitle/OCR mentions do not establish depiction.','Related-work class-name hits may have ambiguous referents; search-vocabulary association only.','FUC unnamed states remain source-local subjects; unbound UI labels remain unbound.','Usage ranks are derived per usage type. Media and thumbnails are not copied.','Historical records are append-only; input changes require a new revision.']}
        actual_predicates=[r[0] for r in self.c.execute('select distinct predicate from relations')]
        self.c.close();os.replace(self.stage,DB);dump(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json',summary)
        dump(S/'Metadata/SEMANTIC_SCHEMA.json',{'revision':self.revision,'entity_types':TYPES,'predicate_vocabulary':sorted(set(PREDICATES+actual_predicates)),'declared_predicate_vocabulary':PREDICATES,'alias_types':['official_name','internal_code','localized_name','romanization','search_alias','abbreviation','source_spelling','derived_translation'],'evidence_types':['runtime_confirmed','ui_confirmed','table_confirmed','source_text_exact','source_text_alias','script_reference','subtitle_exact','official_page_text','official_page_section','source_filename','source_path','exact_hash','visual_similarity','manual_visual','manual_review','visual_candidate','external_reference'],'scopes':SCOPES,'semantic_strength':'S5 runtime/exact hash; S4 UI/explicit text; S3 table/script; S2 alias/context; S1 candidate; S0 unknown. Original evidence types/statuses retained.','id_policy':self.registry['algorithm'],'combination_query':'Union of selected entities; optional shared source subject intersection. Shared mentions never imply uses_weapon/depiction.','incremental_policy':'Append evidence/relations/history; preserve stable source IDs. Never overwrite frozen revision snapshots.'})
        print('BUILD COMPLETE',js(counts),flush=True);return summary
def build(revision='v1'):
    b=Build(revision);b.seeds();b.import_subjects();b.official();b.animation();b.games();b.fuc();b.cross_source();b.usage();return b.finish()
if __name__=='__main__':build(sys.argv[1] if len(sys.argv)>1 else 'v1')
