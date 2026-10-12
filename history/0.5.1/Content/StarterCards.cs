using MegaCrit.Sts2.Core.Models.Powers;
using BaseLib.Extensions;
using MegaCrit.Sts2.Core.Saves.Runs;
namespace RinArcherCore;
public abstract class StarterCard : CustomCardModel
{
    protected StarterCard(CardType type,TargetType target=TargetType.Self,int energy=1,bool library=true,CardRarity rarity=CardRarity.Basic):base(energy,type,rarity,target,library,autoAdd:library){}
    public abstract string SourceCardId{get;}
    public abstract string OwnerCharacterId{get;}
    protected abstract string NameText{get;}
    protected abstract string RulesText{get;}
    [SavedProperty] public string InstanceId{get;set;}="";
    public virtual int PrintedManaCost=>0;
    public virtual int ModifiedManaCost=>PrintedManaCost;
    public virtual bool HasJewelChoice=>false;
    public override List<(string,string)> Localization=>[("title",NameText),("description","{Rules}"),("selectionScreenPrompt",NameText)];
    protected override void AddExtraArgsToDescription(MegaCrit.Sts2.Core.Localization.LocString description){base.AddExtraArgsToDescription(description);description.Add("Rules",RulesText.Replace("[MILESTONE B EFFECT PLACEHOLDER]","[lb]MILESTONE B EFFECT PLACEHOLDER[rb]"));}
    protected override bool IsPlayable=>ContractRuntime.For(Owner) is {} d&&d.StartingSelected&&!d.Finished&&d.Active.CharacterId==OwnerCharacterId
        &&d.CanSpendMana(d.EffectiveManaCost(OwnerCharacterId,PrintedManaCost,ModifiedManaCost));
    public override Texture2D? CustomPortrait=>PlaceholderVisuals.CardTexture(OwnerCharacterId=="CHAR_RIN");
    public override CardPoolModel Pool=>ModelDb.CardPool<RinArcherPool>();
    protected ContractRuntime Runtime=>ContractRuntime.For(Owner)??throw new InvalidOperationException("Card outside contract");
    protected async Task Hit(PlayerChoiceContext ctx,int damage,int hits=1,bool weak=false)
    {
        var d=Runtime;
        var profile=d.DamageProfile(this,damage,hits);
        for(int hit=0;hit<hits&&!d.Finished;hit++)await Targeting.EnemyDamage(ctx,d,ContractTarget.FRONT,profile[hit],d.Member(OwnerCharacterId).Creature,this,hit+1);
        if(weak&&d.Enemy?.Active is {} target&&target.IsAlive)await PowerCmd.Apply<WeakPower>(ctx,target,1,d.Rin.Creature,this);
    }
    protected Task Block(CardPlay play,int amount,CharacterRuntime? member=null){var recipient=member??Runtime.Member(OwnerCharacterId);Runtime.SetAlphaTarget(this,recipient.CharacterId);return CreatureCmd.GainBlock(recipient.Creature,Runtime.BlockAmount(this,recipient,amount),ValueProp.Move,play);}
    protected async Task<bool> Boost(){if(Runtime.Jewel==0)return false;return Runtime.UseJewelBoost(this,await JewelChoice.Ask(this));}
}
public abstract class RinStarter(CardType type,TargetType target=TargetType.Self):StarterCard(type,target)
{public override string OwnerCharacterId=>"CHAR_RIN";}
public abstract class ArcherStarter(CardType type,TargetType target=TargetType.Self):StarterCard(type,target)
{public override string OwnerCharacterId=>"CHAR_ARCHER";}
[Pool(typeof(RinArcherPool))]
public sealed class Gandr():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"RIN_S_GANDR";protected override string NameText=>"甘德射击";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"对敌方前场造成 {(IsUpgraded?8:6)} 点伤害。\n可选宝石强化：消耗 1 颗宝石，改为造成 {(IsUpgraded?12:9)} 点伤害，并施加 1 层虚弱。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){bool boost=await Boost();await Hit(ctx,boost?(IsUpgraded?12:9):(IsUpgraded?8:6),weak:boost);}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class RinReinforcement():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_REINFORCEMENT";protected override string NameText=>"强化";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"获得 {(IsUpgraded?7:5)} 点格挡。\n可选宝石强化：消耗 1 颗宝石，改为获得 {(IsUpgraded?11:9)} 点格挡。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await Block(play,await Boost()?(IsUpgraded?11:9):(IsUpgraded?7:5));
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class JewelPreparation():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_JEWEL_PREPARATION";protected override string NameText=>"宝石准备";
    protected override string RulesText=>"获得 1 颗宝石。\n抽 1 张牌。"+(IsUpgraded?"\n获得 3 点格挡。":"");
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){Runtime.GainJewel(1);await CardPileCmd.Draw(ctx,1,Owner);if(IsUpgraded)await Block(play,3);}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class ManaSupply():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_MANA_SUPPLY";protected override string NameText=>"供魔";
    protected override string RulesText=>$"获得 {(IsUpgraded?3:2)} 点契约魔力。";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play){Runtime.GainMana(IsUpgraded?3:2);return Task.CompletedTask;}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class ReinforceProjection():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_REINFORCE_PROJECTION";protected override string NameText=>"强化投影";
    public override bool HasJewelChoice=>true;
    protected override bool IsPlayable=>base.IsPlayable&&!Runtime.PendingReinforcement.Active;
    protected override string RulesText=>"弓兵下一次成功生成的投影武器获得强化。\n可选择消耗 1 颗宝石，使该武器在本场战斗中魔力消耗 -1。\n待生效时不可重复施加。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)
    {
        if(Runtime.PendingReinforcement.Active){Runtime.Log("PENDING_REINFORCEMENT_ALREADY_ACTIVE");return;}
        Runtime.ApplyReinforcement(await Boost());
    }
    protected override void OnUpgrade()=>EnergyCost.UpgradeBy(-1);
}
[Pool(typeof(RinArcherPool))]
public sealed class JewelRelease():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"RIN_S_JEWEL_RELEASE";protected override string NameText=>"宝石释放";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"对敌方前场造成 {(IsUpgraded?5:4)} 点伤害。\n玩家可选择消耗 1 颗宝石，改为造成 {(IsUpgraded?16:13)} 点伤害。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await Hit(ctx,await Boost()?(IsUpgraded?16:13):(IsUpgraded?5:4));
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class BowShot():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"ARC_S_BOW_SHOT";protected override string NameText=>"弓箭射击";
    protected override string RulesText=>$"对敌方前场造成 {(IsUpgraded?9:7)} 点伤害。";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Hit(ctx,IsUpgraded?9:7);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class CloseCombat():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"ARC_S_CLOSE_COMBAT";protected override string NameText=>"近身战斗";
    protected override string RulesText=>$"对敌方前场造成 {(IsUpgraded?4:3)} 点伤害两次。";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Hit(ctx,IsUpgraded?4:3,2);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Deflect():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_DEFLECT";protected override string NameText=>"格挡";
    protected override string RulesText=>$"获得 {(IsUpgraded?7:5)} 点格挡。";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Block(play,IsUpgraded?7:5);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Trace():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_TRACE";protected override string NameText=>"投影";
    internal string? PreparedArmId;
    protected override string RulesText=>"从当前三件武器库中选择 1 件投影武器，加入弓兵手牌。"+(IsUpgraded?"\n本次生成的武器在当前共享玩家回合中魔力消耗 -1。":"");
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)
    {
        var id=PreparedArmId;PreparedArmId=null;
        if(id==null)id=await AlphaChoice.AskArm(this);
        if(id!=null)await Runtime.GenerateArm(ctx,id,SourceCardId,IsUpgraded);
    }
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Cover():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_COVER";protected override string NameText=>"掩护";
    protected override string RulesText=>$"御主（凛）获得 {(IsUpgraded?10:7)} 点格挡。";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Block(play,IsUpgraded?10:7,Runtime.Rin);
    protected override void OnUpgrade(){}
}
public static class StarterDefinitions
{
    public static IEnumerable<CardModel> Rin=>[ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<JewelPreparation>(),ModelDb.Card<ManaSupply>(),ModelDb.Card<ReinforceProjection>(),ModelDb.Card<JewelRelease>()];
    public static IEnumerable<CardModel> Archer=>[ModelDb.Card<BowShot>(),ModelDb.Card<BowShot>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Trace>(),ModelDb.Card<Trace>(),ModelDb.Card<Cover>()];
}
