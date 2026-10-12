const fs=require('fs');const cp=require('child_process');
const {ready,take,command,sleep}=require('./record.cjs');
const c=(card,up=false)=>({card,up});
const play=(card,choices=[],hold=3)=>({command:'play',params:{card,choices},hold});
const rin=[c('RIN_S_GANDR'),c('RIN_S_JEWEL_PREPARATION'),c('RIN_S_JEWEL_RELEASE'),c('RIN_S_MANA_SUPPLY'),c('RIN_S_MANA_SUPPLY')];
const archer=[c('ARC_S_TRACE'),c('ARC_S_CLOSE_COMBAT'),c('ARC_S_BOW_SHOT'),c('ARC_S_DEFLECT')];
async function setup(cards,active=false){await command('quit');await sleep(1500);fs.writeFileSync('E:/FSN_Trailer/qa/status.json',JSON.stringify({id:0,state:'LAUNCHING'}));cp.execFileSync('powershell.exe',['-NoProfile','-File','E:/FSN_Trailer/qa/launch.ps1'],{stdio:'inherit'});await ready();await command('combat',{archer:active});await command('setup',{cards});await command('clean-overlays');}
async function run(){
 await setup([...rin,...archer]);
 await take('03_rin_magic',38,[play('RIN_S_JEWEL_PREPARATION',[],3),play('RIN_S_GANDR',['BOOST'],4),play('RIN_S_MANA_SUPPLY',['GAIN_MANA'],2),play('RIN_S_JEWEL_RELEASE',['BOOST'],4)]);
 await setup([...rin,...archer],true);
 await take('04_archer_projection',38,[play('ARC_S_TRACE',['ARM_KANSHOU_BAKUYA'],4),play('ARM_KANSHOU_BAKUYA',[],4),play('ARC_S_CLOSE_COMBAT',[],4),play('ARC_S_BOW_SHOT',[],4)]);
 await setup([...rin,...archer]);
 await take('05_dual_switch',40,[play('RIN_S_GANDR',['BOOST'],3),{command:'switch',hold:4},play('ARC_S_TRACE',['ARM_KANSHOU_BAKUYA'],3),play('ARM_KANSHOU_BAKUYA',[],3),play('ARC_S_CLOSE_COMBAT',[],3),{command:'end',hold:3},{command:'switch',hold:3}]);
 await setup([...rin,c('ARC-R13',true),c('ARC-R08',true),c('ARC_S_TRACE',true),c('ARC_S_CLOSE_COMBAT'),c('ARC_S_BOW_SHOT'),c('ARC_S_DEFLECT')],true);
 await take('06_projection_build',53,[play('ARC-R13',[],4),play('ARC-R08',[],4),play('ARC_S_TRACE',['ARM_KANSHOU_BAKUYA'],4),play('ARM_KANSHOU_BAKUYA',[],4),play('ARM_HRUNTING',['1'],4),play('ARC_S_TRACE',['ARM_RHO_AIAS'],2),play('ARM_RHO_AIAS',[],3)]);
 await command('deck');await command('tab',{owner:'CHAR_RIN'});
 await take('07_dual_decks',28,[{command:'detail',hold:5},{command:'close-detail',hold:3},{command:'tab',params:{owner:'CHAR_ARCHER'},hold:5},{command:'detail',hold:5},{command:'close-detail',hold:2}]);
 await command('close-deck');await command('capture');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
