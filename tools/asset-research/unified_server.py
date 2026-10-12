"""Loopback semantic workbench. All queries read-only; exports are reference-only JSON."""
from unified_common import *
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs,quote,unquote
import secrets, argparse, threading, webbrowser, mimetypes, re, subprocess
TOKEN=secrets.token_urlsafe(32)
def connect():
    c=ro(DB);c.row_factory=sqlite3.Row;return c
def resolve(c,label):
    return [dict(r) for r in c.execute('select distinct e.* from aliases a join entities e on e.entity_id=a.entity_id where a.normalized_alias=?',(norm(label),))]
def enrich(c,r):
    r=dict(r);p=json.loads(r.get('payload','{}'));r['payload']=p
    r['display_status']=display_status(r.get('status','unknown'),r.get('predicate',''))
    r['thumbnail_url']='/file?subject='+r['semantic_subject_id']+'&kind=thumbnail' if r.get('thumbnail') else ''
    r['file_url']='/file?subject='+r['semantic_subject_id']+'&kind=source'
    typ=r['subject_type'];nid=r['native_id']
    r['origin_url']=('/AnimationReferences/index.html#'+__import__('urllib.parse',fromlist=['urlencode']).urlencode({'q':nid,'shot':nid}) if typ=='shot' else '/ReferenceBooks/index.html#'+quote(nid) if typ=='page' else '/Gallery/FUC_LAN_CLIP145_REPLAY.html' if typ=='fuc_replay' else '/Gallery/FUC_SEMANTIC_MOVES.html' if typ.startswith('fuc_') else '/Gallery/index.html?asset='+quote(nid.split(':')[0]))
    r['role']=typ if typ!='asset' else p.get('asset_kind') or p.get('category','other')
    r['evidence_ids']=[x[0] for x in c.execute('select evidence_id from relation_evidence where relation_id=?',(r.get('relation_id',''),))]
    r['usages']=[dict(x) for x in c.execute('select usage_type,candidate_rank,reason from usage_candidates where relation_id=? order by candidate_rank desc',(r.get('relation_id',''),))]
    return r
