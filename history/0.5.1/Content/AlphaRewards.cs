namespace RinArcherCore;
public sealed record AlphaDefinition(string Id,string Owner,CardRarity Rarity,CardType Type,int Energy,int Mana,string Name,string Rules,string Upgrade);
public static class AlphaRewardRegistry
{
    public const string RinPoolId="RIN_ALPHA_REWARD_POOL",ArcherPoolId="ARCHER_ALPHA_REWARD_POOL";
    public static readonly IReadOnlyList<AlphaDefinition> Definitions=Array.AsReadOnly(new[]{
        D("RIN-C04",CardRarity.Common,CardType.Attack,1,0,"强化格斗","对 FRONT 造成 7 伤害。若敌方攻击意图最终目标包含凛，凛获得 4 格挡。","伤害 9；格挡 6"),
        D("RIN-C05",CardRarity.Common,CardType.Skill,1,0,"储魔宝石","宝石未满：获得 1 宝石；已满：凛获得 8 格挡。","满宝石格挡 11"),
        D("RIN-C08",CardRarity.Common,CardType.Skill,1,0,"强化支援","弓兵获得 7 格挡，包含后备弓兵。","格挡 10"),
        D("RIN-C10",CardRarity.Common,CardType.Skill,1,1,"Gandr 连射","对敌方 FRONT 施加 2 虚弱。","虚弱 3"),
        D("RIN-C12",CardRarity.Common,CardType.Skill,1,0,"魔力转换","选择：凛获得 8 格挡；或获得 2 契约魔力。可取消。","格挡 11；魔力 3"),
        D("RIN-C13",CardRarity.Common,CardType.Skill,0,0,"宝石供魔","消耗 1 宝石，获得 3 契约魔力。需要宝石。直接消费。","魔力 4"),
        D("RIN-U01",CardRarity.Uncommon,CardType.Attack,1,0,"宝石爆发","对 FRONT 造成 8 伤害。可选 Jewel Boost：改为 18。若目标在攻击结算时有虚弱，施加 1 易伤。","伤害 10 / Boost 22"),
        D("RIN-U04",CardRarity.Uncommon,CardType.Attack,2,1,"强化连击","对 FRONT 造成 4 伤害 3 次。若攻击意图最终目标包含凛，凛获得 6 格挡。","伤害 5×3；格挡 8"),
        D("RIN-U06",CardRarity.Uncommon,CardType.Skill,1,1,"术式解析","有敌方 FIELD：选择并压制到下次共享玩家回合开始。无 FIELD：对 FRONT 施加 1 虚弱，凛获得 4 格挡。","有 FIELD 额外凛 4 格挡；无 FIELD 虚弱 2"),
        D("RIN-U10",CardRarity.Uncommon,CardType.Skill,1,0,"投影强化术式","消耗 1 宝石。本共享玩家回合所有成功生成的投影兵装均强化。本回合不可重复施加。","能量 0"),
        D("RIN-U12",CardRarity.Uncommon,CardType.Power,1,0,"强化供魔","凛前场开始共享玩家回合时，在基础供魔之后额外获得 1 契约魔力。","能量 0"),
        D("RIN-U14",CardRarity.Uncommon,CardType.Skill,1,0,"宝石转换","消耗 1 宝石。选择：FRONT 12 伤害；凛 12 格挡；3 契约魔力。可取消。","伤害 15；格挡 15；魔力 4"),
        D("RIN-R04",CardRarity.Rare,CardType.Power,2,0,"宝石魔术精炼","每共享玩家回合第一次 Jewel Boost 不消耗宝石。仍须至少 1 宝石。直接消费不受影响。","能量 1"),
        D("RIN-R05",CardRarity.Rare,CardType.Power,2,0,"持续供魔","共享玩家回合结束时，若凛前场，获得 1 契约魔力。","能量 1"),
        D("ARC-C03",CardRarity.Common,CardType.Attack,1,0,"武装续击","对 FRONT 造成 7 伤害。弓兵手牌有投影兵装时改为 10。","伤害 9 / 13"),
        D("ARC-C06",CardRarity.Common,CardType.Skill,1,0,"即时投影","选择生成干将·莫邪或 Rho Aias。本共享回合该实例魔力为 0。可取消。","成功生成后抽 1 弓兵牌"),
        D("ARC-C07",CardRarity.Common,CardType.Skill,1,0,"投影调整","选择弓兵手牌投影兵装。本共享回合该实例魔力 -1，最低 0。抽 1。","折扣持续本场战斗"),
        D("ARC-C10",CardRarity.Common,CardType.Skill,1,0,"独立防御","魔力至少 2：弓兵获得 6 格挡；魔力至多 1：获得 9。","格挡 8 / 12"),
        D("ARC-C11",CardRarity.Common,CardType.Skill,0,0,"舍弃投影","选择并消耗弓兵手牌 1 投影兵装。弓兵获得 5 格挡，抽 1。不记录 ARM_RESOLVED。","格挡 8"),
        D("ARC-C14",CardRarity.Common,CardType.Skill,1,0,"护卫御主","弓兵获得 5 格挡。获得 Guard Master 1。","格挡 8"),
        D("ARC-U01",CardRarity.Uncommon,CardType.Attack,1,0,"武装轮替","对 FRONT 造成 7 + 3×本战斗成功使用的不同兵装数的伤害，最多计算 3 种。","基础伤害 9"),
        D("ARC-U02",CardRarity.Uncommon,CardType.Attack,1,2,"Broken Phantasm","选择并消耗手牌投影武器（干将·莫邪 / Hrunting）。对 FRONT 造成 18；强化实例改为 23。成功记录 ARM_RESOLVED。","伤害 21 / 26"),
        D("ARC-U05",CardRarity.Uncommon,CardType.Attack,1,0,"精准狙击","选择 FRONT 或有至少 1 Debuff 的敌方契约成员，造成 8 伤害。可取消。","伤害 11"),
        D("ARC-U12",CardRarity.Uncommon,CardType.Power,1,0,"一次性兵装","每共享玩家回合首次投影兵装被消耗时，抽 1 弓兵牌，弓兵获得 3 格挡。","触发格挡 5"),
        D("ARC-U13",CardRarity.Uncommon,CardType.Power,1,0,"单独行动","独立行动实际使魔力消耗 1→0 时，弓兵获得 4 格挡。","触发格挡 6"),
        D("ARC-U14",CardRarity.Uncommon,CardType.Skill,1,0,"武装再现","选择生成尚未 ARM_RESOLVED 的兵装。本共享回合该实例能量为 0。消耗。","该实例本共享回合魔力额外 -1"),
        D("ARC-R03",CardRarity.Rare,CardType.Skill,2,3,"高阶幻想崩坏","消耗手牌指定武器。干将·莫邪：FRONT 6×4；Hrunting：选择任意敌方契约成员，20 伤害及 2 易伤。不读取强化加成。","干将·莫邪 7×4；Hrunting 24"),
        D("ARC-R05",CardRarity.Rare,CardType.Power,2,0,"无供魔作战","打出前魔力为 0：每共享回合第一张弓兵攻击总伤害 +8，分配到原 Hit；第一张实际给弓兵自身格挡的牌 +6 格挡。两次机会独立。","能量 1")
    });
    static AlphaDefinition D(string id,CardRarity rarity,CardType type,int energy,int mana,string name,string rules,string upgrade)=>new(id,id.StartsWith("RIN")?"CHAR_RIN":"CHAR_ARCHER",rarity,type,energy,mana,name,rules,upgrade);
    public static AlphaDefinition Get(string id)=>Definitions.Single(d=>d.Id==id);
    public static IReadOnlyList<AlphaDefinition> Pool(string owner)=>Definitions.Where(d=>d.Owner==owner).ToArray();
    public static CardModel Card(string id)=>id switch{
        "RIN-C04"=>ModelDb.Card<RinC04>(),"RIN-C05"=>ModelDb.Card<RinC05>(),"RIN-C08"=>ModelDb.Card<RinC08>(),"RIN-C10"=>ModelDb.Card<RinC10>(),"RIN-C12"=>ModelDb.Card<RinC12>(),"RIN-C13"=>ModelDb.Card<RinC13>(),
        "RIN-U01"=>ModelDb.Card<RinU01>(),"RIN-U04"=>ModelDb.Card<RinU04>(),"RIN-U06"=>ModelDb.Card<RinU06>(),"RIN-U10"=>ModelDb.Card<RinU10>(),"RIN-U12"=>ModelDb.Card<RinU12>(),"RIN-U14"=>ModelDb.Card<RinU14>(),"RIN-R04"=>ModelDb.Card<RinR04>(),"RIN-R05"=>ModelDb.Card<RinR05>(),
        "ARC-C03"=>ModelDb.Card<ArcC03>(),"ARC-C06"=>ModelDb.Card<ArcC06>(),"ARC-C07"=>ModelDb.Card<ArcC07>(),"ARC-C10"=>ModelDb.Card<ArcC10>(),"ARC-C11"=>ModelDb.Card<ArcC11>(),"ARC-C14"=>ModelDb.Card<ArcC14>(),
        "ARC-U01"=>ModelDb.Card<ArcU01>(),"ARC-U02"=>ModelDb.Card<ArcU02>(),"ARC-U05"=>ModelDb.Card<ArcU05>(),"ARC-U12"=>ModelDb.Card<ArcU12>(),"ARC-U13"=>ModelDb.Card<ArcU13>(),"ARC-U14"=>ModelDb.Card<ArcU14>(),"ARC-R03"=>ModelDb.Card<ArcR03>(),"ARC-R05"=>ModelDb.Card<ArcR05>(),_=>throw new ArgumentException("Unknown Alpha Reward ID")};
}
// Explicit QA registry only: no auto-add or Pool attribute can leak these rewards into a run.
public abstract class AlphaRewardCard:StarterCard
{
    protected AlphaRewardCard(string id):this(AlphaRewardRegistry.Get(id)){}
    AlphaRewardCard(AlphaDefinition d):base(d.Type,TargetType.Self,d.Energy,false,d.Rarity){Definition=d;}
    public AlphaDefinition Definition{get;}
    public override string SourceCardId=>Definition.Id;
    public override string OwnerCharacterId=>Definition.Owner;
    public override int PrintedManaCost=>Definition.Mana;
    protected override string NameText=>$"{Definition.Name} [{Definition.Id}]";
    protected override string RulesText=>RewardRules.Text(this)+$"\n{Definition.Owner} · {Definition.Rarity} · 魔力 {PrintedManaCost}";
    public override CardPoolModel Pool=>OwnerCharacterId=="CHAR_RIN"?ModelDb.CardPool<RinAlphaRewardPool>():ModelDb.CardPool<ArcherAlphaRewardPool>();
    public override bool HasJewelChoice=>SourceCardId=="RIN-U01";
    public override IEnumerable<CardKeyword> CanonicalKeywords=>SourceCardId=="ARC-U14"?[CardKeyword.Exhaust]:[];
    protected override bool IsPlayable=>base.IsPlayable&&RewardRules.CanPlay(Runtime,this);
    internal string? PreparedSelection;
    internal ProjectedArm? PreparedArm;
    internal Creature? PreparedTarget;
    internal FieldStatus? PreparedField;
    public async Task<bool> PrepareChoice()=>await RewardChoice.Prepare(this);
    public void ClearChoice(){PreparedSelection=null;PreparedArm=null;PreparedTarget=null;PreparedField=null;}
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>RewardRules.Play(ctx,play,Runtime,this);
    protected override void OnUpgrade(){if(SourceCardId is "RIN-U10" or "RIN-U12" or "RIN-R04" or "RIN-R05" or "ARC-R05")EnergyCost.UpgradeBy(-1);}
}
public sealed class RinAlphaRewardPool:CustomCardPoolModel
{public override string Title=>AlphaRewardRegistry.RinPoolId;public override string EnergyColorName=>"ironclad";public override Color DeckEntryCardColor=>new("92374d");public override bool IsColorless=>false;}
public sealed class ArcherAlphaRewardPool:CustomCardPoolModel
{public override string Title=>AlphaRewardRegistry.ArcherPoolId;public override string EnergyColorName=>"ironclad";public override Color DeckEntryCardColor=>new("527087");public override bool IsColorless=>false;}
public sealed class RinC04():AlphaRewardCard("RIN-C04");
public sealed class RinC05():AlphaRewardCard("RIN-C05");
public sealed class RinC08():AlphaRewardCard("RIN-C08");
public sealed class RinC10():AlphaRewardCard("RIN-C10");
public sealed class RinC12():AlphaRewardCard("RIN-C12");
public sealed class RinC13():AlphaRewardCard("RIN-C13");
public sealed class RinU01():AlphaRewardCard("RIN-U01");
public sealed class RinU04():AlphaRewardCard("RIN-U04");
public sealed class RinU06():AlphaRewardCard("RIN-U06");
public sealed class RinU10():AlphaRewardCard("RIN-U10");
public sealed class RinU12():AlphaRewardCard("RIN-U12");
public sealed class RinU14():AlphaRewardCard("RIN-U14");
public sealed class RinR04():AlphaRewardCard("RIN-R04");
public sealed class RinR05():AlphaRewardCard("RIN-R05");
public sealed class ArcC03():AlphaRewardCard("ARC-C03");
public sealed class ArcC06():AlphaRewardCard("ARC-C06");
public sealed class ArcC07():AlphaRewardCard("ARC-C07");
public sealed class ArcC10():AlphaRewardCard("ARC-C10");
public sealed class ArcC11():AlphaRewardCard("ARC-C11");
public sealed class ArcC14():AlphaRewardCard("ARC-C14");
public sealed class ArcU01():AlphaRewardCard("ARC-U01");
public sealed class ArcU02():AlphaRewardCard("ARC-U02");
public sealed class ArcU05():AlphaRewardCard("ARC-U05");
public sealed class ArcU12():AlphaRewardCard("ARC-U12");
public sealed class ArcU13():AlphaRewardCard("ARC-U13");
public sealed class ArcU14():AlphaRewardCard("ARC-U14");
public sealed class ArcR03():AlphaRewardCard("ARC-R03");
public sealed class ArcR05():AlphaRewardCard("ARC-R05");
