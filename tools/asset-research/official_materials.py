"""Read-only official reference-book pipeline. Outputs and caches stay on E:.
Stable identities depend on preserved scan order, never OCR order.
"""
import os, sys, json, csv, hashlib, pathlib, shutil, sqlite3, re, subprocess, datetime, collections, concurrent.futures, unicodedata, math, time
sys.stdout.reconfigure(encoding='utf-8')
W=pathlib.Path('E:/FSN_MASTER_ASSET_WORK'); L=pathlib.Path('E:/FSN_MASTER_ASSET_LIBRARY')
S=pathlib.Path('E:/BaiduNetdiskDownload/FSN/素材'); R=L/'ReferenceBooks'; M=R/'Metadata'; B=W/'backups/official-material-pre'; T=W/'official-material'
for d in [M,B,T,W/'tmp/official-material',W/'logs'] : d.mkdir(parents=True,exist_ok=True)
os.environ.update(TEMP=str(W/'tmp/official-material'), TMP=str(W/'tmp/official-material'), OMP_THREAD_LIMIT='1', PIP_CACHE_DIR=str(W/'tmp/pip'))
Z=pathlib.Path('D:/7-Zip/7z.exe')
IMAGE_EXT={'.jpg','.jpeg','.png','.webp','.tif','.tiff','.bmp','.jp2','.gif'}
ARCHIVE_EXT={'.zip','.rar','.7z','.cbz','.cbr'}
BOOKS={'CM_I':('CompleteMaterial_I','Fate/complete material I Art material.','I'), 'CM_II':('CompleteMaterial_II','Fate/complete material II Character material.','II'), 'CM_III':('CompleteMaterial_III','Fate/complete material III World material.','III'), 'CM_IV':('CompleteMaterial_IV','Fate/complete material IV Extra material.','IV'), 'CM_V':('CompleteMaterial_V','Fate/complete material V Hollow material.','V'), 'SIDE':('SideMaterial','Fate/side side materiale complete','Side')}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def writejson(p,d):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def readjson(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def writejl(p,rows):
    tmp=pathlib.Path(str(p)+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    os.replace(tmp,p)
def readjl(p):
    with pathlib.Path(p).open(encoding='utf-8-sig') as f:return [json.loads(s) for s in f if s.strip()]
def csvout(p,rows,fields=None):
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    with pathlib.Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def log(*a):print(now(),*a,flush=True)
def natural(p):return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)',str(p))]
def book_for(name):
    n=name.lower()
    if re.search(r'side[ _-]*material',n):return 'SIDE'
    m=re.search(r'complete[ _-]*material[ _-]+(iii|ii|iv|v|i)(?![a-z])',n)
    return 'CM_'+m[1].upper() if m else ''
def sources():return sorted([p for p in S.rglob('*') if p.is_file() and re.search(r'(complete[ _-]*material|side[ _-]*material)',str(p),re.I)],key=lambda p:str(p))
def baseline():
    dest=L/'Reports/OFFICIAL_MATERIAL_PRE_INTEGRATION_BASELINE.json'
    if dest.exists():log('Baseline already frozen');return
    catalogs={}
    for ext in ['csv','jsonl','sqlite']:
        p=L/('Metadata/ASSET_CATALOG.'+ext);q=B/p.relative_to(L);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(p)==sha(q);catalogs[ext]={'sha256':sha(p),'size':p.stat().st_size}
    db=sqlite3.connect('file:'+str(L/'Metadata/ASSET_CATALOG.sqlite')+'?mode=ro',uri=True)
    count,maxid=db.execute('select count(*),max(asset_id) from assets').fetchone();integrity=db.execute('pragma integrity_check').fetchone()[0];counts=dict(db.execute('select source_version,count(*) from assets group by source_version'));db.close()
    assert count==268504 and maxid=='FSN268504' and integrity=='ok',(count,maxid,integrity)
    protected=['Gallery','Reports','Original','Remastered','HollowAtaraxia','FateUnlimitedCodesPortable_Europe'];summaries={};manifest=B/'PROTECTED_PATHS.jsonl';n=0
    with manifest.open('w',encoding='utf-8') as f:
        for directory in protected:
            c=0;size=0
            for root,dirs,files in os.walk(L/directory):
                for name in files:
                    p=pathlib.Path(root)/name;st=p.stat();r={'path':str(p.relative_to(L)),'size':st.st_size,'mtime_ns':st.st_mtime_ns}
                    if directory in ['Gallery','Reports']:
                        r['sha256']=sha(p)
                        if p.suffix.lower() in {'.html','.js','.json','.md','.csv','.css'} and st.st_size<400_000_000:
                            q=B/p.relative_to(L);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
                    f.write(json.dumps(r,ensure_ascii=False)+'\n');c+=1;size+=st.st_size;n+=1
            summaries[directory]={'file_count':c,'logical_bytes':size};log('Frozen directory',directory,c)
    data={'created_at':now(),'asset_count':count,'max_asset_id':maxid,'source_counts':counts,'catalogs':catalogs,'sqlite_integrity':integrity,'protected_directories':summaries,'protected_manifest_sha256':sha(manifest),'backup':str(B),'raw_copied':False,'protection_method':'All protected paths/size/mtime; Gallery and Reports SHA256; exact catalog byte copies'}
    writejson(dest,data);writejson(B/'BASELINE.json',data);log('BASELINE',count,maxid,n)
def inventory():
    out=M/'BOOK_SOURCE_INVENTORY.json'
    if out.exists():log('Inventory frozen');return
    from PIL import Image
    rows=[]
    for p in sources():
        st=p.stat();bid=book_for(p.name);kind=p.suffix.lower();r={'source_id':'SRC'+str(len(rows)+1).zfill(4),'path':str(p),'file_type':kind,'size':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(p),'book_id':bid,'scope':'target' if bid else 'accessory_or_excluded','page_count':None,'width':None,'height':None,'complete':'unverified','has_cover':'unverified','scan_version':'unverified','error':''}
        if kind in IMAGE_EXT:
            if not bid:bid=book_for(str(p.parent));r['book_id']=bid;r['scope']='target' if bid else 'accessory_or_excluded'
            try:
                with Image.open(p) as im:r.update(width=im.width,height=im.height,format=im.format,mode=im.mode,page_count=getattr(im,'n_frames',1))
            except Exception as e:r['error']=str(e)
        elif kind in ARCHIVE_EXT:
            proc=subprocess.run([str(Z),'l','-slt','-sccUTF-8',str(p)],capture_output=True,encoding='utf-8',errors='replace');r['archive_list_exit']=proc.returncode
            (T/(r['source_id']+'_listing.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
            entries=[]
            for block in proc.stdout.split('\n\n'):
                attrs=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
                if 'Path' in attrs and 'Size' in attrs and attrs.get('Folder')!='+':entries.append(attrs)
            r['archive_image_count']=sum(pathlib.Path(a['Path']).suffix.lower() in IMAGE_EXT for a in entries);r['page_count']=r['archive_image_count'];r['archive_entries']=len(entries)
            writejson(T/(r['source_id']+'_entries.json'),entries)
            if proc.returncode:r['error']=proc.stderr
        rows.append(r);log('Source',r['source_id'],p.name,r.get('page_count'))
    writejson(out,rows);csvout(M/'BOOK_SOURCE_INVENTORY.csv',rows)
def extract():
    marker=M/'EXTRACTION_RESULTS.json'
    if marker.exists():log('Extraction already complete');return
    inv=readjson(M/'BOOK_SOURCE_INVENTORY.json');results=[]
    for r in inv:
        if r['scope']!='target' or r['file_type'] in IMAGE_EXT:continue
        bid=r['book_id'];p=pathlib.Path(r['path']);folder=R/'Preservation'/BOOKS[bid][0]/r['source_id'];folder.mkdir(parents=True,exist_ok=True);cp=folder/p.name
        if not cp.exists():shutil.copy2(p,cp)
        assert sha(cp)==r['sha256']
        dst=folder/'Extracted';dst.mkdir(exist_ok=True)
        # Extract only into this library-owned folder; archive listing is retained.
        entries=readjson(T/(r['source_id']+'_entries.json'))
        for item in entries:
            parts=pathlib.PureWindowsPath(item['Path']).parts
            assert not pathlib.PureWindowsPath(item['Path']).is_absolute() and '..' not in parts,'Unsafe archive member'
        log('Extracting',bid,p.name)
        proc=subprocess.run([str(Z),'x','-y','-bsp0','-sccUTF-8','-o'+str(dst),str(cp)],capture_output=True,encoding='utf-8',errors='replace')
        (W/'logs'/('official_'+r['source_id']+'_extract.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        results.append({'source_id':r['source_id'],'book_id':bid,'container_copy':str(cp),'extracted_root':str(dst),'exit_code':proc.returncode,'image_files':len([p for p in dst.rglob('*') if p.suffix.lower() in IMAGE_EXT]),'log':str(W/'logs'/('official_'+r['source_id']+'_extract.txt'))})
        log('Extracted',bid,results[-1]['image_files'],proc.returncode)
    # Loose Side scan files are copied, never hardlinked to the user's originals.
    loose=[r for r in inv if r['scope']=='target' and r['file_type'] in IMAGE_EXT]
    for bid in BOOKS:
        group=[r for r in loose if r['book_id']==bid]
        if not group:continue
        folder=R/'Preservation'/BOOKS[bid][0]/'LOOSE';folder.mkdir(parents=True,exist_ok=True)
        for r in group:
            cp=folder/pathlib.Path(r['path']).name
            if not cp.exists():shutil.copy2(r['path'],cp)
            assert sha(cp)==r['sha256']
        results.append({'source_id':'LOOSE_'+bid,'book_id':bid,'container_copy':'','extracted_root':str(folder),'exit_code':0,'image_files':len(group),'source_ids':[r['source_id'] for r in group]})
    # Preserve accessory box photographs without assigning them book-page identities.
    for r in inv:
        if r['scope']=='accessory_or_excluded' and r['file_type'] in IMAGE_EXT:
            folder=R/'Preservation/Accessories';folder.mkdir(parents=True,exist_ok=True);shutil.copy2(r['path'],folder/pathlib.Path(r['path']).name)
    writejson(marker,results)

def pages():
    from PIL import Image,ImageStat,ImageOps,ImageDraw,ImageFont
    import imagehash
    output=M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl'
    if output.exists() and output.stat().st_size and (M/'CONTACT_SHEETS.json').exists():log('Page identity already established');return
    inv=readjson(M/'BOOK_SOURCE_INVENTORY.json');ex=readjson(M/'EXTRACTION_RESULTS.json');allpages=[];provenance=[];books=[];duplicates=[];anomalies=[];payload_objects={};nextid=268505
    for bid,(directory,title,volume) in BOOKS.items():
        scans=[r for r in ex if r['book_id']==bid]
        scans.sort(key=lambda r:(0 if 'collection' in r.get('container_copy','') else 1, r['source_id']))
        prior=[];variant=0
        for scan in scans:
            source_id=scan['source_id'];root=pathlib.Path(scan['extracted_root']);files=sorted([p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in IMAGE_EXT],key=lambda p:natural(p.relative_to(root)))
            log('Inspecting scan',bid,source_id,len(files))
            scanned=[]
            for i,p in enumerate(files,1):
                h=sha(p);r={'source_id':source_id,'book_id':bid,'source_member':str(p.relative_to(root)),'preservation_path':str(p),'scan_page_index':i,'sha256':h,'size':p.stat().st_size,'extraction_status':'success'}
                try:
                    with Image.open(p) as im:
                        width,height,fmt,mode,bands=im.width,im.height,im.format,im.mode,im.getbands();dpi=im.info.get('dpi','');orientation=int(im.getexif().get(274,1));im.draft('RGB',(512,512));im.load();small=im.convert('RGB');small.thumbnail((512,512));stat=ImageStat.Stat(small.convert('L'));r.update(width=width,height=height,format=fmt,color_mode=mode,alpha='A' in bands,dpi=[float(x) for x in dpi] if isinstance(dpi,tuple) else dpi,exif_orientation=orientation,display_rotation=0,phash=str(imagehash.phash(small)),dhash=str(imagehash.dhash(small)),mean_luminance=stat.mean[0],std_luminance=stat.stddev[0])
                    if min(r['width'],r['height'])<500:anomalies.append({'book_id':bid,'source_id':source_id,'scan_page':i,'kind':'small_image','evidence':f"{r['width']}x{r['height']}",'status':'retained'})
                    if r['std_luminance']<7 and r['mean_luminance']>225:anomalies.append({'book_id':bid,'source_id':source_id,'scan_page':i,'kind':'blank_candidate','evidence':f"luminance mean={r['mean_luminance']:.2f}, std={r['std_luminance']:.2f}",'status':'retained'})
                    if r['exif_orientation']!=1:anomalies.append({'book_id':bid,'source_id':source_id,'scan_page':i,'kind':'exif_orientation','evidence':str(r['exif_orientation']),'status':'preserved; preview honors EXIF'})
                except Exception as e:r.update(extraction_status='unreadable',error=str(e));anomalies.append({'book_id':bid,'source_id':source_id,'scan_page':i,'kind':'unreadable','evidence':str(e),'status':'unresolved'})
                scanned.append(r)
            numeric=[]
            for p in files:
                m=re.search(r'_(\d+)([a-z]*)$',p.stem,re.I)
                if m and not m[2] and 0<int(m[1])<999:numeric.append(int(m[1]))
            if numeric:
                absent=sorted(set(range(1,max(numeric)+1))-set(numeric))
                if absent:anomalies.append({'book_id':bid,'source_id':source_id,'scan_page':'','kind':'filename_number_gap','evidence':json.dumps(absent),'status':'unresolved'})
            sequence=[r['sha256'] for r in scanned];exact=next((s for s in prior if s['sequence']==sequence),None)
            if exact:
                for i,r in enumerate(scanned):
                    r['page_id']=exact['pages'][i]['page_id'];r['page_asset_id']=exact['pages'][i]['page_asset_id'];r['duplicate_of']=exact['pages'][i]['preservation_path'];provenance.append(r)
                    original=pathlib.Path(r['duplicate_of']);p=pathlib.Path(r['preservation_path'])
                    # Both files are library-owned preservation copies. Replace only identical output bytes.
                    if p!=original and p.stat().st_ino!=original.stat().st_ino:p.unlink();os.link(original,p)
                duplicates.append({'book_id':bid,'source_a':exact['source_id'],'source_b':source_id,'relationship':'same_scan_different_container','page_count':len(scanned),'exact_payload_matches':len(scanned),'status':'confirmed','evidence':'ordered page SHA256 sequences identical; all origins retained'})
                continue
            variant+=1;vid='PRIMARY' if variant==1 else 'ALT'+str(variant-1).zfill(2)
            for old in prior:
                matched=sum(a==b for a,b in zip(sequence,old['sequence']));dist=[(int(a.get('phash','0'),16)^int(b.get('phash','0'),16)).bit_count() for a,b in zip(scanned,old['pages'])]
                same_dim=sum((a.get('width'),a.get('height'))==(b.get('width'),b.get('height')) for a,b in zip(scanned,old['pages']))
                relation='unknown'
                if len(scanned)==len(old['pages']) and dist and sum(d<=4 for d in dist)/len(dist)>.95:relation='same_scan_different_container' if same_dim==len(scanned) else 'higher_resolution_scan'
                else:relation='different_scan'
                duplicates.append({'book_id':bid,'source_a':old['source_id'],'source_b':source_id,'relationship':relation,'page_count':len(scanned),'exact_payload_matches':matched,'matching_dimensions':same_dim,'mean_phash_distance':sum(dist)/len(dist) if dist else None,'status':'visual_candidate' if matched!=len(scanned) else 'confirmed','evidence':'ordered SHA256/dimensions/pHash comparison; variant remains independently indexed'})
            bookpages=[]
            for i,r in enumerate(scanned,1):
                pid=bid+('' if vid=='PRIMARY' else '_'+vid)+'_'+str(i).zfill(4);aid=f'FSN{nextid:06d}';nextid+=1
                pagefolder=R/'Pages'/directory/vid;pagefolder.mkdir(parents=True,exist_ok=True);original=pathlib.Path(r['preservation_path']);working=pagefolder/(str(i).zfill(4)+original.suffix.lower())
                canonical=payload_objects.setdefault(r['sha256'],original)
                if original!=canonical and original.stat().st_ino!=canonical.stat().st_ino:original.unlink();os.link(canonical,original)
                if not working.exists():os.link(original,working)
                thumb=R/'Thumbnails'/directory/(pid+'.webp');thumb.parent.mkdir(parents=True,exist_ok=True)
                if r['extraction_status']=='success' and not thumb.exists():
                    with Image.open(original) as im:
                        im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((480,640));im.save(thumb,'WEBP',quality=82)
                source_record=next((v for v in inv if v['source_id']==source_id),None)
                source_file=source_record['path'] if source_record else str(S/'Fate-side material complete')
                row={**r,'page_id':pid,'page_asset_id':aid,'asset_id':aid,'book_title':title,'volume':volume,'scan_variant':vid,'source_file':source_file,'source_book':bid,'scan_page':i,'printed_page':None,'printed_page_number':None,'printed_page_label':'','printed_page_evidence':'','section':'','section_context':'','page_role':['Unknown'],'page_path':str(working),'thumbnail':str(thumb),'ocr_status':'pending','ocr_language':'jpn+eng','ocr_confidence':None,'characters_confirmed':[],'characters_candidate':[],'keywords':[],'notes':'Filename numbering retained as source metadata; printed numbering requires visible/OCR evidence.','reference_only':True,'source_family':'OfficialMaterial'}
                bookpages.append(row);allpages.append(row);provenance.append({**r,'page_id':pid,'page_asset_id':aid})
            prior.append({'source_id':source_id,'sequence':sequence,'pages':bookpages})
            books.append({'book_id':bid,'title':title,'volume':volume,'scan_variant':vid,'source':source_file,'source_id':source_id,'page_count':len(scanned),'scan_format':'JPEG' if all(r.get('format')=='JPEG' for r in scanned) else 'mixed','language':'Japanese; Latin headings','source_hash':source_record['sha256'] if source_record else hashlib.sha256(''.join(sequence).encode()).hexdigest(),'duplicate_group':'','status':'accessible_scan; physical completeness pending visual review','numbered_scan_count':len(numeric),'filename_sequence_end':max(numeric) if numeric else None,'filename_missing':absent if numeric else []})
    groups=collections.defaultdict(list)
    for r in allpages:groups[r['sha256']].append(r['page_id'])
    for h,ids in groups.items():
        if len(ids)>1:anomalies.append({'book_id':'','source_id':'','scan_page':'','kind':'exact_duplicate','evidence':json.dumps(ids),'status':'retained'})
    writejl(output,allpages);csvout(M/'OFFICIAL_MATERIAL_PAGE_INDEX.csv',allpages);writejl(M/'SOURCE_PAGE_PROVENANCE.jsonl',provenance);csvout(M/'OFFICIAL_MATERIAL_BOOK_INDEX.csv',books);writejson(M/'BOOKS.json',books);csvout(M/'OFFICIAL_MATERIAL_DUPLICATES.csv',duplicates,['book_id','source_a','source_b','relationship','page_count','exact_payload_matches','matching_dimensions','mean_phash_distance','status','evidence']);writejson(M/'DUPLICATES.json',duplicates);csvout(M/'OFFICIAL_MATERIAL_PAGE_ANOMALIES.csv',anomalies,['book_id','source_id','scan_page','kind','evidence','status']);writejson(M/'ANOMALIES.json',anomalies)
    # Stable paged overview sheets; no hundreds-of-pages canvas.
    sheets=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    for b in books:
        group=[r for r in allpages if r['book_id']==b['book_id'] and r['scan_variant']==b['scan_variant']]
        folder=R/'ContactSheets'/BOOKS[b['book_id']][0]/b['scan_variant'];folder.mkdir(parents=True,exist_ok=True)
        for start in range(0,len(group),24):
            chunk=group[start:start+24];canvas=Image.new('RGB',(1200,1608),'#e8edf2');draw=ImageDraw.Draw(canvas)
            for j,r in enumerate(chunk):
                x=(j%4)*300;y=(j//4)*268
                if pathlib.Path(r['thumbnail']).exists():
                    with Image.open(r['thumbnail']) as im:im=im.convert('RGB');im.thumbnail((282,225));canvas.paste(im,(x+(300-im.width)//2,y+4))
                draw.text((x+10,y+232),r['page_id'],fill='#152f50',font=font);draw.text((x+10,y+249),r['page_asset_id'],fill='#152f50',font=font)
            path=folder/(str(start//24+1).zfill(3)+'.jpg');canvas.save(path,quality=90);sheets.append({'book_id':b['book_id'],'scan_variant':b['scan_variant'],'sheet':start//24+1,'scan_start':start+1,'scan_end':start+len(chunk),'path':str(path)})
    writejson(M/'CONTACT_SHEETS.json',sheets);log('PAGES',len(allpages),'unique payloads',len(groups),'scans',len(books))

def ocr_one(row,tools):
    from PIL import Image,ImageOps
    pid=row['page_id'];raw=R/'OCR/Raw'/row['book_id'];norm=R/'OCR/Normalized'/row['book_id'];raw.mkdir(parents=True,exist_ok=True);norm.mkdir(parents=True,exist_ok=True);base=raw/pid;result=raw/(pid+'.result.json')
    if result.exists() and (raw/(pid+'.tsv')).exists():return readjson(result)
    inp=W/'tmp/official-material'/(pid+'.png');languages='jpn+eng';start=time.time()
    try:
        with Image.open(row['page_path']) as im:
            im=ImageOps.exif_transpose(im).convert('RGB');orig=im.size;im.thumbnail((2400,2400));scale=(orig[0]/im.width,orig[1]/im.height);im.save(inp)
        cmd=[tools['executable'],str(inp),str(base),'--tessdata-dir',tools['tessdata'],'-l',languages,'--oem','1','--psm','3','txt','tsv','hocr']
        proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
        (raw/(pid+'.stderr.txt')).write_text(proc.stderr,encoding='utf-8')
        text=(raw/(pid+'.txt')).read_text(encoding='utf-8') if (raw/(pid+'.txt')).exists() else ''
        normalized=unicodedata.normalize('NFKC',text).replace('\r\n','\n')
        normalized=re.sub(r'(?<=[\u3000-\u9fff]) +(?=[\u3000-\u9fff])','',normalized)
        (norm/(pid+'.txt')).write_text(normalized,encoding='utf-8')
        words=[];lines=collections.defaultdict(list)
        if (raw/(pid+'.tsv')).exists():
            with (raw/(pid+'.tsv')).open(encoding='utf-8',newline='') as f:
                for word in csv.DictReader(f,delimiter='\t'):
                    if word['level']=='5' and word.get('text','').strip():
                        w={'x':round(int(word['left'])*scale[0],2),'y':round(int(word['top'])*scale[1],2),'width':round(int(word['width'])*scale[0],2),'height':round(int(word['height'])*scale[1],2),'text':word['text'],'confidence':float(word['conf'])};words.append(w);lines[(word['block_num'],word['par_num'],word['line_num'])].append(w)
        blocks=[]
        for key,ws in lines.items():
            x=min(w['x'] for w in ws);y=min(w['y'] for w in ws);right=max(w['x']+w['width'] for w in ws);bottom=max(w['y']+w['height'] for w in ws)
            txt=' '.join(w['text'] for w in ws);txt=re.sub(r'(?<=[\u3000-\u9fff]) +(?=[\u3000-\u9fff])','',unicodedata.normalize('NFKC',txt))
            blocks.append({'page_id':pid,'block_id':'.'.join(key),'coordinate_space':'original_page_pixels','x':x,'y':y,'width':round(right-x,2),'height':round(bottom-y,2),'text':txt,'confidence':sum(w['confidence'] for w in ws)/len(ws),'words':ws})
        confidence=sum(w['confidence'] for w in words)/len(words) if words else None
        status='failed' if proc.returncode or not (raw/(pid+'.tsv')).exists() else ('no_text_detected' if not words and not text.strip() else 'success' if words and confidence>=70 else 'partial')
        res={'page_id':pid,'raw_text_path':str(raw/(pid+'.txt')),'raw_tsv_path':str(raw/(pid+'.tsv')),'raw_hocr_path':str(raw/(pid+'.hocr')),'normalized_text_path':str(norm/(pid+'.txt')),'language':languages,'block_count':len(blocks),'word_count':len(words),'confidence':confidence,'confidence_metric':'Tesseract native word confidence 0..100; line/mean arithmetic aggregation, not a probability','status':status,'exit_code':proc.returncode,'command':cmd,'input_dimensions':orig,'scale_to_original':scale,'normalization_evidence':'Unicode NFKC; CRLF to LF; remove whitespace only between adjacent CJK characters; no wording corrections','elapsed_seconds':round(time.time()-start,2),'blocks':blocks}
    except Exception as e:
        (raw/(pid+'.txt')).write_text('',encoding='utf-8');(norm/(pid+'.txt')).write_text('',encoding='utf-8');res={'page_id':pid,'raw_text_path':str(raw/(pid+'.txt')),'normalized_text_path':str(norm/(pid+'.txt')),'language':languages,'block_count':0,'word_count':0,'confidence':None,'status':'failed','error':str(e),'blocks':[]}
    finally:
        if inp.exists():inp.unlink()
    writejson(result,res);return res
def ocr():
    rows=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');tools=readjson(W/'tools/official-tesseract/TOOLS_MANIFEST.json');writejson(M/'OFFICIAL_MATERIAL_OCR_TOOLS.json',tools)
    # Front matter first, then all pages. Cache by immutable page ID.
    priority=sorted(rows,key=lambda r:(0 if r['scan_page']<=16 else 1,list(BOOKS).index(r['book_id']),r['scan_page']))
    results={};workers=min(8,max(2,(os.cpu_count() or 4)//2));log('OCR workers',workers,'pages',len(rows))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(ocr_one,r,tools):r for r in priority}
        for n,f in enumerate(concurrent.futures.as_completed(futures),1):
            rr=f.result();results[rr['page_id']]=rr
            if n%25==0:log('OCR',n,'/',len(rows),rr['page_id'],rr['status'])
    blocks=[];idx=[]
    for r in rows:
        o=results[r['page_id']];r.update(ocr_status=o['status'],ocr_language=o['language'],ocr_confidence=o['confidence']);blocks.extend(o.get('blocks',[]));idx.append({k:v for k,v in o.items() if k!='blocks'})
    writejl(M/'OFFICIAL_MATERIAL_OCR_BLOCKS.jsonl',blocks);writejl(M/'OCR_INDEX.jsonl',idx);csvout(M/'OFFICIAL_MATERIAL_OCR_INDEX.csv',idx);writejl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl',rows);csvout(M/'OFFICIAL_MATERIAL_PAGE_INDEX.csv',rows);log('OCR COMPLETE',dict(collections.Counter(r['status'] for r in idx)))

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'Inventory'
    if mode=='Inventory':baseline();inventory()
    elif mode=='Extract':extract()
    elif mode=='Pages':pages()
    elif mode=='OCR':ocr()
    else:raise SystemExit('Stage not yet implemented: '+mode)