def search(c,params):
    q=params.get('q',[''])[0].strip();parts=[p.strip() for p in re.split(r'[+＋]',q) if p.strip()];selected=[];unresolved=[]
    explicit=[x for x in params.get('entities',[''])[0].split(',') if x]
    if explicit:
        for eid in explicit:
            r=c.execute('select * from entities where entity_id=?',(eid,)).fetchone()
            if r:selected.append(dict(r))
    else:
        for p in parts:
            hits=resolve(c,p)
            if hits:selected.extend(hits)
            else:unresolved.append(p)
    selected=list({x['entity_id']:x for x in selected}.values());ids=[x['entity_id'] for x in selected]
    args=[];where=["r.status!='rejected'"];synthetic=[]
    if ids:
        where.append('r.subject_entity_id in ('+','.join('?'*len(ids))+')');args+=ids
        if params.get('mode',['union'])[0]=='shared' and len(ids)>1:
            where.append('r.object_subject_id in (select object_subject_id from relations where subject_entity_id in ('+','.join('?'*len(ids))+') group by object_subject_id having count(distinct subject_entity_id)=?)');args+=ids+[len(ids)]
    elif q:
        native=[dict(r) for r in c.execute('select * from source_subjects where native_id=? or semantic_subject_id=?',(q,q))]
        if native:
            sid=[r['semantic_subject_id'] for r in native];where.append('(r.object_subject_id in ('+','.join('?'*len(sid))+') or r.subject_subject_id in ('+','.join('?'*len(sid))+'))');args+=sid+sid
            synthetic=[enrich(c,dict(s,status='unknown',predicate='source_record',relation_id='',entity_label='',subject_entity_id=None,evidence_count=0,best_evidence_grade=0)) for s in native]
        else:
            evid=[]
            try:evid=[r[0] for r in c.execute('select evidence_id from evidence_text_fts where evidence_text_fts match ? limit 500',('"'+norm(q).replace('"','""')+'"',))]
            except sqlite3.OperationalError:pass
            if not evid:evid=[r[0] for r in c.execute('select evidence_id from evidence where normalized_text like ? limit 500',('%'+norm(q)+'%',))]
            if evid:where.append('r.relation_id in (select relation_id from relation_evidence where evidence_id in ('+','.join('?'*len(evid))+'))');args+=evid
            else:where.append('0')
    else:where.append('r.subject_entity_id is not null')
    src=[x for x in params.get('source',[''])[0].split(',') if x]
    if src:where.append('s.source_family in ('+','.join('?'*len(src))+')');args+=src
    sc=params.get('scope',[''])[0]
    if sc:where.append('s.scope=?');args.append(sc)
    usage=params.get('usage',[''])[0]
    if usage:where.append('exists(select 1 from usage_candidates u where u.relation_id=r.relation_id and u.usage_type=?)');args.append(usage)
    kind=params.get('kind',[''])[0]
    if kind:where.append('s.subject_type=?');args.append(kind)
    status=params.get('status',[''])[0]
    if status=='confirmed':where.append("r.status not like '%candidate%' and r.status not like '%unknown%' and r.status not like '%mention%' and r.status not like '%text_reference%' and r.predicate!='mentioned_in'")
    elif status=='mention':where.append("r.predicate='mentioned_in' and r.status not like '%candidate%'")
    elif status=='candidate':where.append("r.status like '%candidate%'")
    elif status=='unknown':where.append("r.status like '%unknown%'")
    base=' from relations r join source_subjects s on r.object_subject_id=s.semantic_subject_id left join entities e on e.entity_id=r.subject_entity_id where '+' and '.join(where)
    total=c.execute('select count(*)'+base,args).fetchone()[0]
    page=max(1,int(params.get('page',['1'])[0]));size=24
    order="r.best_evidence_grade desc,case s.scope when 'FSN_CORE' then 0 when 'FSN_DIRECT_EXTENSION' then 1 when 'FSN_ADAPTATION' then 2 when 'FATE_RELATED_REFERENCE' then 3 when 'DAILY_LIFE_REFERENCE' then 4 when 'PARODY_COMEDY' then 5 else 6 end,s.native_id,r.relation_id"
    if usage:order='(select max(candidate_rank) from usage_candidates u where u.relation_id=r.relation_id and usage_type='+"'"+usage.replace("'","''")+"') desc,"+order
    # Sort IDs first; fetch only one page of full raw source records after ranking.
    page_ids='select r.relation_id'+base+' order by '+order+' limit ? offset ?'
    page_query='select r.*,s.*,e.preferred_label as entity_label from relations r join source_subjects s on r.object_subject_id=s.semantic_subject_id left join entities e on e.entity_id=r.subject_entity_id where r.relation_id in ('+page_ids+') order by '+order
    found=[enrich(c,r) for r in c.execute(page_query,args+[size,(page-1)*size])]
    if not found and synthetic:
        found=[r for r in synthetic if (not src or r['source_family'] in src) and (not sc or r['scope']==sc) and (not kind or r['subject_type']==kind) and not usage and (not status or status=='unknown')];total=len(found)
    coverage={}
    for e in selected:
        coverage[e['entity_id']]={x:0 for x in FAMILIES}
        coverage[e['entity_id']].update(dict(c.execute('select s.source_family,count(distinct r.object_subject_id) from relations r join source_subjects s on r.object_subject_id=s.semantic_subject_id where r.subject_entity_id=? group by s.source_family',(e['entity_id'],))))
        e['aliases']=[dict(x) for x in c.execute('select distinct alias,alias_type,status from aliases where entity_id=?',(e['entity_id'],))]
        e['entity_relations']=[dict(x) for x in c.execute('select r.predicate,r.status,r.relation_id,t.entity_id as target_entity_id,t.preferred_label as target_label from relations r join entities t on t.entity_id=r.object_entity_id where r.subject_entity_id=?',(e['entity_id'],))]
    return {'query':q,'entities':selected,'unresolved':unresolved,'coverage':coverage,'results':found,'total':total,'page':page,'page_size':size,'combination_mode':params.get('mode',['union'])[0],'combination_note':'Shared source means co-mention/association on the same indexed object; it does not establish a character↔weapon relation.'}
