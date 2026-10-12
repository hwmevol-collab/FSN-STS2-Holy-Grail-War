using MegaCrit.Sts2.Core.Models.RelicPools;
namespace FateStayNight;
public abstract class FateRelic : CustomRelicModel
{
    protected abstract string NameText{get;}
    protected abstract string RulesText{get;}
    public override List<(string,string)> Localization=>[("title",NameText),("description",RulesText),("flavor","")];
    public override string PackedIconPath=>"res://images/atlases/relic_atlas.sprites/anchor.tres";
    protected override string PackedIconOutlinePath=>"res://images/atlases/relic_outline_atlas.sprites/anchor.tres";
    public virtual void ResetCombatFlags(){}
}
[Pool(typeof(FateRelicPool))]
public sealed class CommandSeals : FateRelic
{
    protected override string NameText=>"令咒";
    protected override string RulesText=>"一局游戏中只能使用三次，每场战斗只能使用一次。在使用次数归零后将所有卡面信息含有Master/Servent的牌移出牌组。";
    public override RelicRarity Rarity=>RelicRarity.Starter;
    [SavedProperty]public int Charges{get;set;}=3;
    [SavedProperty]public bool Released{get;set;}
    [SavedProperty]public bool EscapeRewardsPending{get;set;}
    [SavedProperty]public string SaberData{get;set;}="";
    public bool UsedThisCombat;
    public override int DisplayAmount=>Charges;
    public override bool ShowCounter=>true;
    protected override IEnumerable<MegaCrit.Sts2.Core.HoverTips.IHoverTip> ExtraHoverTips{
        get{yield return new MegaCrit.Sts2.Core.HoverTips.HoverTip(Title,$"剩余次数：{Charges}/3。"+(Charges<=0?"次数已耗尽。":UsedThisCombat?"本战已使用。":Duo.For(Owner) is {} d&&Art.SealAvailable(d)?"点击遗物图标选择效果。":"当前不可用，等待玩家回合。"));}
    }
    public override bool IsUsedUp=>Charges<=0;
    public override Task BeforeCombatStart(){if(Owner.Creature.CombatState is CombatState combat){Duo.For(Owner)?.Start(combat);Art.AttachUi(Owner);}return Task.CompletedTask;}
    public override Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner)Duo.For(Owner)?.NaturalTurn();return Task.CompletedTask;}
    public override Task AfterDeath(PlayerChoiceContext ctx,Creature creature,bool prevented,float length){if(!prevented&&creature==Owner.Creature&&Duo.For(Owner) is {} duo&&duo.ContractActive){duo.Master.Hp=duo.Saber.Hp=0;duo.Save();}return Task.CompletedTask;}
    public override bool ShouldAfflict(CardModel card,AfflictionModel affliction)=>!Rules.Immortal(card);
}
[Pool(typeof(SharedRelicPool))]
public sealed class OldHeater : FateRelic
{
    protected override string NameText=>"破旧暖炉";
    protected override string RulesText=>"每两个回合，获得4点格挡。\n若你处于“解明构造”状态下，改为每一个回合。";
    public override RelicRarity Rarity=>RelicRarity.Common;
    int turns;
    public override void ResetCombatFlags()=>turns=0;
    public override Task BeforeCombatStart(){ResetCombatFlags();return Task.CompletedTask;}
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner&&(++turns%2==0||Owner.Creature.HasPower<AnalysisPower>())){Flash();await CreatureCmd.GainBlock(Owner.Creature,4,ValueProp.Unpowered,null);}}
}
[Pool(typeof(SharedRelicPool))]
public sealed class EmiyaHouse : FateRelic
{
    protected override string NameText=>"卫宫宅";
    protected override string RulesText=>"你无法看到对手意图\n在首个回合开始时，将两张预防措施加入你的手牌。";
    public override RelicRarity Rarity=>RelicRarity.Uncommon;
    bool given;
    public override void ResetCombatFlags()=>given=false;
    public override Task BeforeCombatStart(){ResetCombatFlags();return Task.CompletedTask;}
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){
        if(player!=Owner||given)return;given=true;Flash();
        for(int i=0;i<2;i++){var c=state.CreateCard<Precaution>(Owner);await CardPileCmd.AddGeneratedCardToCombat(c,PileType.Hand,Owner);}
    }
}
[Pool(typeof(SharedRelicPool))]
public sealed class Avalon : FateRelic
{
    protected override string NameText=>"遥远的理想乡";
    protected override string RulesText=>"在你的回合开始时，恢复10点生命。";
    public override RelicRarity Rarity=>RelicRarity.Rare;
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner){Flash();await CreatureCmd.Heal(Owner.Creature,10);}}
}
[Pool(typeof(FateRelicPool))]
public sealed class KingsArmor : FateRelic
{
    protected override string NameText=>"王之铠甲";
    protected override string RulesText=>"在你的回合开始时，恢复2点生命。";
    public override RelicRarity Rarity=>RelicRarity.Starter;
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner){Flash();await CreatureCmd.Heal(Owner.Creature,2);}}
}
[Pool(typeof(FateRelicPool))]
public sealed class WindBarrier : FateRelic
{
    protected override string NameText=>"风王结界";
    protected override string RulesText=>"在你使用一张攻击牌后，若此牌未能突破对手的格挡，获得1点力量。否则你重置以此法获得的力量。";
    public override RelicRarity Rarity=>RelicRarity.Starter;
    int strength;
    HashSet<CardModel> breached=[];
    protected override void DeepCloneFields(){base.DeepCloneFields();breached=[];strength=0;}
    public override void ResetCombatFlags(){strength=0;breached.Clear();}
    public override Task BeforeCombatStart(){ResetCombatFlags();return Task.CompletedTask;}
    public override Task AfterDamageGiven(PlayerChoiceContext ctx,Creature? dealer,DamageResult result,ValueProp props,Creature target,CardModel? source){if(dealer==Owner.Creature&&source?.Type==CardType.Attack&&target.IsEnemy&&result.UnblockedDamage>0)breached.Add(source);return Task.CompletedTask;}
    public override async Task AfterCardPlayed(PlayerChoiceContext ctx,CardPlay play){
        if(play.Card.Owner!=Owner||play.Card.Type!=CardType.Attack||!play.IsLastInSeries)return;
        if(breached.Remove(play.Card)){if(strength!=0){await PowerCmd.Apply<StrengthPower>(ctx,Owner.Creature,-strength,Owner.Creature,null);strength=0;}}
        else{strength++;await PowerCmd.Apply<StrengthPower>(ctx,Owner.Creature,1,Owner.Creature,null);}
    }
}
