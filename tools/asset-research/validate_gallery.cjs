// Offline DOM simulation validates page logic and data without operating a browser.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=process.env.FSN_LIBRARY_ROOT||'E:/FSN_MASTER_ASSET_LIBRARY',gallery=root+'/Gallery';
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.value='';this.textContent='';this.listeners={};this.classList={toggle(){}};}
 append(...children){this.children.push(...children)} replaceChildren(...c){this.children=c} add(o){this.children.push(o)} addEventListener(k,f){this.listeners[k]=f} setAttribute(k,v){this[k]=v} remove(){this.removed=true} reset(){for(const k of ['query','version','route','category','format','container','resolution','minwidth'])els[k].value='';els.view.value='grid'}
}
const ids=['filters','query','version','route','category','format','container','resolution','minwidth','view','count','prev','next','reset','page','grid','loading'];const els=Object.fromEntries(ids.map(id=>[id,new Element()]));els.view.value='grid';
const document={getElementById:id=>els[id],createElement:tag=>new Element(tag),createDocumentFragment:()=>new Element('fragment')};const context={window:{},document,Option:class{constructor(text,value){this.text=text;this.value=value}},navigator:{clipboard:{writeText:async()=>{}}},setTimeout:f=>{f();return 1},clearTimeout(){},console};
vm.createContext(context);vm.runInContext(fs.readFileSync(gallery+'/catalog.js','utf8'),context,{timeout:30000});
const html=fs.readFileSync(gallery+'/index.html','utf8');const source=html.match(/<script>([\s\S]*?)<\/script>/)[1];vm.runInContext(source,context,{timeout:30000});
const M=context.window.FSN_META,A=context.window.FSN_ASSETS,results=[];function check(name,test){test();results.push({name,pass:true});}
function filter(){els.query.listeners.input();}
function renderedCards(){return els.grid.children[0]?.tag==='fragment'?els.grid.children[0].children:els.grid.children;}
check('Full index loads offline',()=>{assert.equal(A.length,M.count);assert.equal(renderedCards().length,Math.min(60,M.count));assert(!els.loading.textContent.includes('无法加载'));});
check('Asset identifier returns exact asset',()=>{els.query.value='FSN034199';filter();assert.equal(renderedCards().length,1);assert(els.count.textContent.includes('1 /'));});
check('No-result search clears cards',()=>{els.query.value='__nonexistent_asset_identifier__';filter();assert.equal(renderedCards()[0].className,'empty');assert(els.next.disabled);});
check('Voice filter provides playable audio controls',()=>{els.filters.reset();els.category.value=String(M.categories.indexOf('Voice'));els.category.listeners.change();assert(els.count.textContent.includes('115,924'));const cards=renderedCards();assert(cards.some(c=>c.children.flatMap(x=>x.children).some(x=>x.tag==='audio')));});
check('Combined version / route / resolution filtering',()=>{els.filters.reset();els.version.value='1';els.route.value=String(M.routes.indexOf('Fate / Saber'));els.minwidth.value='1280';els.minwidth.listeners.change();const expected=A.filter(a=>a[1]===1&&a[6]===Number(els.route.value)&&Number(a[8])>=1280).length;assert(els.count.textContent.startsWith('找到 '+expected.toLocaleString()));});
check('Pagination changes visible identifiers',()=>{els.filters.reset();filter();const old=renderedCards()[0].children[1].children[0].textContent;els.next.listeners.click();assert.notEqual(renderedCards()[0].children[1].children[0].textContent,old);assert(!els.prev.disabled);els.prev.listeners.click();assert.equal(renderedCards()[0].children[1].children[0].textContent,old);});
check('Declared local dependencies, no server fetch',()=>{assert(html.includes('src="catalog.js"'));assert(!/\bfetch\s*\(/.test(html));assert(!/<script[^>]+src=["']https?:/.test(html));assert(!/<link[^>]+href=["']https?:/.test(html));});
let checked=0,missing=[];const paths=new Set();for(const a of A){paths.add(a[3]);if(a[4])paths.add(a[4]);if(a[11])paths.add('Gallery/thumbnails/'+a[11]);}for(const p of paths){if(!fs.existsSync(path.join(root,p)))missing.push(p);checked++;}
check('All indexed local raw, working and thumbnail paths exist',()=>assert.equal(missing.length,0));
fs.writeFileSync(root+'/Reports/GALLERY_OFFLINE_LOGIC_QA.json',JSON.stringify({mode:'offline JavaScript/DOM simulation, not a real browser',tests:results,indexed_paths_checked:checked,missing,browser_validation:'blocked: browser tool security policy permits only HTTP/HTTPS; file:// opening not tested'},null,2));console.log(JSON.stringify({tests:results.length,paths_checked:checked,missing:missing.length}));