def details(c,rid,sid=''):
    r=c.execute('select r.*,s.*,e.preferred_label as entity_label from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id left join entities e on e.entity_id=r.subject_entity_id where relation_id=?',(rid,)).fetchone()
    if r:item=enrich(c,r);sid=r['semantic_subject_id']
    else:
        r=c.execute('select * from source_subjects where semantic_subject_id=?',(sid,)).fetchone()
        if not r:raise ValueError('Unknown source subject')
        item=enrich(c,dict(r,status='unknown',predicate='source_record',relation_id='',evidence_count=0,best_evidence_grade=0,entity_label='',subject_entity_id=None))
    evidence=[dict(x) for x in c.execute('select e.* from relation_evidence re join evidence e on re.evidence_id=e.evidence_id where re.relation_id=? order by semantic_strength desc',(rid,))]
    edges=[dict(x) for x in c.execute('select r.relation_id,r.predicate,r.status,r.best_evidence_grade,s.native_id,s.label,s.semantic_subject_id from relations r join source_subjects s on s.semantic_subject_id=r.object_subject_id where r.subject_subject_id=? order by r.best_evidence_grade desc limit 150',(sid,))]
    item['evidence']=evidence;item['resource_edges']=edges
    item['helper_command']="& 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\OPEN_ANIMATION_REFERENCE.ps1' -ShotId '"+item['native_id']+"'" if item['subject_type']=='shot' else ''
    return item
