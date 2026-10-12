using MegaCrit.Sts2.Core.Models.Powers;
using BaseLib.Extensions;
using MegaCrit.Sts2.Core.Saves.Runs;
namespace RinArcherCore;
public abstract class StarterCard : CustomCardModel
{
    protected StarterCard(CardType type,TargetType target=TargetType.Self):base(1,type,CardRarity.Basic,target){}
    public abstract string SourceCardId{get;}
    public abstract string OwnerCharacterId{get;}
    protected abstract string NameText{get;}
    protected abstract string RulesText{get;}
    [SavedProperty] public string InstanceId{get;set;}="";
    public virtual int PrintedManaCost=>0;
    public virtual bool HasJewelChoice=>false;
    public override List<(string,string)> Localization=>[("title",NameText),("description","{Rules}"),("selectionScreenPrompt",NameText)];
    protected override void AddExtraArgsToDescription(MegaCrit.Sts2.Core.Localization.LocString description){base.AddExtraArgsToDescription(description);description.Add("Rules",RulesText.Replace("[MILESTONE B EFFECT PLACEHOLDER]","[lb]MILESTONE B EFFECT PLACEHOLDER[rb]"));}
    protected override bool IsPlayable=>ContractRuntime.For(Owner) is {} d&&d.StartingSelected&&!d.Finished&&d.Active.CharacterId==OwnerCharacterId
        &&d.CanSpendMana(d.EffectiveManaCost(OwnerCharacterId,PrintedManaCost,PrintedManaCost));
    public override Texture2D? CustomPortrait=>PlaceholderVisuals.CardTexture(OwnerCharacterId=="CHAR_RIN");
    public override CardPoolModel Pool=>ModelDb.CardPool<RinArcherPool>();
    protected ContractRuntime Runtime=>ContractRuntime.For(Owner)??throw new InvalidOperationException("Card outside contract");
    protected async Task Hit(PlayerChoiceContext ctx,int damage,int hits=1,bool weak=false)
    {
        var d=Runtime;
        for(int hit=0;hit<hits;hit++)await Targeting.EnemyDamage(ctx,d,ContractTarget.FRONT,damage,d.Member(OwnerCharacterId).Creature,this,hit+1);
        if(weak&&d.Enemy?.Active is {} target&&target.IsAlive)await PowerCmd.Apply<WeakPower>(ctx,target,1,d.Rin.Creature,this);
    }
    protected Task Block(CardPlay play,int amount,CharacterRuntime? member=null)=>CreatureCmd.GainBlock((member??Runtime.Member(OwnerCharacterId)).Creature,amount,ValueProp.Move,play);
    protected async Task<bool> Boost(){if(Runtime.Jewel==0)return false;return Runtime.SpendJewel(await JewelChoice.Ask(this));}
}
public abstract class RinStarter(CardType type,TargetType target=TargetType.Self):StarterCard(type,target)
{public override string OwnerCharacterId=>"CHAR_RIN";}
public abstract class ArcherStarter(CardType type,TargetType target=TargetType.Self):StarterCard(type,target)
{public override string OwnerCharacterId=>"CHAR_ARCHER";}
[Pool(typeof(RinArcherPool))]
public sealed class Gandr():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"RIN_S_GANDR";protected override string NameText=>"Gandr";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"Deal {(IsUpgraded?8:6)} Damage to FRONT.\nOptional Jewel Boost: Consume 1 Jewel → Deal {(IsUpgraded?12:9)} instead → Apply 1 Weak.";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){bool boost=await Boost();await Hit(ctx,boost?(IsUpgraded?12:9):(IsUpgraded?8:6),weak:boost);}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class RinReinforcement():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_REINFORCEMENT";protected override string NameText=>"Reinforcement";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"Gain {(IsUpgraded?7:5)} Block.\nOptional Jewel Boost: Consume 1 Jewel → Gain {(IsUpgraded?11:9)} Block instead.";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await Block(play,await Boost()?(IsUpgraded?11:9):(IsUpgraded?7:5));
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class JewelPreparation():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_JEWEL_PREPARATION";protected override string NameText=>"Jewel Preparation";
    protected override string RulesText=>"Gain 1 Jewel.\nDraw 1."+(IsUpgraded?"\nGain 3 Block.":"");
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){Runtime.GainJewel(1);await CardPileCmd.Draw(ctx,1,Owner);if(IsUpgraded)await Block(play,3);}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class ManaSupply():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_MANA_SUPPLY";protected override string NameText=>"Mana Supply";
    protected override string RulesText=>$"Gain {(IsUpgraded?3:2)} Contract Mana.";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play){Runtime.GainMana(IsUpgraded?3:2);return Task.CompletedTask;}
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class ReinforceProjection():RinStarter(CardType.Skill)
{
    public override string SourceCardId=>"RIN_S_REINFORCE_PROJECTION";protected override string NameText=>"Reinforce Projection";
    protected override string RulesText=>"[MILESTONE B EFFECT PLACEHOLDER]";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Task.CompletedTask;
    protected override void OnUpgrade()=>EnergyCost.UpgradeBy(-1);
}
[Pool(typeof(RinArcherPool))]
public sealed class JewelRelease():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"RIN_S_JEWEL_RELEASE";protected override string NameText=>"Jewel Release";
    public override bool HasJewelChoice=>true;
    protected override string RulesText=>$"Deal {(IsUpgraded?5:4)} Damage to FRONT.\nPlayer may choose: Consume 1 Jewel → Deal {(IsUpgraded?16:13)} instead.";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await Hit(ctx,await Boost()?(IsUpgraded?16:13):(IsUpgraded?5:4));
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class BowShot():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"ARC_S_BOW_SHOT";protected override string NameText=>"Bow Shot";
    protected override string RulesText=>$"Deal {(IsUpgraded?9:7)} Damage to FRONT.";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Hit(ctx,IsUpgraded?9:7);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class CloseCombat():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{
    public override string SourceCardId=>"ARC_S_CLOSE_COMBAT";protected override string NameText=>"Close Combat";
    protected override string RulesText=>$"Deal {(IsUpgraded?4:3)} Damage twice to FRONT.";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Hit(ctx,IsUpgraded?4:3,2);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Deflect():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_DEFLECT";protected override string NameText=>"Deflect";
    protected override string RulesText=>$"Gain {(IsUpgraded?7:5)} Block.";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Block(play,IsUpgraded?7:5);
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Trace():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_TRACE";protected override string NameText=>"Trace";
    protected override string RulesText=>"[MILESTONE B EFFECT PLACEHOLDER]";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Task.CompletedTask;
    protected override void OnUpgrade(){}
}
[Pool(typeof(RinArcherPool))]
public sealed class Cover():ArcherStarter(CardType.Skill)
{
    public override string SourceCardId=>"ARC_S_COVER";protected override string NameText=>"Cover";
    protected override string RulesText=>$"Master gains {(IsUpgraded?10:7)} Block.";
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>Block(play,IsUpgraded?10:7,Runtime.Rin);
    protected override void OnUpgrade(){}
}
public static class StarterDefinitions
{
    public static IEnumerable<CardModel> Rin=>[ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<JewelPreparation>(),ModelDb.Card<ManaSupply>(),ModelDb.Card<ReinforceProjection>(),ModelDb.Card<JewelRelease>()];
    public static IEnumerable<CardModel> Archer=>[ModelDb.Card<BowShot>(),ModelDb.Card<BowShot>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Trace>(),ModelDb.Card<Trace>(),ModelDb.Card<Cover>()];
}
