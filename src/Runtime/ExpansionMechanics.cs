using System.Numerics;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Random;
namespace RinArcherCore;
public sealed partial class ContractRuntime
{
    public const int NativeValueLimit=999999999; // Creature HP/block and PowerModel.SetAmount, game 0.107.1.
    public int SelfReinforcement{get;set;}
    public BigInteger BoostMultiplier{get;private set;}=BigInteger.One;
    public BigInteger ArmUses{get;private set;}=BigInteger.Zero;
    public bool EngineLimitReached{get;private set;}
    BigInteger futureEnergyDebt;
    int transferDepth,archerHits;
    readonly HashSet<CardPlay> settledEvents=[];
    readonly ConditionalWeakTable<DamageResult,object> countedHits=new(),countedDefenses=new();
    public int Bound(BigInteger value)
    {
        if(value<=NativeValueLimit)return (int)BigInteger.Max(0,value);
        EngineLimitReached=true;return NativeValueLimit;
    }
    public async Task ExpansionEnergy(int amount)
    {if(amount>0)await ContractEffectResolver.GainEnergy(Player,Math.Min(amount,int.MaxValue-Energy));}
    public void BorrowFutureEnergy()=>futureEnergyDebt+=2;
    public void ApplyEnergyDebt(){if(futureEnergyDebt==0)return;Player.PlayerCombatState!.Energy=(int)BigInteger.Max(0,(BigInteger)Energy-futureEnergyDebt);Log("FUTURE_ENERGY_DEBT",new{amount=futureEnergyDebt.ToString()});futureEnergyDebt=0;}
    public static bool AuditedDebuff(PowerModel p)=>p is WeakPower or VulnerablePower or FrailPower or PoisonPower;
    public static int DebuffTypes(Creature target,bool threeOnly=false)=>target.Powers.Count(p=>p.Amount>0&&(threeOnly?p is WeakPower or VulnerablePower or FrailPower:AuditedDebuff(p)));
    public PowerModel[] Transferable(CharacterRuntime source,CharacterRuntime target)=>source.Creature.Powers.Where(p=>AuditedDebuff(p)&&p.Amount>0&&target.Creature.IsAlive&&target.Creature.CanReceivePowers&&CompatibleStatus(p,target.Creature)).ToArray();
    static bool CompatibleStatus(PowerModel source,Creature recipient)
    {
        var existing=recipient.Powers.FirstOrDefault(p=>p.GetType()==source.GetType());
        return existing==null||existing.Applier==source.Applier&&existing.SkipNextDurationTick==source.SkipNextDurationTick;
    }
    public async Task<bool> TransferDebuff(PlayerChoiceContext ctx,PowerModel source,CharacterRuntime target,int? partial=null)
    {
        if(!AuditedDebuff(source)||!source.Owner.Powers.Contains(source)||!target.Creature.IsAlive||!CompatibleStatus(source,target.Creature))return false;
        int amount=partial??source.Amount;if(amount<=0||amount>source.Amount)return false;
        // Native PowerModel forbids changing Owner. Create the same audited native type, retaining its clock/source.
        PowerModel canonical=source switch{WeakPower=>ModelDb.Power<WeakPower>(),VulnerablePower=>ModelDb.Power<VulnerablePower>(),FrailPower=>ModelDb.Power<FrailPower>(),PoisonPower=>ModelDb.Power<PoisonPower>(),_=>throw new InvalidOperationException("Unsupported transfer")};
        var copy=canonical.ToMutable();bool skip=source.SkipNextDurationTick;int start=source.AmountOnTurnStart;
        var existing=target.Creature.Powers.FirstOrDefault(p=>p.GetType()==source.GetType());int before=existing?.Amount??0;
        transferDepth++;
        try
        {
            using var scope=CompatibilityExecution.Bind(new(Player,"CONTRACT_DEBUFF_TRANSFER","ApplyPower",[],target.Creature,null));
            await PowerCmd.Apply(ctx,copy,target.Creature,amount,null,null);
            var applied=target.Creature.Powers.FirstOrDefault(p=>p.GetType()==source.GetType());int gained=(applied?.Amount??0)-before;
            if(gained!=amount)
            {
                if(gained>0)await PowerCmd.ModifyAmount(ctx,applied!,-gained,null,null);
                Log("DEBUFF_TRANSFER_REJECTED",new{power=source.Id.Entry,amount,gained});return false;
            }
            applied!.SkipNextDurationTick=skip;
            applied.AmountOnTurnStart=Bound((BigInteger)(existing?.AmountOnTurnStart??0)+Math.Min(start,amount));
            if(existing==null){applied.Applier=source.Applier;applied.Target=source.Target;}
            if(amount==source.Amount)await PowerCmd.Remove(source);else await PowerCmd.ModifyAmount(ctx,source,-amount,null,null);
            Log("DEBUFF_TRANSFERRED",new{power=source.Id.Entry,amount,skip,member=target.CharacterId,applier=applied.Applier?.CombatId});return true;
        }
        finally{transferDepth--;}
    }
    public async Task ObservePowerChange(PlayerChoiceContext ctx,PowerModel power,decimal delta,Creature? applier,bool newlyPresent)
    {
        if(Finished||transferDepth>0||delta<=0||power.Amount<=0||!AuditedDebuff(power))return;
        if(power.Owner==Rin.Creature&&applier?.IsEnemy==true&&AlphaPowers.TryGetValue("RIN-R12",out int redirect))
        {
            if(await TransferDebuff(ctx,power,Archer,Math.Min(power.Amount,(int)delta))){GainMana(redirect==2?4:3);GainJewel(redirect==2?2:1);}
        }
        else if(power.Owner.IsEnemy&&newlyPresent&&AlphaPowers.TryGetValue("RIN-U22",out int level))
        {GainMana(1);if(level==2)GainJewel(1);await DrawMember(ctx,Rin,1);}
    }
    public async Task OwnBlockEvent(Creature recipient,decimal gained,CardModel? card)
    {
        bool archerCard=card is StarterCard s?s.OwnerCharacterId=="CHAR_ARCHER":card!=null&&GenericCombatCardOwnership.Get(card)?.Member=="CHAR_ARCHER";
        if(Finished||gained<=0||recipient!=Archer.Creature||!archerCard||!AlphaPowers.TryGetValue("ARC-U19",out int level))return;
        GainMana(level==2?2:1);
        // A single ordinary enemy is the only unambiguous front. Multiple ordinary enemies use native target RNG.
        var legal=GameplayChoice.Enemies(this);Creature? enemy=Enemy?.Active??(legal.Length==0?null:legal.Length==1?legal[0]:Player.RunState.Rng.CombatTargets.NextItem(legal));
        if(enemy?.IsAlive==true)await GameApi.Damage(EventChoiceContext(),enemy,level==2?6:4,ValueProp.Unpowered,Archer.Creature,null);
    }
    public async Task ActualArcherHit(PlayerChoiceContext ctx,Creature? dealer,DamageResult hit,ValueProp props,Creature target)
    {
        if(Finished||dealer!=Archer.Creature||!target.IsEnemy||!props.HasFlag(ValueProp.Move)||props.HasFlag(ValueProp.Unpowered)||countedHits.TryGetValue(hit,out _)||!AlphaPowers.TryGetValue("ARC-R09",out int level))return;
        countedHits.Add(hit,new());archerHits++;int threshold=level==2?2:3;
        if(archerHits>=threshold){archerHits-=threshold;await ExpansionEnergy(1);await DrawArcher(ctx,1);}
    }
    public async Task ActualArcherDefense(PlayerChoiceContext ctx,Creature target,DamageResult hit,ValueProp props,Creature? dealer)
    {
        if(Finished||target!=Archer.Creature||dealer?.IsEnemy!=true||!props.HasFlag(ValueProp.Move)||props.HasFlag(ValueProp.Unpowered)||hit.BlockedDamage<1||hit.UnblockedDamage!=0||countedDefenses.TryGetValue(hit,out _)||!AlphaPowers.TryGetValue("ARC-R11",out int level))return;
        countedDefenses.Add(hit,new());await PowerCmd.Apply<StrengthPower>(ctx,target,level,null,null);await PowerCmd.Apply<DexterityPower>(ctx,target,level,null,null);
    }
    public async Task SettleExpansionPlay(PlayerChoiceContext ctx,CardPlay play)
    {
        if(play.Card is not StarterCard card)
        {
            // Audited native generated statuses also have a real bank owner and pay no contract mana.
            if(GenericCombatCardOwnership.Get(play.Card)?.Member=="CHAR_ARCHER"&&AlphaPowers.TryGetValue("ARC-R13",out int nativeCycle))
            {await ExpansionEnergy(nativeCycle);await DrawArcher(ctx,nativeCycle==2?2:1);}
            return;
        }
        var r=Receipt(card);
        if(r.JewelBoostUsed&&!r.BoostSettled)
        {
            r.BoostSettled=true;
            if(AlphaPowers.ContainsKey("RIN-R11"))BoostMultiplier*=2;
            if(AlphaPowers.TryGetValue("RIN-U17",out int gem)){GainJewel(1);await CreatureCmd.GainBlock(Rin.Creature,gem==2?6:3,ValueProp.Move,null);}
        }
        if(card.OwnerCharacterId=="CHAR_RIN"&&r.ManaPaid>0&&play.PlayIndex==0&&AlphaPowers.TryGetValue("RIN-R08",out int cycle))
        {GainJewel(1);await DrawMember(ctx,Rin,cycle==2?2:1);}
        // Broken weapons count toward finishers, but these engines require a normal successful arm play.
        if(card is ProjectedArm arm)
        {
            if(AlphaPowers.TryGetValue("ARC-U17",out int mana))GainMana(mana);
            if(AlphaPowers.TryGetValue("ARC-U18",out int chain))await GenerateOthers(ctx,arm.ArmId,chain==2?2:1,"ARC-U18",true);
            if(AlphaPowers.TryGetValue("ARC-R08",out int multiply))await GenerateOthers(ctx,arm.ArmId,multiply==2?3:2,"ARC-R08",false);
        }
        if(card.OwnerCharacterId=="CHAR_ARCHER"&&(play.PlayIndex>0||r.ManaPaid==0)&&AlphaPowers.TryGetValue("ARC-R13",out int transcend))
        {await ExpansionEnergy(transcend);await DrawArcher(ctx,transcend==2?2:1);}
    }
    async Task GenerateOthers(PlayerChoiceContext ctx,string used,int amount,string source,bool distinct)
    {
        var choices=Arsenal.Ids.Where(id=>id!=used).ToList();
        for(int i=0;i<amount&&!Finished;i++)
        {
            if(!HasArcherSpace()){Log("PROJECTION_UNAVAILABLE",new{reason=FsnLoc.Text("UI_D78BF118B3F2"),source});break;}
            var id=Player.RunState.Rng.CombatCardGeneration.NextItem(choices)!;
            if(await GenerateArm(ctx,id,source,energyOverrideThisTurn:0)==null)break;
            if(distinct)choices.Remove(id);
        }
    }
    public void ClearExpansionState(){SelfReinforcement=archerHits=0;futureEnergyDebt=0;BoostMultiplier=1;ArmUses=0;EngineLimitReached=false;settledEvents.Clear();}
}