def manifest(c,selection):
    if not isinstance(selection,list) or not 0<len(selection)<=500:raise ValueError('Select 1–500 references')
    out=[]
    for sel in selection:
        d=details(c,sel.get('relation_id',''),sel.get('subject_id',''));usage=sel.get('usage_type','lore_reference')
        allowed=['card_art','portrait','battle_animation','effect_reference','voice','sound','background','event_art','UI_reference','lore_reference']
        if usage not in allowed:raise ValueError('Unknown usage')
        out.append({'selection_id':ident('SEL',d['semantic_subject_id'],d.get('subject_entity_id'),usage),'entity':{'entity_id':d.get('subject_entity_id'),'label':d.get('entity_label','')},'usage_type':usage,'source_type':d['subject_type'],'source_id':d['native_id'],'asset_id':d['native_id'] if d['subject_type']=='asset' else d.get('page_asset_id') or d.get('media_asset_id'),'semantic_subject_id':d['semantic_subject_id'],'relation_id':d.get('relation_id',''),'predicate':d['predicate'],'reason':str(sel.get('reason','User selection from semantic workbench'))[:4000],'evidence_grade':{'semantic_strength':d['best_evidence_grade'],'original_status':d['status'],'display_status':d['display_status']},'evidence_ids':d['evidence_ids'],'evidence':d['evidence'],'source_path':d['source_path'],'source_family':d['source_family'],'source_version':d['source_version'],'scope':d['scope'],'source_locator':d['locator'],'media_asset_id':d['media_asset_id'],'page_asset_id':d['page_asset_id'],'timecode':d['payload'].get('start_time',''),'end_timecode':d['payload'].get('end_time',''),'source_sha256':d['payload'].get('source_sha256',d['payload'].get('sha256','')),'technical_quality':d['payload'],'notes':str(sel.get('notes',''))[:4000],'helper_command':d['helper_command']})
    return {'manifest_type':'MOD_SELECTION_MANIFEST','semantic_revision':read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json')['semantic_catalog_revision'],'exported_at':now(),'selection_id':ident('SELECTION',out,now()),'media_copied':False,'selections':out,'policy':'References only. Copy a selected working file when the actual MOD project needs it.'}
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k):super().__init__(*a,directory=str(L),**k)
    def json(self,obj,status=200):
        data=js(obj).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        u=urlparse(self.path);p=parse_qs(u.query)
        if u.path=='/':self.send_response(302);self.send_header('Location','/SemanticCatalog/index.html');self.end_headers();return
        if u.path=='/api/config':self.json({'service':'FSN_UNIFIED','token':TOKEN,'sources':FAMILIES,'scopes':SCOPES,'summary':read(S/'Metadata/SEMANTIC_FINAL_SUMMARY.json')});return
        if u.path in ('/api/search','/api/detail','/api/entities','/api/review'):
            try:
                c=connect()
                if u.path=='/api/search':result=search(c,p)
                elif u.path=='/api/detail':result=details(c,p.get('relation',[''])[0],p.get('subject',[''])[0])
                elif u.path=='/api/entities':result=[dict(r) for r in c.execute('select * from entities order by preferred_label')]
                else:
                    eid=p.get('entity',[''])[0];offset=max(0,int(p.get('page',['1'])[0])-1)*24
                    where=' where entity_id=?' if eid else '';args=[eid] if eid else []
                    result={'total':c.execute('select count(*) from review_queue'+where,args).fetchone()[0],'results':[dict(r) for r in c.execute('select * from review_queue'+where+' order by priority,review_id limit 24 offset ?',args+[offset])]}
                c.close();self.json(result)
            except Exception as e:self.json({'error':str(e)},400)
            return
        if u.path=='/file':
            c=connect();r=c.execute('select * from source_subjects where semantic_subject_id=?',(p.get('subject',[''])[0],)).fetchone();c.close()
            if not r:self.send_error(404);return
            kind=p.get('kind',['source'])[0];payload=json.loads(r['payload'])
            path=r['thumbnail'] if kind=='thumbnail' else payload.get('validation',{}).get('animated_glb','') if kind=='animated_glb' else payload.get('validation',{}).get('preview','') if kind=='preview' else r['source_path']
            if not path or not Path(path).is_file():self.send_error(404,'Registered source path unavailable');return
            self.serve_file(Path(path));return
        if u.path=='/Gallery/index.html' or u.path.startswith(('/Gallery/','/ReferenceBooks/','/AnimationReferences/','/Original/','/Remastered/','/HollowAtaraxia/','/FateUnlimitedCodesPortable_Europe/','/Converted/','/Metadata/','/SemanticCatalog/','/Reports/')):
            # SimpleHTTP's rooted translation prevents traversal outside the library.
            return super().do_GET()
        self.send_error(404)
    def serve_file(self,path):
        size=path.stat().st_size;start=0;end=size-1;partial=False
        value=self.headers.get('Range','')
        if value:
            m=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
            if not m:self.send_error(416);return
            start=int(m[1]);end=min(end,int(m[2])) if m[2] else end;partial=True
            if start>end:self.send_error(416);return
        self.send_response(206 if partial else 200);self.send_header('Content-Type',mimetypes.guess_type(str(path))[0] or 'application/octet-stream');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
        if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with path.open('rb') as f:
                f.seek(start);left=end-start+1
                while left:
                    data=f.read(min(1024*1024,left));self.wfile.write(data);left-=len(data)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):
        if self.headers.get('X-Semantic-Token')!=TOKEN and self.headers.get('X-Animation-Token')!=TOKEN:self.send_error(403);return
        if self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):self.send_error(403);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<1024*1024:raise ValueError('Request size')
            data=json.loads(self.rfile.read(size))
            if self.path=='/api/export':
                c=connect();obj=manifest(c,data['selection']);c.close();filename='MOD_SELECTION_MANIFEST_'+obj['selection_id']+'.json';dump(S/'Exports'/filename,obj);dump(S/'Exports/MOD_SELECTION_MANIFEST.json',obj);self.json({'status':'EXPORTED','count':len(obj['selections']),'path':str(S/'Exports'/filename),'url':'/SemanticCatalog/Exports/'+filename,'latest_path':str(S/'Exports/MOD_SELECTION_MANIFEST.json'),'manifest':obj})
            elif self.path=='/api/open':
                c=connect();r=c.execute("select native_id from source_subjects where native_id=? and subject_type='shot'",(data['shot_id'],)).fetchone();c.close()
                if not r:raise ValueError('Unknown shot')
                subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',r'E:\FSN_MASTER_ASSET_WORK\scripts\OPEN_ANIMATION_REFERENCE.ps1','-ShotId',r['native_id']],creationflags=subprocess.CREATE_NO_WINDOW);self.json({'status':'OPENED','shot_id':r['native_id']})
            elif self.path=='/api/shutdown':self.json({'status':'STOPPING'});threading.Thread(target=self.server.shutdown,daemon=True).start()
            else:self.send_error(404)
        except Exception as e:self.json({'error':str(e)},400)
    def log_message(self,*args):pass
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);ap.add_argument('--open-browser',action='store_true');args=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);url=f'http://127.0.0.1:{server.server_address[1]}/SemanticCatalog/index.html'
    dump(W/'SERVER.json',{'service':'FSN_UNIFIED','pid':os.getpid(),'port':server.server_address[1],'url':url,'token':TOKEN,'timestamp':now(),'bind':'127.0.0.1'})
    print(url,flush=True)
    if args.open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
