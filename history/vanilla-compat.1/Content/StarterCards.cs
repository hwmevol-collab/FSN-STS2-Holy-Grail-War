using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Saves.Runs;
using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.HoverTips;
namespace RinArcherCore;
public abstract class StarterCard : CustomCardModel
{
    protected StarterCard(CardType type,TargetType target=TargetType.Self,int energy=1,bool library=true,CardRarity rarity=CardRarity.Basic):base(energy,type,rarity,target,library,autoAdd:library){}
    public abstract string SourceCardId{get;}
    public abstract string OwnerCharacterId{get;}
    protected abstract string NameText{get;}
    protected virtual string RulesText=>GameplayCatalog.Text(this);
    protected override IEnumerable<IHoverTip> ExtraHoverTips=>GameplayCatalog.Tips(this).Concat(ContractCostArtwork.HoverTips(this));
    [SavedProperty] public string InstanceId{get;set;}="";
    public virtual int PrintedManaCost=>GameplayCatalog.Cards.TryGetValue(SourceCardId,out var s)?(IsUpgraded?s.UpMana:s.Mana):0;
    public virtual int ModifiedManaCost=>PrintedManaCost;
    public virtual bool HasJewelChoice=>false;
    internal GameplayPlayPlan? Plan;
    public override List<(string,string)> Localization=>[("title",GameplayCatalog.Cards.ContainsKey(SourceCardId)?FsnLoc.Name(this):NameText),("description","{Rules}"),("selectionScreenPrompt",GameplayCatalog.Cards.ContainsKey(SourceCardId)?FsnLoc.Name(this):NameText)];
    protected override void AddExtraArgsToDescription(LocString description)
    {
        base.AddExtraArgsToDescription(description);
        var d=ContractRuntime.For(Owner);var state=d is {Finished:false}&&Pile?.Type is PileType.Hand or PileType.Play?GameplayRules.Availability(d,this):"";
        description.Add("Rules",PresentationCopy.CardRules(RulesText,this,d).Replace("[MILESTONE B EFFECT PLACEHOLDER]","[lb]MILESTONE B EFFECT PLACEHOLDER[rb]")+(state.Length>0?"\n"+FsnLoc.Format("UNAVAILABLE",state):""));
    }
    protected override bool IsPlayable=>ContractRuntime.For(Owner) is {} d&&d.StartingSelected&&!d.Finished&&d.Active.CharacterId==OwnerCharacterId
        &&d.CanSpendMana(d.EffectiveManaCost(OwnerCharacterId,PrintedManaCost,ModifiedManaCost))&&GameplayRules.Availability(d,this).Length==0;
    public override Texture2D? CustomPortrait=>PresentationTheme.Portrait(this);
    public override Texture2D? CustomFrame=>PresentationTheme.Frame(this);
    public override CardPoolModel Pool=>ModelDb.CardPool<RinArcherPool>();
    protected ContractRuntime Runtime=>ContractRuntime.For(Owner)??throw new InvalidOperationException("Card outside contract");
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)
    {await PresentationEffects.Play(Runtime,this);await GameplayRules.Play(ctx,play,Runtime,this);}
    protected async Task Hit(PlayerChoiceContext ctx,int damage,int hits=1,bool weak=false)
    {
        var d=Runtime;var target=d.PlayTarget(this);if(target==null||!target.IsAlive)return;
        var profile=d.DamageProfile(this,damage,hits);
        for(int hit=0;hit<hits&&!d.Finished&&target.IsAlive;hit++)await Targeting.Damage(ctx,d,ContractTarget.ANY_CONTRACT_MEMBER,profile[hit],d.Member(OwnerCharacterId).Creature,this,true,hit+1,target);
        if(weak&&target.IsAlive)await PowerCmd.Apply<WeakPower>(ctx,target,1,d.Rin.Creature,this);
    }
    protected Task Block(CardPlay play,int amount,CharacterRuntime? member=null){var recipient=member??Runtime.Member(OwnerCharacterId);Runtime.SetAlphaTarget(this,recipient.CharacterId);return CreatureCmd.GainBlock(recipient.Creature,Runtime.BlockAmount(this,recipient,amount),ValueProp.Move,play);}
    protected Task<bool> Boost()=>Task.FromResult(Runtime.Receipt(this).JewelBoostUsed);
    protected override void OnUpgrade(){}
}
public abstract class RinStarter(CardType type,TargetType target=TargetType.Self,int energy=1):StarterCard(type,target,energy)
{public override string OwnerCharacterId=>"CHAR_RIN";}
public abstract class ArcherStarter(CardType type,TargetType target=TargetType.Self,int energy=1):StarterCard(type,target,energy)
{public override string OwnerCharacterId=>"CHAR_ARCHER";}
[Pool(typeof(RinArcherPool))]
public sealed class Gandr():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{public override string SourceCardId=>"RIN_S_GANDR";protected override string NameText=>"甘德射击";public override bool HasJewelChoice=>true;}
[Pool(typeof(RinArcherPool))]
public sealed class RinReinforcement():RinStarter(CardType.Skill)
{public override string SourceCardId=>"RIN_S_REINFORCEMENT";protected override string NameText=>"强化";public override bool HasJewelChoice=>true;}
[Pool(typeof(RinArcherPool))]
public sealed class JewelPreparation():RinStarter(CardType.Skill)
{public override string SourceCardId=>"RIN_S_JEWEL_PREPARATION";protected override string NameText=>"宝石准备";}
[Pool(typeof(RinArcherPool))]
public sealed class ManaSupply():RinStarter(CardType.Skill,energy:0)
{public override string SourceCardId=>"RIN_S_MANA_SUPPLY";protected override string NameText=>"供魔";}
[Pool(typeof(RinArcherPool))]
public sealed class ReinforceProjection():RinStarter(CardType.Skill,energy:0)
{public override string SourceCardId=>"RIN_S_REINFORCE_PROJECTION";protected override string NameText=>"强化投影";public override bool HasJewelChoice=>true;}
[Pool(typeof(RinArcherPool))]
public sealed class JewelRelease():RinStarter(CardType.Attack,TargetType.AnyEnemy)
{public override string SourceCardId=>"RIN_S_JEWEL_RELEASE";protected override string NameText=>"宝石释放";public override bool HasJewelChoice=>true;}
[Pool(typeof(RinArcherPool))]
public sealed class BowShot():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{public override string SourceCardId=>"ARC_S_BOW_SHOT";protected override string NameText=>"弓箭射击";}
[Pool(typeof(RinArcherPool))]
public sealed class CloseCombat():ArcherStarter(CardType.Attack,TargetType.AnyEnemy)
{public override string SourceCardId=>"ARC_S_CLOSE_COMBAT";protected override string NameText=>"近身战斗";}
[Pool(typeof(RinArcherPool))]
public sealed class Deflect():ArcherStarter(CardType.Skill)
{public override string SourceCardId=>"ARC_S_DEFLECT";protected override string NameText=>"格挡";}
[Pool(typeof(RinArcherPool))]
public sealed class Trace():ArcherStarter(CardType.Skill)
{public override string SourceCardId=>"ARC_S_TRACE";protected override string NameText=>"投影";internal string? PreparedArmId;}
[Pool(typeof(RinArcherPool))]
public sealed class Cover():ArcherStarter(CardType.Skill)
{public override string SourceCardId=>"ARC_S_COVER";protected override string NameText=>"掩护";}
public static class StarterDefinitions
{
    public static IEnumerable<CardModel> Rin=>[ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<Gandr>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<RinReinforcement>(),ModelDb.Card<JewelPreparation>(),ModelDb.Card<ManaSupply>(),ModelDb.Card<ReinforceProjection>(),ModelDb.Card<JewelRelease>()];
    public static IEnumerable<CardModel> Archer=>[ModelDb.Card<BowShot>(),ModelDb.Card<BowShot>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<CloseCombat>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Deflect>(),ModelDb.Card<Trace>(),ModelDb.Card<Trace>(),ModelDb.Card<Cover>()];
}
