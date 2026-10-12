// Replay in an initialized cua_repl session using its documented browser APIs.
// Native media controls: read a fresh AX tree or screenshot before clicking Play.
// This is a persistent acceptance recipe, not a claim of an unattended PASS.
async function acceptGallery(tab) {
  const checks=[];
  const read=()=>tab.playwright.evaluate(()=>({count:document.querySelector('#count').textContent,page:document.querySelector('#page').textContent}));
  for (const version of ['Original','Remastered','HollowAtaraxia']) {
    await tab.playwright.getByLabel('版本',{exact:true}).selectOption({label:version});
    checks.push({test:'version',version,...await read()});
  }
  await tab.playwright.getByRole('button',{name:'下一页',exact:true}).click();checks.push({test:'pagination',...await read()});
  await tab.playwright.getByRole('button',{name:'重置筛选',exact:true}).click();
  for (const id of ['FSN000380','FSN042471','FSN202604']) {
    await tab.playwright.getByLabel('搜索编号、文件名、路径、脚本场景').fill(id);
    await tab.playwright.getByText(id,{exact:true}).waitFor({state:'visible'});
    checks.push({test:'image',id,...await tab.playwright.evaluate(()=>({loaded:document.querySelector('.card img').complete&&document.querySelector('.card img').naturalWidth>0,href:document.querySelector('.card a').href}))});
  }
  return checks;
}
// Play-check IDs: Original audio FSN000047; Remastered audio FSN078239;
// FHA Opus FSN216988; FHA BGM FSN204245; FHA MP4 FSN215096.
// Legacy Theora case FSN042476 must be separately verified in real Chrome.
// After a real Play click, read: paused, currentTime, readyState, duration,
// error, and (for video) videoWidth/videoHeight. No synthetic play() in evaluate.
