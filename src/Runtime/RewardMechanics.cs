namespace RinArcherCore;
public sealed class GameplayPlayPlan
{
    public string? Selection,Member,ArmId;
    public Creature? Target;
    public ProjectedArm? Arm;
    public FieldStatus? Field;
    public CardModel[] Cards=[],ReserveCards=[];
    public PowerModel[] Debuffs=[];
    public ProjectedArm[] Arms=[];
    public PowerModel? Cleanse;
    public string? ReserveMember;
    public int AdditionalMana,DirectJewels;
    public System.Numerics.BigInteger ArmUsesSnapshot;
    public bool Boost;
}
public sealed class AlphaPlayReceipt
{
    public long RootSequence;
    public int ManaBefore,EnergyPaid,ManaPaid,JewelSpent,RinLayers,ForgeLayers;
    public System.Numerics.BigInteger BoostMultiplier=1;
    public bool BoostSettled,SelfReinforcementUsed;
    public bool ZeroManaEligible,AttackBonus,JewelBoostUsed,JewelBoostFree,IaApplied,EnergyDiscount,IsAutoPlay,MaterialConsumed,Resolved,ForgeEvent,U12Tuning;
    public string? Target;
    public GameplayPlayPlan Plan=new();
    public readonly Dictionary<string,int[]> Profiles=[];
    public readonly HashSet<int> FinishedIndices=[];
}
public sealed partial class ContractRuntime
{
    public readonly HashSet<string> ProjectedArmsResolvedThisCombat=new(StringComparer.Ordinal);
    public readonly Dictionary<string,int> AlphaPowers=[];
    public readonly Dictionary<string,int> AlphaMetrics=[];
    readonly Dictionary<StarterCard,AlphaPlayReceipt> alphaReceipts=new(ReferenceEqualityComparer.Instance);
    public bool ReinforceAllThisTurn{get;private set;} // Legacy API; V1.2 uses encounter charges.
    public int U10Charges{get;private set;}
    public bool U15Pending{get;set;}
    public int RinGrowthLayers{get;private set;}
    public int ForgeLayers{get;private set;}
    public bool SupplyGainUsed{get;set;}
    public bool SupplyExchangeUsed{get;set;}
    public bool C13Used{get;set;}
    public bool C15Used{get;set;}
    public bool U12ManaEventUsed{get;set;}
    public bool RinSuccessful{get;private set;}
    public bool ArcherSuccessful{get;private set;}
    public bool ArmActivityThisTurn{get;set;}
    public bool FreeJewelBoostUsed{get;private set;}
    public bool ProjectedExhaustUsed{get;private set;}
    public bool ZeroManaAttackBonusAvailable{get;private set;}=true;
    public bool ZeroManaBlockBonusAvailable{get;private set;}=true;
    bool firstBoost,firstForge,firstArcherDamage,rinR05Triggered,alphaSummaryEmitted;
    int alphaEndedTurn=-1,energyDueTurn=-1;
    long rootSequence;
    readonly HashSet<string> duplicatePowerDraw=[],c16Issued=[];
    readonly List<string> c16Tickets=[];
    readonly HashSet<CardPlay> successfulEvents=[];
    public static readonly string[] MetricNames=["rinRewardCardsPlayed","archerRewardCardsPlayed","jewelBoostCount","freeJewelBoostCount","directJewelConsumeCount","armsResolvedDistinct","armsResolvedByNormalPlay","armsResolvedByBroken","projectedExhaustTriggerCount","zeroManaTurns","zeroManaAttackBonusTriggers","zeroManaBlockBonusTriggers","rinActiveEndTurnManaTriggers","guardMasterTriggers","reserveTargetsHit"];
    public void EmitAlphaSummary(){if(alphaSummaryEmitted||alphaReceipts.Count>0)return;alphaSummaryEmitted=true;Log("COMBAT_SUMMARY",MetricNames.ToDictionary(id=>id,id=>AlphaMetrics.GetValueOrDefault(id)));}
    public void Metric(string id,int n=1)=>AlphaMetrics[id]=AlphaMetrics.GetValueOrDefault(id)+n;
    public void BeginAlphaTurn()
    {
        SupplyGainUsed=SupplyExchangeUsed=C13Used=C15Used=U12ManaEventUsed=false;
        firstBoost=firstForge=firstArcherDamage=rinR05Triggered=RinSuccessful=ArcherSuccessful=ArmActivityThisTurn=false;
        TuningUsedByMember.Clear();duplicatePowerDraw.Clear();c16Issued.Clear();c16Tickets.Clear();successfulEvents.Clear();settledEvents.Clear();
        FreeJewelBoostUsed=ProjectedExhaustUsed=false;ZeroManaAttackBonusAvailable=ZeroManaBlockBonusAvailable=true;
        if(Mana==0)Metric("zeroManaTurns");
    }
    public void ApplyNextTurnEnergy(){if(energyDueTurn==Turn){energyDueTurn=-1;Player.PlayerCombatState!.Energy++;Log("CONTRACT_RESONANCE_ENERGY",new{amount=1});}}
    public void EndAlphaTurn()
    {
        if(alphaEndedTurn==Turn)return;alphaEndedTurn=Turn;c16Tickets.Clear();
        foreach(var arm in PileTypes.SelectMany(t=>Archer.Pile(t).Cards).OfType<ProjectedArm>())arm.ExpireTemporary(Turn+1);
        Log("ALPHA_PLAYER_TURN_END");
    }
    public AlphaPlayReceipt Receipt(StarterCard c)
    {
        if(alphaReceipts.TryGetValue(c,out var r))return r;
        r=new(){RootSequence=++rootSequence,Plan=c.Plan??new(),RinLayers=RinGrowthLayers,ForgeLayers=ForgeLayers,ManaBefore=Mana,BoostMultiplier=BoostMultiplier};alphaReceipts[c]=r;return r;
    }
    public void RecordPayment(StarterCard c,int manaBefore,int energyPaid,int manaPaid,bool ia=false,bool energyDiscount=false)
    {
        alphaReceipts.Remove(c);var r=Receipt(c);r.ManaBefore=manaBefore;r.EnergyPaid=energyPaid;r.ManaPaid=manaPaid;r.IaApplied=ia;r.EnergyDiscount=energyDiscount;
        r.ZeroManaEligible=c.OwnerCharacterId=="CHAR_ARCHER"&&(manaBefore==0||ia)&&AlphaPowers.ContainsKey("ARC-R05");
        if(manaPaid>=2){r.U12Tuning=!U12ManaEventUsed&&AlphaPowers.ContainsKey("RIN-U12");U12ManaEventUsed=true;}
        if(energyDiscount)U15Pending=false;
    }
    public bool EnergyDiscountActive(StarterCard c)=>U15Pending||alphaReceipts.TryGetValue(c,out var r)&&r.EnergyDiscount;
    public void ActivatePower(AlphaRewardCard c)=>AlphaPowers[c.SourceCardId]=Math.Max(AlphaPowers.GetValueOrDefault(c.SourceCardId),c.IsUpgraded?2:1);
    public async Task ActivatePower(AlphaRewardCard c,CardPlay play,PlayerChoiceContext ctx)
    {
        int level=c.IsUpgraded?2:1;bool duplicate=AlphaPowers.TryGetValue(c.SourceCardId,out int previous);
        AlphaPowers[c.SourceCardId]=Math.Max(level,previous);
        if(duplicate&&play.PlayIndex==0&&!play.IsAutoPlay)await DrawMember(ctx,Member(c.OwnerCharacterId),1);
        Log("ALPHA_POWER_ACTIVE",new{cardId=c.SourceCardId,level=AlphaPowers[c.SourceCardId],duplicate});
    }
    public bool DirectJewelConsume(StarterCard c)
    {
        if(!SpendJewel(true))return false;Metric("directJewelConsumeCount");Receipt(c).JewelSpent++;Log("DIRECT_JEWEL_CONSUME",new{cardId=c.SourceCardId});return true;
    }
    public bool UseJewelBoost(StarterCard c,bool confirmed)
    {
        var r=Receipt(c);if(r.JewelBoostUsed)return true;if(!confirmed||Jewel<1)return false;
        bool free=AlphaPowers.ContainsKey("RIN-R04")&&!FreeJewelBoostUsed;
        if(free){FreeJewelBoostUsed=true;Metric("freeJewelBoostCount");}else if(!SpendJewel(true))return false;
        r.JewelBoostUsed=true;r.JewelBoostFree=free;r.JewelSpent+=free?0:1;Metric("jewelBoostCount");Log("JEWEL_BOOST",new{cardId=c.SourceCardId,free});return true;
    }
    public bool ActivateAllProjection(StarterCard c)
    {if(U10Charges>0)return false;U10Charges=2;Log("U10_CHARGES",new{charges=2});return true;}
    public bool HasArcherSpace(CardModel? leaving=null)=>Archer.Hand.Cards.Count-(leaving!=null&&Archer.Hand.Cards.Contains(leaving)?1:0)<CardPile.MaxCardsInHand;
    public string ConsumeProjectionSource()
    {
        if(PendingReinforcement.Active){PendingReinforcement.Active=false;PendingReinforcement.ManaDiscount=0;return "STARTER_PENDING";}
        if(U10Charges>0){U10Charges--;return "U10_CHARGE";}return "NONE";
    }
    public Creature? PlayTarget(StarterCard c)
    {
        var r=Receipt(c);
        if(r.Plan.Target!=null)return r.Plan.Target;
        if(c.CurrentTarget!=null)return r.Plan.Target=c.CurrentTarget;
        if(Enemy!=null)return r.Plan.Target=Enemy.Active;
        var legal=Combat.Enemies.Where(t=>t.IsAlive).Take(2).ToArray();
        // Multiple ordinary enemies require the existing explicit selection, never an arbitrary fallback.
        return r.Plan.Target=legal.Length==1?legal[0]:null;
    }
    public int[] DamageProfile(StarterCard c,int damage,int hits,string scope="")
    {
        var r=Receipt(c);string key=$"{scope}:{damage}:{hits}";if(r.Profiles.TryGetValue(key,out var profile))return profile;
        int bonus=0;
        if(c.OwnerCharacterId=="CHAR_RIN"&&SelfReinforcement>0&&!r.SelfReinforcementUsed){bonus+=SelfReinforcement;SelfReinforcement=0;r.SelfReinforcementUsed=true;}
        if(r.ZeroManaEligible&&c.Type==CardType.Attack&&ZeroManaAttackBonusAvailable){ZeroManaAttackBonusAvailable=false;bonus+=8;Metric("zeroManaAttackBonusTriggers");}
        if(c.OwnerCharacterId=="CHAR_ARCHER"&&!firstArcherDamage){firstArcherDamage=true;if(AlphaPowers.ContainsKey("ARC-R06"))bonus+=r.ForgeLayers*2;}
        if(r.JewelBoostUsed&&c.Type==CardType.Attack&&AlphaPowers.ContainsKey("RIN-R06"))bonus+=r.RinLayers*2;
        var total=((System.Numerics.BigInteger)damage*hits+bonus)*(r.JewelBoostUsed?r.BoostMultiplier:1);
        profile=Enumerable.Range(0,hits).Select(i=>Bound(total/hits+(i<total%hits?1:0))).ToArray();r.Profiles[key]=profile;return profile;
    }
    public int BlockAmount(StarterCard c,CharacterRuntime recipient,int amount)
    {
        var r=Receipt(c);
        if(amount>0&&recipient==Archer&&ZeroManaBlockBonusAvailable&&r.ZeroManaEligible){ZeroManaBlockBonusAvailable=false;amount+=6;Metric("zeroManaBlockBonusTriggers");}
        if(recipient==Rin&&c.OwnerCharacterId=="CHAR_RIN"&&SelfReinforcement>0&&!r.SelfReinforcementUsed){amount=Bound((System.Numerics.BigInteger)amount+SelfReinforcement);SelfReinforcement=0;r.SelfReinforcementUsed=true;}
        if(recipient==Rin&&r.JewelBoostUsed&&AlphaPowers.ContainsKey("RIN-R06"))amount+=r.RinLayers;
        if(r.JewelBoostUsed)amount=Bound((System.Numerics.BigInteger)amount*r.BoostMultiplier);
        return Bound(amount);
    }
    public async Task IaEngineBlock()
    {
        if(!AlphaPowers.TryGetValue("ARC-U13",out int level))return;
        await CreatureCmd.GainBlock(Archer.Creature,level==2?6:4,ValueProp.Move,null);
        await CreatureCmd.GainBlock(Rin.Creature,level==2?3:2,ValueProp.Move,null);
        Log("IA_ENGINE_BLOCK",new{level});
    }
    public async Task ProjectedExhaust(PlayerChoiceContext ctx,ProjectedArm arm,string source)
    {
        if(!AlphaPowers.TryGetValue("ARC-U12",out int level)||ProjectedExhaustUsed)return;
        ProjectedExhaustUsed=true;await DrawArcher(ctx,1);await CreatureCmd.GainBlock(Archer.Creature,level==2?5:3,ValueProp.Move,null);
        if(level==2&&!Finished){var selected=await GameplayChoice.OptionalTuning(this,Reserve,1,null);if(selected is {Length:>0})await Tune(ctx,Reserve,selected);}
        Metric("projectedExhaustTriggerCount");Log("PROJECTED_EXHAUST_ENGINE",new{armId=arm.ArmId,source});
    }
    public Task DrawArcher(PlayerChoiceContext ctx,int amount)=>DrawMember(ctx,Archer,amount);
    public void ArmResolved(ProjectedArm arm,string source)
    {
        ArmActivityThisTurn=true;ArmUses++;
        if(!ProjectedArmsResolvedThisCombat.Add(arm.ArmId))return;
        AlphaMetrics["armsResolvedDistinct"]=ProjectedArmsResolvedThisCombat.Count;Metric(source=="NORMAL_PLAY"?"armsResolvedByNormalPlay":"armsResolvedByBroken");Log("ARM_RESOLVED_ADDED",new{armId=arm.ArmId,source});
    }
    public void NativePlayFinished(CardPlay play)
    {
        string? owner=play.Card is StarterCard own?own.OwnerCharacterId:GenericCombatCardOwnership.Get(play.Card)?.Member;
        if(owner!=Active.CharacterId||!successfulEvents.Add(play))return;
        if(owner=="CHAR_RIN")RinSuccessful=true;else ArcherSuccessful=true;
        if(play.Card is not StarterCard c)return;
        var r=Receipt(c);if(!r.FinishedIndices.Add(play.PlayIndex))return;r.Resolved=true;
        if(c.SourceCardId=="ARC-C16")c16Tickets.Add(c.InstanceId);
        if(c is ProjectedArm arm){ArmResolved(arm,"NORMAL_PLAY");r.ForgeEvent=true;}
        if(r.JewelBoostUsed&&!firstBoost){firstBoost=true;if(AlphaPowers.TryGetValue("RIN-R06",out int level))RinGrowthLayers=Math.Min(level==2?6:5,RinGrowthLayers+1);}
        if(r.ForgeEvent&&!firstForge){firstForge=true;if(AlphaPowers.TryGetValue("ARC-R06",out int level))ForgeLayers=Math.Min(level==2?6:5,ForgeLayers+1);}
        if(c is AlphaRewardCard)Metric(c.OwnerCharacterId=="CHAR_RIN"?"rinRewardCardsPlayed":"archerRewardCardsPlayed");
    }
    public async Task SettleSuccessfulPlay(PlayerChoiceContext ctx,CardPlay play)
    {
        if(!successfulEvents.Contains(play)||Finished||!settledEvents.Add(play))return;
        await SettleExpansionPlay(ctx,play);
        if(Finished)return;
        if(RinSuccessful&&c16Tickets.Count>0){int draws=c16Tickets.Count;c16Tickets.Clear();await DrawArcher(ctx,draws);}
        if(!rinR05Triggered&&RinSuccessful&&ArcherSuccessful&&AlphaPowers.TryGetValue("RIN-R05",out int level))
        {rinR05Triggered=true;energyDueTurn=Turn+1;int block=level==2?4:3;await CreatureCmd.GainBlock(Rin.Creature,block,ValueProp.Move,null);await CreatureCmd.GainBlock(Archer.Creature,block,ValueProp.Move,null);Log("CONTRACT_RESONANCE",new{block,nextTurnEnergy=1});}
    }
    public async Task C16(PlayerChoiceContext ctx,StarterCard c)
    {await Task.CompletedTask;} // Ticket is issued by the successful native finish event.
    public void CompleteAlphaPlay(StarterCard c)
    {
        if(alphaReceipts.Remove(c,out var r))Log(r.Resolved?"ALPHA_CARD_RESOLVED":"ALPHA_CARD_NOT_RESOLVED",new{cardId=c.SourceCardId,owner=c.OwnerCharacterId,r.RootSequence,r.EnergyPaid,r.ManaPaid,r.JewelSpent,r.IaApplied,r.Resolved});
        if(Finished)EmitAlphaSummary();
    }
    public void ClearGameplayState()
    {ClearExpansionState();U10Charges=RinGrowthLayers=ForgeLayers=0;U15Pending=false;energyDueTurn=-1;c16Tickets.Clear();alphaReceipts.Clear();TuningUsedByMember.Clear();}
    public void SetAlphaTarget(StarterCard c,string target)=>Receipt(c).Target=target;
    public void GiveGuardMaster(){GuardCharges=1;Log("STATUS_GUARD_MASTER",new{charges=1});}
    public bool SuppressField(FieldStatus field)
    {if(!FieldStatuses.Contains(field)||field.Owner!="ENEMY_CONTRACT"||field.Duration==0)return false;field.Suppressed=true;field.SuppressUntil=Turn+1;QaTargetTag.RefreshNumbers(this);Log("FIELD_SUPPRESSED",new{field.FieldId,field.Duration,field.SuppressUntil});return true;}
}
public static class RewardRules
{
    public static string Text(AlphaRewardCard c)=>GameplayCatalog.Text(c);
    public static FieldStatus[] Fields(ContractRuntime d)=>d.FieldStatuses.Where(f=>f.Owner=="ENEMY_CONTRACT"&&f.Duration!=0).ToArray();
    public static ProjectedArm[] Arms(ContractRuntime d,bool weapon=false)=>d.Archer.Hand.Cards.OfType<ProjectedArm>().Where(a=>!weapon||a.ArmId is "ARM_KANSHOU_BAKUYA" or "ARM_HRUNTING").ToArray();
    public static Creature[] PrecisionTargets(ContractRuntime d)=>d.Enemy==null?d.Combat.Enemies.Where(c=>c.IsAlive).ToArray():new[]{d.Enemy.Active,d.Enemy.Master,d.Enemy.Servant}.Distinct().Where(c=>c.IsAlive&&(c==d.Enemy.Active||c.Powers.Any(p=>p.Type==MegaCrit.Sts2.Core.Entities.Powers.PowerType.Debuff))).ToArray();
    public static bool CanPlay(ContractRuntime d,AlphaRewardCard c)=>GameplayRules.Availability(d,c).Length==0;
    public static bool NeedsChoice(AlphaRewardCard c)=>true;
    public static Task Play(PlayerChoiceContext ctx,CardPlay play,ContractRuntime d,AlphaRewardCard c)=>GameplayRules.Play(ctx,play,d,c);
}
