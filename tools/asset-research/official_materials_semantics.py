"""Evidence-led metadata. Section propagation never confirms a page character."""
from official_materials import *
sys.stdout.reconfigure(encoding='utf-8')
# Transcribed after visual inspection of each original TOC crop, retained beside raw OCR.
TOC={
'CM_I':[(3,'EVENT VISUAL Prologue'),(8,'EVENT VISUAL Fate'),(42,'EVENT VISUAL Unlimited Blade Works'),(74,'EVENT VISUAL Heavens Feel'),(112,'SECOND EVENT VISUAL Other'),(145,'IMAGE VISUAL Adult Scene'),(172,'IMAGE VISUAL Title'),(178,'IMAGE VISUAL Another'),(188,'IMAGE VISUAL Another+'),(194,'IMAGE VISUAL Effect'),(206,'IMAGE VISUAL Tarot'),(213,'ART WORKS Publicity')],
'CM_II':[(3,'CHARACTERS'),(4,'セイバー'),(16,'遠坂凛'),(26,'間桐桜'),(42,'衛宮士郎'),(46,'アーチャー'),(50,'ライダー'),(54,'イリヤスフィール・フォン・アインツベルン'),(64,'バーサーカー'),(66,'言峰綺礼'),(70,'ランサー'),(74,'ギルガメッシュ'),(80,'葛木宗一郎'),(84,'キャスター'),(88,'アサシン'),(90,'間桐臓硯'),(92,'真アサシン'),(94,'間桐慎二'),(98,'藤村大河'),(106,'柳洞一成'),(108,'美綴綾子'),(110,'リーゼリット'),(112,'セラ'),(114,'蒔寺楓'),(115,'氷室鐘'),(116,'三枝由紀香'),(117,'WEAPONS'),(141,'ROUGH COLLECTION'),(142,'キャラクターラフ'),(216,'武器ラフ'),(221,'タロットカードラフ'),(228,'イベントラフ'),(248,'版権絵・その他ラフ')],
'CM_III':[(3,'RECORD OF HEAVENS FEEL'),(4,'聖杯戦争'),(12,'サーヴァントシステム'),(19,'第五次聖杯戦争参戦サーヴァント'),(20,'アルトリア'),(22,'クー・フーリン'),(24,'ギルガメッシュ'),(26,'エミヤ'),(28,'メドゥーサ'),(30,'メディア'),(32,'ハサン・サッバーハ'),(34,'佐々木小次郎'),(36,'ヘラクレス'),(38,'サーヴァントの黒化'),(39,'THEORY OF MAGIC'),(40,'魔術'),(50,'魔術世界の二大組織'),(53,'BACKGROUND ART'),(113,'TIGER DOJO'),(129,'FREQUENTLY ASKED QUESTIONS'),(137,'Fate/complete material Réalta Nua'),(138,'ART WORKS'),(242,'CHARACTERS'),(250,'OFFICIAL ILLUSTRATION'),(289,'LAST EPISODE')],
'CM_IV':[(3,'Fate/unlimited codes'),(4,'Fate/unlimited codes / CHARACTERS'),(74,'Fate/unlimited codes / OFFICIAL ILLUSTRATION'),(99,'Fate/tiger colosseum & UPPER'),(100,'Fate/tiger colosseum & UPPER / CHARACTERS'),(182,'Fate/tiger colosseum & UPPER / BACKGROUND ART'),(190,'Fate/tiger colosseum & UPPER / TAROT CARD'),(202,'Fate/tiger colosseum & UPPER / OFFICIAL ILLUSTRATION'),(245,'Fate/EXTRA'),(246,'Fate/EXTRA / CHARACTERS'),(261,'Fate/Zero'),(262,'Fate/Zero / CHARACTERS'),(272,'Fate/Zero / OFFICIAL ILLUSTRATION'),(295,'Fate/Apocrypha'),(296,'ジークフリード'),(300,'カルナ'),(304,'ヴラド三世'),(306,'武蔵坊弁慶'),(308,'ダビデ'),(312,'アタランテ'),(316,'ゲオルギウス'),(318,'アストルフォ'),(322,'シェイクスピア'),(326,'ジャック・ザ・リッパー'),(330,'セミラミス'),(332,'フランケンシュタイン'),(336,'スパルタクス'),(338,'坂田金時'),(342,'Fate/Apocrypha の真実')],
'CM_V':[(3,'PROLOGUE'),(11,'CHARACTERS'),(12,'セイバー'),(24,'遠坂凛'),(36,'間桐桜'),(44,'ライダー'),(52,'イリヤスフィール・フォン・アインツベルン'),(55,'衛宮士郎'),(56,'アーチャー'),(60,'ランサー'),(66,'ギルガメッシュ'),(68,'キャスター'),(79,'アサシン'),(80,'藤村大河'),(84,'間桐慎二'),(85,'美綴綾子'),(87,'美綴実典'),(88,'柳洞一成'),(90,'柳洞零観'),(91,'蛍塚音子'),(92,'蒔寺楓'),(94,'氷室鐘'),(96,'三枝由紀香'),(98,'リーゼリット'),(100,'セラ'),(102,'ルヴィアゼリッタ・エーデルフェルト'),(105,'HOLLOW the first part'),(137,'BACKGROUND ART'),(171,'ART GALLERY'),(172,'OFFICIAL ILLUSTRATION'),(202,'GUEST WALLPAPER'),(212,'ROUGH COLLECTION'),(227,'SPECIAL CONTENTS'),(228,'トラぶる花札道中記'),(258,'開運 遠坂神社'),(262,'風雲 イリヤ城'),(269,'HOLLOW the latter part'),(270,'カレン・オルテンシア'),(278,'バゼット・フラガ・マクレミッツ'),(283,'アヴェンジャー'),(341,'LAST TALK'),(344,'奥付')],
'SIDE':[(2,'Fate/side side materiale 1'),(32,'Fate/side side materiale 2'),(66,'Fate/side side materiale 3'),(100,'Fate/side side materiale 4')]
}
CHAR={
'Saber':['Saber','セイバー','アルトリア'], 'Shirou':['Shirou','Shiro','衛宮士郎'], 'Rin':['Rin','遠坂凛','远坂凛','Rin Tohsaka'], 'Archer':['Archer','アーチャー','エミヤ'], 'Sakura':['Sakura','間桐桜'], 'Lancer':['Lancer','ランサー','クー・フーリン'], 'Rider':['Rider','ライダー','メドゥーサ'], 'Caster':['Caster','キャスター','メディア'], 'Assassin':['Assassin','アサシン','佐々木小次郎'], 'TrueAssassin':['真アサシン','ハサン・サッバーハ'], 'Berserker':['Berserker','バーサーカー','ヘラクレス'], 'Illya':['Illya','イリヤスフィール'], 'Kirei':['Kirei','言峰綺礼'], 'Taiga':['Taiga','藤村大河'], 'Gilgamesh':['Gilgamesh','ギルガメッシュ'], 'Bazett':['Bazett','バゼット'], 'Caren':['Caren','カレン・オルテンシア'], 'Avenger':['Avenger','アヴェンジャー'], 'Leysritt':['リーゼリット'], 'Sella':['セラ'], 'Luvia':['ルヴィアゼリッタ'], 'Shinji':['間桐慎二'], 'Zouken':['間桐臓硯'], 'Kuzuki':['葛木宗一郎'], 'Issei':['柳洞一成'], 'Ayako':['美綴綾子'], 'Kaede':['蒔寺楓'], 'Kane':['氷室鐘'], 'Yukika':['三枝由紀香'], 'RyudouReikan':['柳洞零観'], 'Hotaruzuka':['蛍塚音子'], 'MitsuzuriMinori':['美綴実典']
}
# English search labels explicitly supplied by the user; Japanese forms activate only when found in a page.
TOPICS={
'Excalibur':('np',['Excalibur','エクスカリバー','約束された勝利の剣']),
'Gáe Bolg':('np',['Gáe Bolg','Gae Bolg','ゲイ・ボルク','刺し穿つ死棘の槍']),
'Kanshou':('weapon',['Kanshou','干将']), 'Bakuya':('weapon',['Bakuya','莫耶']),
'Rule Breaker':('np',['Rule Breaker','ルールブレイカー','破戒すべき全ての符']),
'Avalon':('np',['Avalon','アヴァロン','全て遠き理想郷']),
'UBW':('np',['Unlimited Blade Works','無限の剣製','アンリミテッドブレイドワークス']),
'Projection':('magic',['Projection','投影']), 'Reinforcement':('magic',['Reinforcement','強化']),
'Command Spell':('magic',['Command Spell','令呪']), 'Jewel':('magic',['Jewel','宝石魔術','宝石']),
'Bounded Field':('magic',['Bounded Field','結界']), 'Magecraft':('magic',['Magecraft','魔術']),
'Holy Grail War':('term',['聖杯戦争']), 'Servant':('term',['サーヴァント']), 'Noble Phantasm':('term',['Noble Phantasm','宝具']),
'Winter Town':('term',['冬木市']), 'Clock Tower':('term',['時計塔']), 'Holy Church':('term',['聖堂教会'])
}
VOCAB=['Cover','Contents','CharacterDesign','CharacterProfile','Expression','Costume','Pose','WeaponDesign','NoblePhantasm','Magic','EffectReference','CG','EventCG','Background','WorldSetting','Location','Item','ConceptArt','Storyboard','Layout','ProductionArt','UI','Typography','Interview','TextReference','Misc','Unknown']
USER_CANONICAL={'Saber','Shirou','Rin','Archer','Sakura','Lancer','Rider','Caster','Assassin','Berserker','Illya','Kirei','Taiga','Gilgamesh','Bazett','Caren','Avenger'}
# Names outside the user's supplied vocabulary retain their original printed Japanese form.
CHAR={name if name in USER_CANONICAL else als[0]:als for name,als in CHAR.items()}
TOPICS={name if kind!='term' or name=='Noble Phantasm' else als[0]:(kind,als) for name,(kind,als) in TOPICS.items()}
def contains(text,alias):
    if re.fullmatch(r'[\w .áÁ-]+',alias,flags=re.ASCII):return re.search(r'(?<![A-Za-z])'+re.escape(alias)+r'(?![A-Za-z])',text,re.I) is not None
    return alias in text
