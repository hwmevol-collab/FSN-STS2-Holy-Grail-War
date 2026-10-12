const{ready,take,command}=require('./record.cjs');
const c=(card,up=false)=>({card,up});
const play=(card,choices=[],hold=3)=>({command:'play',params:{card,choices},hold});
(async()=>{
 await ready();await command('combat',{archer:true});
 await command('setup',{cards:[c('RIN_S_GANDR'),c('RIN_S_JEWEL_PREPARATION'),c('RIN_S_JEWEL_RELEASE'),c('RIN_S_MANA_SUPPLY'),c('RIN_S_MANA_SUPPLY'),c('ARC-R13',true),c('ARC-R08',true),c('ARC_S_TRACE',true),c('ARC_S_CLOSE_COMBAT'),c('ARC_S_BOW_SHOT'),c('ARC_S_DEFLECT')]});await command('clean-overlays');
 await take('06_projection_build',53,[play('ARC-R13',[],4),play('ARC-R08',[],4),play('ARC_S_TRACE',['ARM_KANSHOU_BAKUYA'],4),play('ARM_KANSHOU_BAKUYA',[],4),play('ARM_HRUNTING',['1'],4),play('ARC_S_TRACE',['ARM_RHO_AIAS'],2),play('ARM_RHO_AIAS',[],3)]);
 await command('deck');await command('tab',{owner:'CHAR_RIN'});
 await take('07_dual_decks',28,[{command:'detail',hold:5},{command:'close-detail',hold:3},{command:'tab',params:{owner:'CHAR_ARCHER'},hold:5},{command:'detail',hold:5},{command:'close-detail',hold:2}]);
 await command('close-deck');await command('capture');
})().catch(e=>{console.error(e);process.exitCode=1;});
