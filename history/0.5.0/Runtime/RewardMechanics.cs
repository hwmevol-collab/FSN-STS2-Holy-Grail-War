using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Entities.Powers;
namespace RinArcherCore;
public sealed class AlphaPlayReceipt
{
    public int ManaBefore,EnergyPaid,ManaPaid,JewelSpent;
    public bool ZeroManaEligible,AttackBonus,JewelBoostUsed,JewelBoostFree;
    public string? Target;
}
public sealed partial class ContractRuntime
{
    public readonly HashSet<string> ProjectedArmsResolvedThisCombat=new(StringComparer.Ordinal);
    public readonly Dictionary<string,int> AlphaPowers=[];
    public readonly Dictionary<string,int> AlphaMetrics=[];
    readonly Dictionary<StarterCard,AlphaPlayReceipt> alphaReceipts=new(ReferenceEqualityComparer.Instance);
    public bool ReinforceAllThisTurn{get;private set;}
    public bool FreeJewelBoostUsed{get;private set;}
    public bool ProjectedExhaustUsed{get;private set;}
    public bool ZeroManaAttackBonusAvailable{get;private set;}=true;
    public bool ZeroManaBlockBonusAvailable{get;private set;}=true;
    int alphaEndedTurn=-1;
    bool alphaSummaryEmitted;
    public static readonly string[] MetricNames=["rinRewardCardsPlayed","archerRewardCardsPlayed","jewelBoostCount","freeJewelBoostCount","directJewelConsumeCount","armsResolvedDistinct","armsResolvedByNormalPlay","armsResolvedByBroken","projectedExhaustTriggerCount","zeroManaTurns","zeroManaAttackBonusTriggers","zeroManaBlockBonusTriggers","rinActiveEndTurnManaTriggers","guardMasterTriggers","reserveTargetsHit"];
    public void EmitAlphaSummary(){if(alphaSummaryEmitted||alphaReceipts.Count>0)return;alphaSummaryEmitted=true;Log("COMBAT_SUMMARY",MetricNames.ToDictionary(id=>id,id=>AlphaMetrics.GetValueOrDefault(id)));}
    public void Metric(string id,int n=1)=>AlphaMetrics[id]=AlphaMetrics.GetValueOrDefault(id)+n;
    public void BeginAlphaTurn(){ReinforceAllThisTurn=false;FreeJewelBoostUsed=false;ProjectedExhaustUsed=false;ZeroManaAttackBonusAvailable=ZeroManaBlockBonusAvailable=true;if(Mana==0)Metric("zeroManaTurns");}
    public void EndAlphaTurn()
    {
        if(alphaEndedTurn==Turn)return;alphaEndedTurn=Turn;
        if(Active==Rin&&AlphaPowers.ContainsKey("RIN-R05")){int before=Mana;GainMana(1);Metric("rinActiveEndTurnManaTriggers");Log("RIN_END_TURN_MANA",new{manaBefore=before,manaAfter=Mana});}
        ReinforceAllThisTurn=false;
        foreach(var arm in PileTypes.SelectMany(t=>Archer.Pile(t).Cards).OfType<ProjectedArm>())arm.ExpireTemporary(Turn+1);
        Log("ALPHA_PLAYER_TURN_END");
    }
    public void ActivatePower(AlphaRewardCard c){AlphaPowers[c.SourceCardId]=c.IsUpgraded?2:1;Log("ALPHA_POWER_ACTIVE",new{cardId=c.SourceCardId,upgrade=c.IsUpgraded,policy="POWER_DUPLICATE_STACK_POLICY_DEFERRED"});}
    public bool DirectJewelConsume(StarterCard card)
    {
        if(!SpendJewel(true))return false;Metric("directJewelConsumeCount");if(alphaReceipts.TryGetValue(card,out var r))r.JewelSpent++;
        Log("DIRECT_JEWEL_CONSUME",new{cardId=card.SourceCardId});return true;
    }
    public bool UseJewelBoost(StarterCard card,bool confirmed)
    {
        if(!confirmed||Jewel<1)return false;
        bool free=AlphaPowers.ContainsKey("RIN-R04")&&!FreeJewelBoostUsed;int before=Jewel;
        if(free){FreeJewelBoostUsed=true;Metric("freeJewelBoostCount");Log("FREE_JEWEL_BOOST_TRIGGERED",new{cardId=card.SourceCardId,jewelBefore=before,jewelAfter=Jewel});}
        else if(!SpendJewel(true))return false;
        Metric("jewelBoostCount");if(alphaReceipts.TryGetValue(card,out var r)){r.JewelBoostUsed=true;r.JewelBoostFree=free;r.JewelSpent+=free?0:1;}
        Log("JEWEL_BOOST",new{cardId=card.SourceCardId,free});return true;
    }
    public bool ActivateAllProjection(StarterCard card)
    {
        if(ReinforceAllThisTurn||!DirectJewelConsume(card))return false;
        ReinforceAllThisTurn=true;Log("REINFORCE_ALL_ACTIVE",new{turn=Turn});return true;
    }
    public void RecordPayment(StarterCard card,int manaBefore,int energyPaid,int manaPaid)
    {
        bool eligible=card.OwnerCharacterId=="CHAR_ARCHER"&&manaBefore==0&&AlphaPowers.ContainsKey("ARC-R05");
        var r=new AlphaPlayReceipt{ManaBefore=manaBefore,EnergyPaid=energyPaid,ManaPaid=manaPaid,ZeroManaEligible=eligible,Target="NONE"};alphaReceipts[card]=r;
        if(eligible&&card.Type==CardType.Attack&&ZeroManaAttackBonusAvailable){r.AttackBonus=true;ZeroManaAttackBonusAvailable=false;}
    }
    public int[] DamageProfile(StarterCard c,int damage,int hits)
    {
        bool bonus=alphaReceipts.TryGetValue(c,out var r)&&r.AttackBonus;
        var distribution=Enumerable.Range(0,hits).Select(i=>bonus?8/hits+(i<8%hits?1:0):0).ToArray();
        if(bonus){r!.AttackBonus=false;Metric("zeroManaAttackBonusTriggers");Log("ZERO_MANA_ATTACK_BONUS",new{cardId=c.SourceCardId,hitCount=hits,bonusDistribution=distribution});}
        return distribution.Select(n=>damage+n).ToArray();
    }
    public int BlockAmount(StarterCard c,CharacterRuntime recipient,int amount)
    {
        if(amount>0&&recipient==Archer&&ZeroManaBlockBonusAvailable&&alphaReceipts.TryGetValue(c,out var r)&&r.ZeroManaEligible)
        {ZeroManaBlockBonusAvailable=false;Metric("zeroManaBlockBonusTriggers");Log("ZERO_MANA_BLOCK_BONUS",new{cardId=c.SourceCardId,baseBlock=amount,bonusBlock=6});return amount+6;}return amount;
    }
    public async Task IaEngineBlock()
    {
        if(!AlphaPowers.TryGetValue("ARC-U13",out int level))return;
        int block=level==2?6:4;await CreatureCmd.GainBlock(Archer.Creature,block,ValueProp.Move,null);Log("IA_ENGINE_BLOCK",new{block});
    }
    public async Task ProjectedExhaust(PlayerChoiceContext ctx,ProjectedArm arm,string source)
    {
        if(!AlphaPowers.TryGetValue("ARC-U12",out int level)||ProjectedExhaustUsed)return;
        ProjectedExhaustUsed=true;int block=level==2?5:3;
        await DrawArcher(ctx,1);await CreatureCmd.GainBlock(Archer.Creature,block,ValueProp.Move,null);
        Metric("projectedExhaustTriggerCount");Log("PROJECTED_EXHAUST_ENGINE",new{armId=arm.ArmId,source,draw=1,block});
    }
    public async Task DrawArcher(PlayerChoiceContext ctx,int amount)
    {
        // CardPileCmd.Draw uses the player's native draw/hand. Exhaust can occur in Reserve.
        if(Active==Archer){await CardPileCmd.Draw(ctx,amount,Player);return;}
        for(int i=0;i<amount;i++)
        {
            if(Archer.DrawPile.IsEmpty&& !Archer.Discard.IsEmpty){foreach(var c in Archer.Discard.Cards.ToArray())await CardPileCmd.Add(c,Archer.DrawPile,skipVisuals:true);Archer.DrawPile.RandomizeOrderInternal(Player,Player.RunState.Rng.Shuffle,Combat);}
            var next=Archer.DrawPile.Cards.FirstOrDefault();if(next==null)break;await CardPileCmd.Add(next,Archer.Hand,skipVisuals:true);
        }
    }
    public void ArmResolved(ProjectedArm arm,string source)
    {
        if(!ProjectedArmsResolvedThisCombat.Add(arm.ArmId))return;
        AlphaMetrics["armsResolvedDistinct"]=ProjectedArmsResolvedThisCombat.Count;Metric(source=="NORMAL_PLAY"?"armsResolvedByNormalPlay":"armsResolvedByBroken");
        Log("ARM_RESOLVED_ADDED",new{armId=arm.ArmId,source,turn=Turn,distinctResolvedCount=ProjectedArmsResolvedThisCombat.Count});
    }
    public void CompleteAlphaPlay(StarterCard c)
    {
        if(c is ProjectedArm arm)ArmResolved(arm,"NORMAL_PLAY");
        if(c is AlphaRewardCard)Metric(c.OwnerCharacterId=="CHAR_RIN"?"rinRewardCardsPlayed":"archerRewardCardsPlayed");
        if(alphaReceipts.Remove(c,out var r))Log("ALPHA_CARD_RESOLVED",new{cardId=c.SourceCardId,owner=c.OwnerCharacterId,rarity=c.Rarity.ToString(),upgrade=c.IsUpgraded,energyPaid=r.EnergyPaid,manaPaid=r.ManaPaid,jewelSpent=r.JewelSpent,jewelBoostUsed=r.JewelBoostUsed,jewelBoostFree=r.JewelBoostFree,target=r.Target});
        if(Finished)EmitAlphaSummary();
    }
    public void SetAlphaTarget(StarterCard c,string target){if(alphaReceipts.TryGetValue(c,out var r))r.Target=target;}
    public void GiveGuardMaster(){GuardCharges=1;Log("STATUS_GUARD_MASTER",new{charges=1});}
    public bool SuppressField(FieldStatus field)
    {
        if(!FieldStatuses.Contains(field)||field.Owner!="ENEMY_CONTRACT"||field.Duration==0)return false;
        field.Suppressed=true;field.SuppressUntil=Turn+1;QaTargetTag.RefreshNumbers(this);Log("FIELD_SUPPRESSED",new{field.FieldId,field.Duration,field.SuppressUntil});return true;
    }
}
public static class RewardRules
{
    public static string Text(AlphaRewardCard c)
    {
        if(!c.IsUpgraded)return c.Definition.Rules;
        return c.SourceCardId switch{
            "RIN-C04"=>"对 FRONT 造成 9 伤害。若敌方攻击意图最终目标包含凛，凛获得 6 格挡。",
            "RIN-C05"=>"宝石未满：获得 1 宝石；已满：凛获得 11 格挡。",
            "RIN-C08"=>"弓兵获得 10 格挡，包含后备弓兵。",
            "RIN-C10"=>"对敌方 FRONT 施加 3 虚弱。",
            "RIN-C12"=>"选择：凛获得 11 格挡；或获得 3 契约魔力。可取消。",
            "RIN-C13"=>"消耗 1 宝石，获得 4 契约魔力。需要宝石。直接消费。",
            "RIN-U01"=>"对 FRONT 造成 10 伤害。可选 Jewel Boost：改为 22。若目标在攻击结算时有虚弱，施加 1 易伤。",
            "RIN-U04"=>"对 FRONT 造成 5 伤害 3 次。若攻击意图最终目标包含凛，凛获得 8 格挡。",
            "RIN-U06"=>"有敌方 FIELD：选择并压制到下次共享玩家回合开始，凛获得 4 格挡。无 FIELD：对 FRONT 施加 2 虚弱，凛获得 4 格挡。",
            "RIN-U14"=>"消耗 1 宝石。选择：FRONT 15 伤害；凛 15 格挡；4 契约魔力。可取消。",
            "ARC-C03"=>"对 FRONT 造成 9 伤害。弓兵手牌有投影兵装时改为 13。",
            "ARC-C06"=>"选择生成干将·莫邪或 Rho Aias。本共享回合该实例魔力为 0。成功生成后抽 1 弓兵牌。可取消。",
            "ARC-C07"=>"选择弓兵手牌投影兵装。本场战斗该实例魔力 -1，最低 0。抽 1。",
            "ARC-C10"=>"魔力至少 2：弓兵获得 8 格挡；魔力至多 1：获得 12。",
            "ARC-C11"=>"选择并消耗弓兵手牌 1 投影兵装。弓兵获得 8 格挡，抽 1。不记录 ARM_RESOLVED。",
            "ARC-C14"=>"弓兵获得 8 格挡。获得 Guard Master 1。",
            "ARC-U01"=>"对 FRONT 造成 9 + 3×本战斗成功使用的不同兵装数的伤害，最多计算 3 种。",
            "ARC-U02"=>"选择并消耗手牌投影武器（干将·莫邪 / Hrunting）。对 FRONT 造成 21；强化实例改为 26。成功记录 ARM_RESOLVED。",
            "ARC-U05"=>"选择 FRONT 或有至少 1 Debuff 的敌方契约成员，造成 11 伤害。可取消。",
            "ARC-U12"=>"每共享玩家回合首次投影兵装被消耗时，抽 1 弓兵牌，弓兵获得 5 格挡。",
            "ARC-U13"=>"独立行动实际使魔力消耗 1→0 时，弓兵获得 6 格挡。",
            "ARC-U14"=>"选择生成尚未 ARM_RESOLVED 的兵装。本共享回合该实例能量为 0，魔力额外 -1。消耗。",
            "ARC-R03"=>"消耗手牌指定武器。干将·莫邪：FRONT 7×4；Hrunting：选择任意敌方契约成员，24 伤害及 2 易伤。不读取强化加成。",
            _=>c.Definition.Rules};
    }
    public static FieldStatus[] Fields(ContractRuntime d)=>d.FieldStatuses.Where(f=>f.Owner=="ENEMY_CONTRACT"&&f.Duration!=0).ToArray();
    public static ProjectedArm[] Arms(ContractRuntime d,bool weapon=false)=>d.Archer.Hand.Cards.OfType<ProjectedArm>().Where(a=>!weapon||a.ArmId is "ARM_KANSHOU_BAKUYA" or "ARM_HRUNTING").ToArray();
    public static Creature[] PrecisionTargets(ContractRuntime d)
    {
        if(d.Enemy==null)return d.Combat.Enemies.Where(c=>c.IsAlive).ToArray();
        return new[]{d.Enemy.Active,d.Enemy.Master,d.Enemy.Servant}.Distinct().Where(c=>c.IsAlive&&(c==d.Enemy.Active||c.Powers.Any(p=>p.Type==PowerType.Debuff))).ToArray();
    }
    public static bool CanPlay(ContractRuntime d,AlphaRewardCard c)=>c.SourceCardId switch{
        "RIN-C13" or "RIN-U14"=>d.Jewel>=1,"RIN-U10"=>d.Jewel>=1&&!d.ReinforceAllThisTurn,
        "ARC-C07" or "ARC-C11"=>Arms(d).Length>0,"ARC-U02" or "ARC-R03"=>Arms(d,true).Length>0,
        "ARC-U14"=>Arsenal.Ids.Any(id=>!d.ProjectedArmsResolvedThisCombat.Contains(id)),_=>true};
    public static bool NeedsChoice(AlphaRewardCard c)=>c.SourceCardId is "RIN-C12" or "RIN-U06" or "RIN-U14" or "ARC-C06" or "ARC-C07" or "ARC-C11" or "ARC-U02" or "ARC-U05" or "ARC-U14" or "ARC-R03";
    public static async Task Play(PlayerChoiceContext ctx,CardPlay play,ContractRuntime d,AlphaRewardCard c)
    {
        bool up=c.IsUpgraded;int V(int normal,int upgraded)=>up?upgraded:normal;
        Task Block(CharacterRuntime member,int n){d.SetAlphaTarget(c,member.CharacterId);return CreatureCmd.GainBlock(member.Creature,d.BlockAmount(c,member,n),ValueProp.Move,play);}
        async Task Damage(int n,int hits=1,Creature? target=null)
        {var profile=d.DamageProfile(c,n,hits);d.SetAlphaTarget(c,target==null?"FRONT":target.CombatId.ToString()!);for(int i=0;i<hits&&!d.Finished;i++)await Targeting.Damage(ctx,d,target==null?ContractTarget.FRONT:ContractTarget.ANY_CONTRACT_MEMBER,profile[i],d.Member(c.OwnerCharacterId).Creature,c,true,i+1,target);}
        async Task Weak(int n){var t=Targeting.Resolve(d,ContractTarget.FRONT,true).Single();d.SetAlphaTarget(c,"FRONT");await PowerCmd.Apply<WeakPower>(ctx,t,n,d.Rin.Creature,c);}
        var arm=c.PreparedArm;
        if(arm!=null&&c.SourceCardId is "ARC-C11" or "ARC-U02" or "ARC-R03")arm.ExhaustSource=c.SourceCardId;
        switch(c.SourceCardId)
        {
            case "RIN-C04":bool threat=Targeting.IsRinTargetedByAttackIntent(d);await Damage(V(7,9));if(threat)await Block(d.Rin,V(4,6));break;
            case "RIN-C05":if(d.Jewel<d.JewelCap)d.GainJewel(1);else await Block(d.Rin,V(8,11));break;
            case "RIN-C08":await Block(d.Archer,V(7,10));break;
            case "RIN-C10":await Weak(V(2,3));break;
            case "RIN-C12":if(c.PreparedSelection=="DEFENSE")await Block(d.Rin,V(8,11));else if(c.PreparedSelection=="SUPPLY")d.GainMana(V(2,3));else throw new InvalidOperationException("Unprepared choice");break;
            case "RIN-C13":if(!d.DirectJewelConsume(c))throw new InvalidOperationException("Missing Jewel");d.GainMana(V(3,4));break;
            case "RIN-U01":var front=Targeting.Resolve(d,ContractTarget.FRONT,true).Single();bool weak=front.Powers.OfType<WeakPower>().Any();bool boost=d.UseJewelBoost(c,d.Jewel>0&&await JewelChoice.Ask(c));await Damage(boost?V(18,22):V(8,10));if(weak&&front.IsAlive)await PowerCmd.Apply<VulnerablePower>(ctx,front,1,d.Rin.Creature,c);break;
            case "RIN-U04":threat=Targeting.IsRinTargetedByAttackIntent(d);await Damage(V(4,5),3);if(threat)await Block(d.Rin,V(6,8));break;
            case "RIN-U06":if(Fields(d).Length>0){if(c.PreparedField==null||!d.SuppressField(c.PreparedField))throw new InvalidOperationException("Unprepared FIELD");if(up)await Block(d.Rin,4);}else{await Weak(V(1,2));await Block(d.Rin,4);}break;
            case "RIN-U10":if(!d.ActivateAllProjection(c))throw new InvalidOperationException("U10 unavailable");break;
            case "RIN-U14":if(!d.DirectJewelConsume(c))throw new InvalidOperationException("Missing Jewel");switch(c.PreparedSelection){case "ATTACK":await Damage(V(12,15));break;case "DEFENSE":await Block(d.Rin,V(12,15));break;case "SUPPLY":d.GainMana(V(3,4));break;default:throw new InvalidOperationException("Unprepared choice");}break;
            case "ARC-C03":await Damage(Arms(d).Length>0?V(10,13):V(7,9));break;
            case "ARC-C06":var instant=await d.GenerateArm(ctx,c.PreparedSelection??throw new InvalidOperationException("Unprepared arm"),c.SourceCardId,zeroManaThisTurn:true);if(up)await d.DrawArcher(ctx,1);break;
            case "ARC-C07":if(arm==null)throw new InvalidOperationException("Unprepared arm");int discount=Math.Min(1,arm.ModifiedManaCost);if(up)arm.ManaDiscount+=discount;else{arm.TemporaryManaDiscount+=discount;arm.TemporaryDiscountTurn=d.Turn;}await d.DrawArcher(ctx,1);d.Log("ARM_MODIFIED",arm.Metadata());break;
            case "ARC-C10":await Block(d.Archer,d.Mana>=2?V(6,8):V(9,12));break;
            case "ARC-C11":if(arm==null)throw new InvalidOperationException("Unprepared arm");await CardPileCmd.Add(arm,d.Archer.Exhaust,skipVisuals:false);await Block(d.Archer,V(5,8));await d.DrawArcher(ctx,1);break;
            case "ARC-C14":await Block(d.Archer,V(5,8));d.GiveGuardMaster();break;
            case "ARC-U01":await Damage(V(7,9)+3*Math.Min(3,d.ProjectedArmsResolvedThisCombat.Count));break;
            case "ARC-U02":if(arm==null)throw new InvalidOperationException("Unprepared weapon");await CardPileCmd.Add(arm,d.Archer.Exhaust,skipVisuals:false);await Damage(arm.Reinforced?V(23,26):V(18,21));d.ArmResolved(arm,c.SourceCardId);d.Log("CONSUMED_AS_BROKEN",arm.Metadata());break;
            case "ARC-U05":await Damage(V(8,11),target:c.PreparedTarget??throw new InvalidOperationException("Unprepared target"));break;
            case "ARC-U14":var repeat=await d.GenerateArm(ctx,c.PreparedSelection??throw new InvalidOperationException("Unprepared arm"),c.SourceCardId,up,energyOverrideThisTurn:0);break;
            case "ARC-R03":if(arm==null)throw new InvalidOperationException("Unprepared profile");await CardPileCmd.Add(arm,d.Archer.Exhaust,skipVisuals:false);switch(arm.ArmId){case "ARM_KANSHOU_BAKUYA":await Damage(V(6,7),4);break;case "ARM_HRUNTING":var target=c.PreparedTarget??throw new InvalidOperationException("Unprepared target");await Damage(V(20,24),target:target);if(target.IsAlive)await PowerCmd.Apply<VulnerablePower>(ctx,target,2,d.Archer.Creature,c);break;default:throw new InvalidOperationException("Unknown Broken Profile");}d.ArmResolved(arm,c.SourceCardId);d.Log("CONSUMED_AS_BROKEN",arm.Metadata());break;
            default:if(c.Type!=CardType.Power)throw new InvalidOperationException("Unimplemented reward");d.ActivatePower(c);break;
        }
        c.ClearChoice();
    }
}
