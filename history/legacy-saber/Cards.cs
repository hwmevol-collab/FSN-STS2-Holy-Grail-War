using MegaCrit.Sts2.Core.CardSelection;
using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.HoverTips;
namespace FateStayNight;

public abstract class FateCard : CustomCardModel
{
    protected FateCard(int cost,CardType type,CardRarity rarity,TargetType target=TargetType.Self,bool library=true) : base(cost,type,rarity,target,library) {}
    protected abstract string NameText { get; }
    protected abstract string RulesText { get; }
    public override List<(string,string)> Localization => [("title",NameText),("description",RulesText),("selectionScreenPrompt",NameText),("contractTitle","Master/Servent"),("contractBody","Master与Servent共同作战，在一方死亡后，另一方也会死亡。Master与Servent分别使用不同的卡组，正常情况下使用同一个{energyPrefix:energyIcons(1)}槽。"),("immortalTitle","不朽"),("immortalBody","此牌不受卡牌侵蚀的影响")];
    protected override IEnumerable<IHoverTip> ExtraHoverTips{
        get{
            if(Rules.Linked(this)){
                var body=new LocString("cards",Id.Entry+".contractBody");body.Add("energyPrefix",MegaCrit.Sts2.Core.Helpers.EnergyIconHelper.GetPrefix(this));
                yield return new HoverTip(new LocString("cards",Id.Entry+".contractTitle"),body);
            }
            if(Rules.Immortal(this))yield return new HoverTip(new LocString("cards",Id.Entry+".immortalTitle"),new LocString("cards",Id.Entry+".immortalBody"));
        }
    }
    public override Texture2D? CustomPortrait => Art.Texture(GetType().Name);
    public override CardPoolModel Pool=>this is LuckyProtection or SwiftStrike or SwordGuard?ModelDb.CardPool<SaberPool>():this is Precaution?ModelDb.CardPool<FateEventPool>():base.Pool;
}
[Pool(typeof(EmiyaPool))]
public sealed class PosterStrike : FateCard
{
    protected override HashSet<CardTag> CanonicalTags=>[CardTag.Strike];
    public PosterStrike():base(1,CardType.Attack,CardRarity.Basic,TargetType.AnyEnemy){}
    protected override string NameText=>"海报打击";
    protected override string RulesText=>"造成{Damage:diff()}点伤害。\n此牌可多次升级。";
    public override int MaxUpgradeLevel=>int.MaxValue;
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DamageVar(4,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await CreatureCmd.Damage(ctx,play.Target!,DynamicVars.Damage,this);
    protected override void OnUpgrade()=>DynamicVars.Damage.UpgradeValueBy(2);
}
[Pool(typeof(EmiyaPool))]
public sealed class QuickDodge : FateCard
{
    protected override HashSet<CardTag> CanonicalTags=>[CardTag.Defend];
    public QuickDodge():base(1,CardType.Skill,CardRarity.Basic){}
    protected override string NameText=>"快速闪避";
    protected override string RulesText=>"获得{Block:diff()}点格挡。\n此牌可多次升级。";
    public override int MaxUpgradeLevel=>int.MaxValue;
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new BlockVar(5,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await CreatureCmd.GainBlock(Owner.Creature,DynamicVars.Block,play);
    protected override void OnUpgrade()=>DynamicVars.Block.UpgradeValueBy(2);
}
[Pool(typeof(EmiyaPool))]
public sealed class Reinforcement : FateCard
{
    public Reinforcement():base(0,CardType.Skill,CardRarity.Common){}
    protected override string NameText=>"强化魔术";
    protected override string RulesText=>"受到2点伤害。在本回合中，你使用的下{Cards:diff()}张牌将被升级。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new CardsVar(1)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){