def run():
    rows=readjl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl');ocridx={r['page_id']:r for r in readjl(M/'OCR_INDEX.jsonl')};bookidx=readjson(M/'BOOKS.json');evidence=[];toc=[];aliases=[];weapon=[];npidx=[];magic=[];terms=[];cg=[];costumes=[];expressions=[];entityhits=[]
    for r in rows:r['book_title']=BOOKS[r['book_id']][1]
    for b in bookidx:b['title']=BOOKS[b['book_id']][1]
    writejson(M/'BOOKS.json',bookidx);csvout(M/'OFFICIAL_MATERIAL_BOOK_INDEX.csv',bookidx)
    annotation={'created_at':now(),'review_method':'Direct visual inspection of six TOC source images; manually transcribed independently of raw OCR','toc':TOC,'reviewed_images':[str(T/(b+'_toc_review.png')) for b in BOOKS],'range_end_method':'next listed section start - 1; last section to last numbered scan; implied ranges, not explicit printed end','scope_note':'No section context confirms a depicted character. Alias keys are search labels, not artwork identity.'};writejson(M/'MANUAL_TOC_TRANSCRIPTION.json',annotation)
    for b in bookidx:
        group=[r for r in rows if r['book_id']==b['book_id'] and r['scan_variant']==b['scan_variant']];nmap={int(m[1]):r for r in group if (m:=re.search(r'_(\d+)$',pathlib.Path(r['source_member']).stem)) and 0<int(m[1])<999};maxnum=max(nmap,default=0)
        for i,(start,title) in enumerate(TOC[b['book_id']]):
            end=TOC[b['book_id']][i+1][0]-1 if i+1<len(TOC[b['book_id']]) else maxnum;sid=b['book_id']+'_'+b['scan_variant']+'_S'+str(i+1).zfill(3);first=nmap.get(start);last=nmap.get(end)
            toc.append({'book_id':b['book_id'],'scan_variant':b['scan_variant'],'section_id':sid,'section_title':title,'printed_page_start':start,'printed_page_end':end,'scan_page_start':first['scan_page'] if first else None,'scan_page_end':last['scan_page'] if last else None,'confidence':None,'status':'manual_verified_toc; scan mapping source_sequence_correlated','evidence':str(R/'OCR/Raw/TOC'/(b['book_id']+'.evidence.json'))+'; visually transcribed TOC; matching numbered scan sequence; implied range ends'})
            for p in range(start,end+1):
                if p not in nmap:continue
                r=nmap[p];r['section']=title;r['section_context']=title;r['section_id']=sid
                candidates=[name for name,als in CHAR.items() if any(contains(title,a) for a in als)];r['characters_candidate']=sorted(set(candidates));r['candidate_evidence']='toc_context' if candidates else ''
                evidence.append({'page_id':r['page_id'],'tag_type':'section','tag':title,'evidence_type':'toc_context','source_text':f'{start:03d} {title}','source_region':'TOC; exact start; end derived from next start','confidence':None,'status':'section_context'})
                for name in candidates:evidence.append({'page_id':r['page_id'],'tag_type':'character','tag':name,'evidence_type':'toc_context','source_text':title,'source_region':'TOC','confidence':None,'status':'candidate'})
                roles=[]
                if 'EVENT VISUAL' in title:roles=['EventCG']
                if 'IMAGE VISUAL Effect' in title:roles=['EffectReference']
                if 'ART WORKS' in title or 'ILLUSTRATION' in title or 'ART GALLERY' in title or 'WALLPAPER' in title:roles=['ConceptArt']
                if 'BACKGROUND ART' in title:roles=['Background']
                if title in ['WEAPONS','武器ラフ']:roles=['WeaponDesign']
                if 'ラフ' in title or 'ROUGH COLLECTION' in title:roles=roles+['ProductionArt']
                if title in ['聖杯戦争','サーヴァントシステム','THEORY OF MAGIC','魔術','魔術世界の二大組織']:roles=['WorldSetting','TextReference']+(['Magic'] if 'MAGIC' in title or '魔術' in title else [])
                if roles:
                    r['page_role']=sorted(set(roles))
                    for role in roles:evidence.append({'page_id':r['page_id'],'tag_type':'page_role','tag':role,'evidence_type':'toc_context','source_text':title,'source_region':'TOC range','confidence':None,'status':'section_context'})
        if group:
            group[0]['page_role']=['Cover'];evidence.append({'page_id':group[0]['page_id'],'tag_type':'page_role','tag':'Cover','evidence_type':'manual_confirmed','source_text':'Cover design visually reviewed','source_region':'full page','confidence':None,'status':'confirmed'})
        for r in group:
            if pathlib.Path(r['source_member']).name.endswith('_002.jpg') and b['book_id']!='SIDE' or pathlib.Path(r['source_member']).name=='fsmc_001.jpg':
                r['page_role']=['Contents'];evidence.append({'page_id':r['page_id'],'tag_type':'page_role','tag':'Contents','evidence_type':'manual_confirmed','source_text':'CONTENTS / INDEX visually reviewed','source_region':'full page','confidence':None,'status':'confirmed'})
    # Manual sample tags describe roles, never unlabelled character identities or emotions.
    sample_roles={'CM_I':{4:['EventCG'],9:['EventCG','EffectReference']},'CM_II':{4:['CharacterProfile'],5:['CharacterDesign','Expression','Costume'],6:['CharacterDesign','Expression','Costume']},'CM_III':{4:['WorldSetting','TextReference'],5:['WorldSetting','Layout'],8:['Location','WorldSetting'],9:['Magic','EffectReference']},'CM_IV':{4:['CharacterProfile'],6:['Expression'],12:['Expression']},'CM_V':{4:['TextReference'],5:['EventCG','TextReference'],12:['CharacterDesign','Expression','Costume']},'SIDE':{4:['ProductionArt','TextReference'],5:['CharacterDesign'],6:['Storyboard','ProductionArt'],7:['Storyboard','ProductionArt'],8:['TextReference'],9:['TextReference']}}
    observed_aliases=collections.defaultdict(list)
    for r in rows:
        o=ocridx[r['page_id']];rawres=readjson(pathlib.Path(o['raw_text_path']).with_suffix('.result.json'));text=pathlib.Path(o['normalized_text_path']).read_text(encoding='utf-8');r['ocr_excerpt']=text[:240];blocks=rawres.get('blocks',[])
        m=re.search(r'_(\d+)$',pathlib.Path(r['source_member']).stem);filename_number=int(m[1]) if m else None
        if filename_number and 0<filename_number<999:
            r['filename_page_hint']=filename_number
            for block in blocks:
                for w in block.get('words',[]):
                    num=re.sub(r'[^0-9]','',w['text'])
                    if w['y']>r['height']*.88 and re.fullmatch(r'\d{1,3}',w['text'].strip()) and num and int(num)==filename_number and w['confidence']>=80:
                        r.update(printed_page=filename_number,printed_page_number=filename_number,printed_page_label=w['text'],printed_page_evidence='ocr_exact footer + source number corroboration');evidence.append({'page_id':r['page_id'],'tag_type':'printed_page','tag':str(filename_number),'evidence_type':'ocr_exact','source_text':w['text'],'source_region':{'x':w['x'],'y':w['y'],'width':w['width'],'height':w['height']},'confidence':w['confidence'],'status':'confirmed'});break
        num=filename_number
        if num in sample_roles.get(r['book_id'],{}) and r['scan_variant']=='PRIMARY':
            r['page_role']=sample_roles[r['book_id']][num]
            for role in r['page_role']:evidence.append({'page_id':r['page_id'],'tag_type':'page_role','tag':role,'evidence_type':'manual_confirmed','source_text':'Direct sample visual review; no emotion or unlabelled character inferred','source_region':'full page','confidence':None,'status':'confirmed'})
        for name,als in CHAR.items():
            for alias in als:
                matching=[b for b in blocks if contains(b['text'],alias)]
                if not matching:continue
                observed_aliases[(name,alias)].append(r['page_id']);best=max(matching,key=lambda b:b['confidence']);strong=best['confidence']>=85;status='confirmed_text_reference' if strong else 'ocr_candidate'
                (r['characters_confirmed'] if strong else r['characters_candidate']).append(name)
                ev={'page_id':r['page_id'],'tag_type':'character','tag':name,'evidence_type':'ocr_exact','source_text':best['text'],'source_region':{k:best[k] for k in ['x','y','width','height']},'confidence':best['confidence'],'status':status};evidence.append(ev);entityhits.append({**ev,'book_id':r['book_id'],'page_asset_id':r['page_asset_id'],'alias_matched':alias,'scope':'name referenced in page text; depicted presence not asserted'})
                break
        for name,(kind,als) in TOPICS.items():
            matching=[(a,b) for a in als for b in blocks if contains(b['text'],a)]
            if not matching:continue
            alias,block=max(matching,key=lambda x:x[1]['confidence']);ambiguous=alias in ['強化','投影','結界','魔術','Jewel','宝石'];status='confirmed_text_reference' if block['confidence']>=85 and not ambiguous else 'ocr_candidate';r['keywords'].extend([name,alias]);observed_aliases[(name,alias)].append(r['page_id']);ev={'page_id':r['page_id'],'tag_type':kind,'tag':name,'evidence_type':'ocr_exact','source_text':block['text'],'source_region':{k:block[k] for k in ['x','y','width','height']},'confidence':block['confidence'],'status':status};evidence.append(ev)
            common={'book':r['book_id'],'page':r['page_id'],'page_asset_id':r['page_asset_id'],'name':name,'original_name':alias,'character':'','source_text':block['text'],'evidence':json.dumps(ev,ensure_ascii=False),'status':status,'page_role':r['page_role']}
            if kind=='weapon':weapon.append({**common,'weapon_name':name})
            elif kind=='np':npidx.append(common);weapon.append({**common,'weapon_name':name,'classification':'named NP textual reference; weapon applicability not asserted'})
            elif kind=='magic':magic.append(common)
            else:terms.append({**common,'term':name,'original_term':alias,'heading':r['section'],'context_snippet':block['text'],'language':'Japanese' if re.search(r'[\u3000-\u9fff]',alias) else 'English'})
        r['characters_confirmed']=sorted(set(r['characters_confirmed']));r['characters_candidate']=sorted(set(r['characters_candidate'])-set(r['characters_confirmed']));r['keywords']=sorted(set(r['keywords']));r['notes']='Filename numbering retained as source metadata; printed numbering requires visible/OCR evidence. Confirmed characters identify printed text references, not guaranteed depicted figures.'
        if 'EventCG' in r['page_role'] or r['book_id']=='CM_I' and r['section']:
            route=''
            if r['section']=='EVENT VISUAL Fate':route='Fate'
            elif r['section']=='EVENT VISUAL Unlimited Blade Works':route='Unlimited Blade Works'
            elif r['section']=='EVENT VISUAL Heavens Feel':route='Heavens Feel'
            cg.append({'page':r['page_id'],'page_asset_id':r['page_asset_id'],'image_region':'','caption':'','route':route,'scene':'','characters':r['characters_confirmed'],'status':'section_context_only; artwork not split','evidence':r['section']})
        if 'Costume' in r['page_role']:costumes.append({'character':r['characters_confirmed'],'costume_name':'','description':'','page':r['page_id'],'variant':'','evidence':'manual page-role review; no invented costume names','status':'unnamed_costume_reference'})
        if 'Expression' in r['page_role']:expressions.append({'page':r['page_id'],'page_role':'Expression','label':'expression_sheet','official_emotion_labels':'','evidence':'manual visual role review; no inferred emotions','status':'confirmed_role'})
    for (name,alias),pages in observed_aliases.items():aliases.append({'entity':name,'alias':alias,'source':'official_material_page_text','source_pages':sorted(set(pages)),'status':'observed_ocr_text','purpose':'search normalization only; no page identity assertion'})
    # Seed English/Chinese search aliases explicitly provided by user; kept distinct from official evidence.
    for name,als in CHAR.items():
        for alias in als:
            if alias==name or alias in ['远坂凛','Rin Tohsaka','Shiro']:aliases.append({'entity':name,'alias':alias,'source':'user_task_vocabulary' if alias!='Shiro' else 'existing_Europe_character_code_map','source_pages':[],'status':'search_alias_only','purpose':'lookup seed, not evidence of presence'})
    for name,(kind,als) in TOPICS.items():
        for alias in list(dict.fromkeys([name]+als)):
            if re.search(r'[A-Za-z]',alias):aliases.append({'entity':name,'alias':alias,'source':'user_task_topic_vocabulary','source_pages':[],'status':'search_alias_only','purpose':'Latin search alias, never substituted into original Japanese source text'})
    aliases.append({'entity':'SIDE','alias':'Fate/side material complete','source':'user_task_title_alias','source_pages':[],'status':'search_alias_only','purpose':'Original request spelling; actual printed title is Fate/side side materiale complete'})
    writejl(M/'OFFICIAL_MATERIAL_PAGE_INDEX.jsonl',rows);csvout(M/'OFFICIAL_MATERIAL_PAGE_INDEX.csv',rows);csvout(M/'OFFICIAL_MATERIAL_TOC.csv',toc);writejson(M/'TOC.json',toc);csvout(M/'OFFICIAL_MATERIAL_TAG_EVIDENCE.csv',evidence);writejl(M/'TAG_EVIDENCE.jsonl',evidence);csvout(M/'OFFICIAL_MATERIAL_ENTITY_ALIASES.csv',aliases);writejson(M/'ALIASES.json',aliases);csvout(M/'OFFICIAL_MATERIAL_CHARACTER_INDEX.csv',entityhits,['page_id','page_asset_id','book_id','tag','alias_matched','evidence_type','source_text','source_region','confidence','status','scope']);csvout(M/'OFFICIAL_MATERIAL_WEAPON_INDEX.csv',weapon,['book','page','page_asset_id','weapon_name','original_name','character','source_text','evidence','status','classification']);csvout(M/'OFFICIAL_MATERIAL_NOBLE_PHANTASM_INDEX.csv',npidx,['book','page','page_asset_id','name','original_name','character','page_role','source_text','evidence','status']);csvout(M/'OFFICIAL_MATERIAL_MAGIC_INDEX.csv',magic,['book','page','page_asset_id','name','original_name','source_text','evidence','status']);csvout(M/'OFFICIAL_MATERIAL_TERM_INDEX.csv',terms,['term','original_term','book','page','heading','context_snippet','language','status','evidence']);csvout(M/'OFFICIAL_MATERIAL_CG_INDEX.csv',cg,['page','page_asset_id','image_region','caption','route','scene','characters','status','evidence']);csvout(M/'OFFICIAL_MATERIAL_COSTUME_INDEX.csv',costumes,['character','costume_name','description','page','variant','evidence','status']);csvout(M/'OFFICIAL_MATERIAL_EXPRESSION_INDEX.csv',expressions,['page','page_role','label','official_emotion_labels','evidence','status']);csvout(M/'OFFICIAL_MATERIAL_IMAGE_REGIONS.csv',[],['page_id','region_id','bbox','caption','linked_character','role','confidence']);writejson(M/'PAGE_ROLE_VOCABULARY.json',VOCAB)
    log('SEMANTICS',len(toc),'TOC sections',len(evidence),'evidence rows',len(entityhits),'character text hits')
if __name__=='__main__':run()