        await CreatureCmd.Damage(ctx,Owner.Creature,2,ValueProp.Unpowered,this);
        if(Owner.Creature.IsAlive) await PowerCmd.Apply<ReinforcePower>(ctx,Owner.Creature,DynamicVars.Cards.IntValue,Owner.Creature,this);
    }
    protected override void OnUpgrade()=>DynamicVars.Cards.UpgradeValueBy(1);
}
[Pool(typeof(EmiyaPool))]
public sealed class StructuralAnalysis : FateCard
{
    public StructuralAnalysis():base(0,CardType.Power,CardRarity.Uncommon){}
    protected override string NameText=>"解明构造";
    protected override string RulesText=>"每回合{CountText}次。当你升级卡牌时，若此牌可以多次升级，则再升级1次。";
    protected override void AddExtraArgsToDescription(LocString description){base.AddExtraArgsToDescription(description);description.Add("CountText",IsUpgraded?"两":"一");}
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DynamicVar("Count",1)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await PowerCmd.Apply<AnalysisPower>(ctx,Owner.Creature,DynamicVars["Count"].IntValue,Owner.Creature,this);
    protected override void OnUpgrade()=>DynamicVars["Count"].UpgradeValueBy(1);
}
[Pool(typeof(EmiyaPool))]
public sealed class Coordination : FateCard
{
    public Coordination():base(0,CardType.Skill,CardRarity.Common){}
    protected override string NameText=>"默契配合";
    protected override string RulesText=>"固有。保留。Servent/Master，来我身边！{Immortal}";
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Innate,CardKeyword.Retain];
    protected override void AddExtraArgsToDescription(LocString description){base.AddExtraArgsToDescription(description);description.Add("Immortal",IsUpgraded?"不朽。":"");}
    protected override bool IsPlayable=>Duo.For(Owner)?.ContractActive??true;
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play){Duo.For(Owner)?.RequestSwitch(this);return Task.CompletedTask;}
}
[Pool(typeof(EmiyaPool))]
public sealed class DesperateFlight : FateCard
{
    public DesperateFlight():base(1,CardType.Skill,CardRarity.Common){}
    protected override string NameText=>"亡命奔逃";
    protected override string RulesText=>"失去3点生命，获得{Block:diff()}点格挡。虚无。";
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Ethereal];
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new BlockVar(17,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){await CreatureCmd.Damage(ctx,Owner.Creature,3,ValueProp.Unblockable|ValueProp.Unpowered,this);await CreatureCmd.GainBlock(Owner.Creature,DynamicVars.Block,play);}
    protected override void OnUpgrade()=>DynamicVars.Block.UpgradeValueBy(5);
}
[Pool(typeof(ColorlessCardPool))]
public sealed class CounterfeitLife : FateCard
{
    public CounterfeitLife():base(2,CardType.Power,CardRarity.Uncommon){}
    protected override string NameText=>"以假乱真";
    protected override string RulesText=>"在下一次受到致死伤害时，防止之。直到你的回合开始前免疫所有伤害，然后敌人获得等量的活力。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await PowerCmd.Apply<SurvivalPower>(ctx,Owner.Creature,1,Owner.Creature,this);
    protected override void OnUpgrade()=>EnergyCost.UpgradeBy(-1);
}
[Pool(typeof(FateEventPool))]
public sealed class Precaution : FateCard
{
    public Precaution():base(0,CardType.Skill,CardRarity.Token,TargetType.Self,false){}
    protected override string NameText=>"预防措施";
    protected override string RulesText=>"获得一层缓冲。若在你的回合开始时此效果还存在，清除之并在本场战斗中将此牌移出牌组。";
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){var p=await PowerCmd.Apply<PrecautionBuffer>(ctx,Owner.Creature,1,Owner.Creature,this);if(p!=null)p.Card=this;}
    protected override void OnUpgrade()=>AddKeyword(CardKeyword.Retain);
}
[Pool(typeof(EmiyaPool))]
public sealed class PaperShield : FateCard
{
    public PaperShield():base(0,CardType.Skill,CardRarity.Common){}
    protected override string NameText=>"化纸为盾";
    protected override string RulesText=>"消耗一张攻击牌，获得卡面数值x{Multiplier:diff()}的格挡。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DynamicVar("Multiplier",4)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){
        var cards=await CardSelectCmd.FromHand(ctx,Owner,new CardSelectorPrefs(CardSelectorPrefs.ExhaustSelectionPrompt,1),c=>c.Type==CardType.Attack,this);
        var card=cards.FirstOrDefault();if(card==null)return;
        int amount=Rules.SumArabicNumbers(card.GetDescriptionForPile(PileType.Hand))*DynamicVars["Multiplier"].IntValue;
        await CardCmd.Exhaust(ctx,card);await CreatureCmd.GainBlock(Owner.Creature,amount,ValueProp.Unpowered,play);
    }
    protected override void OnUpgrade()=>DynamicVars["Multiplier"].UpgradeValueBy(1);
}
[Pool(typeof(EmiyaPool))]
public sealed class FateNight : FateCard
{
    public FateNight():base(3,CardType.Skill,CardRarity.Rare){}
    protected override string NameText=>"命运之夜";
    protected override string RulesText=>"与 Servent/Master 互换生命值（多余的生命值转换为临时生命），从Servent/Master 的卡组中选择一张牌加入手牌，在本回合中免费打出。消耗。";
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Exhaust];
    protected override bool IsPlayable=>Duo.For(Owner)?.ContractActive??true;
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){
        if(Duo.For(Owner) is not {} duo || !duo.ContractActive)return;
        await duo.ExchangeHp(ctx,this);
        var choices=duo.Other.OpeningDeck.Select(c=>CardModel.FromSerializable(c)).ToList();
        foreach(var c in choices)duo.Combat!.AddCard(c,Owner);
        if(choices.Count==0)return;
        var chosen=(await CardSelectCmd.FromSimpleGrid(ctx,choices,Owner,new CardSelectorPrefs(new LocString("cards",Id.Entry+".selectionScreenPrompt"),1))).FirstOrDefault();
        if(chosen!=null){chosen.SetToFreeThisTurn();await CardPileCmd.AddGeneratedCardToCombat(chosen,PileType.Hand,Owner);}
    }
    protected override void OnUpgrade()=>EnergyCost.UpgradeBy(-1);
}
[Pool(typeof(SaberPool))]
public sealed class LuckyProtection : FateCard
{
    public LuckyProtection():base(0,CardType.Skill,CardRarity.Rare){}
    protected override string NameText=>"幸运加护";
    protected override string RulesText=>"若对手的意图不是具体攻击，则你在下回合将要受到致死伤害时防止之，并将生命值恢复至最大生命的{HealPercent:diff()}%，否则获得{Block:diff()}点格挡。获得99层临时人工制品。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DynamicVar("HealPercent",10),new BlockVar(10,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){
        if(Owner.Creature.CombatState!.HittableEnemies.All(e=>!Rules.IsAttacking(e))){var p=await PowerCmd.Apply<SurvivalPower>(ctx,Owner.Creature,1,Owner.Creature,this);p?.SetLastLucky(DynamicVars["HealPercent"].IntValue);}
        else await CreatureCmd.GainBlock(Owner.Creature,DynamicVars.Block,play);
        await PowerCmd.Apply<TemporaryArtifact>(ctx,Owner.Creature,99,Owner.Creature,this);
    }
    protected override void OnUpgrade(){DynamicVars["HealPercent"].UpgradeValueBy(5);DynamicVars.Block.UpgradeValueBy(5);}
}
[Pool(typeof(ColorlessCardPool))]
public sealed class GemWind : FateCard
{
    public GemWind():base(0,CardType.Skill,CardRarity.Uncommon,TargetType.AllEnemies){}
    protected override string NameText=>"宝石魔术·风";
    protected override string RulesText=>"给予所有敌人一层虚弱，意图为具体攻击且数值低于{Threshold:diff()}的敌人将被击晕。消耗。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DynamicVar("Threshold",15)];
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Exhaust];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){
        var enemies=Owner.Creature.CombatState!.HittableEnemies.ToList();await PowerCmd.Apply<WeakPower>(ctx,enemies,1,Owner.Creature,this);
        foreach(var e in enemies)if(Rules.IsAttacking(e)&&Rules.IntentDamage(e)<DynamicVars["Threshold"].IntValue)await CreatureCmd.Stun(e);
    }
    protected override void OnUpgrade()=>DynamicVars["Threshold"].UpgradeValueBy(10);
}
[Pool(typeof(SaberPool))]
public sealed class SwiftStrike : FateCard
{
    protected override HashSet<CardTag> CanonicalTags=>[CardTag.Strike];
    public SwiftStrike():base(1,CardType.Attack,CardRarity.Basic,TargetType.AnyEnemy){}
    protected override string NameText=>"疾风打击";
    protected override string RulesText=>"造成{Damage:diff()}点伤害。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DamageVar(8,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){await CreatureCmd.Damage(ctx,play.Target!,DynamicVars.Damage,this);}
    protected override void OnUpgrade()=>DynamicVars.Damage.UpgradeValueBy(4);
}
[Pool(typeof(SaberPool))]
public sealed class SwordGuard : FateCard
{
    protected override HashSet<CardTag> CanonicalTags=>[CardTag.Defend];
    public SwordGuard():base(1,CardType.Skill,CardRarity.Basic){}
    protected override string NameText=>"举剑横挡";
    protected override string RulesText=>"获得{Block:diff()}点格挡。";
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new BlockVar(9,ValueProp.Move)];
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>await CreatureCmd.GainBlock(Owner.Creature,DynamicVars.Block,play);
    protected override void OnUpgrade()=>DynamicVars.Block.UpgradeValueBy(4);
}

