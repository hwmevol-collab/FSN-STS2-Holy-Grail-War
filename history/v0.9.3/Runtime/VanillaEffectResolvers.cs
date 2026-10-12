using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Commands.Builders;
using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;

public sealed class CompatibilityRunState
{
    public string MatrixRevision{get;set;}="";
    public string MatrixSignature{get;set;}="";
    public Dictionary<string,string> MemberBindings{get;set;}=new(StringComparer.Ordinal);
    public Dictionary<string,int> ContractCounters{get;set;}=new(StringComparer.Ordinal);
    public Dictionary<int,RewardBudgetAllocation> RewardAllocations{get;set;}=[];
    public Dictionary<int,string> RewardOptionModifierOwners{get;set;}=[];
}
public sealed record RewardBudgetAllocation(string Owner,int Delta,bool BeforeRoll);
public sealed record ActiveScopeSnapshot(ContractRuntime Contract,string Member,Creature Creature)
{
    public CharacterRuntime Character=>Contract.Member(Member);
}
public static class CompatibilityExecution
{
    static readonly AsyncLocal<EffectScopeBinding?> CurrentSlot=new();
    public static EffectScopeBinding? Current=>CurrentSlot.Value;
    public static IDisposable Bind(EffectScopeBinding binding)
    {var before=CurrentSlot.Value;CurrentSlot.Value=binding;return new BindingLease(()=>CurrentSlot.Value=before);}
    sealed class BindingLease(Action release):IDisposable
    {bool disposed;public void Dispose(){if(!disposed){disposed=true;release();}}}
}
public sealed record EffectScopeBinding(Player Player,string ContentId,string Trigger,IReadOnlyList<CompatibilityEffect> Rows,
    Creature? PersonalRecipient,ActiveScopeSnapshot? ActiveSnapshot,string? DeckMember=null);

public static class ContractEffectResolver
{
    public static void RequireContract(Player p)
    {if(p.Character is not RinContractCharacter)throw new InvalidOperationException("RinContract capability required");}
    public static int Counter(Player p,string effectId,int delta)
    {
        RequireContract(p);var counters=ContractSave.Get(p).Compatibility.ContractCounters;
        int value=counters.GetValueOrDefault(effectId)+delta;counters[effectId]=value;return value;
    }
    public static async Task GainEnergy(Player p,int amount)
    {RequireContract(p);await PlayerCmd.GainEnergy(amount,p);}
    public static async Task GainGold(Player p,int amount)
    {RequireContract(p);await PlayerCmd.GainGold(amount,p);}
}
public static class ActiveCharacterEffectResolver
{
    public static ActiveScopeSnapshot Capture(ContractRuntime d,string effectId)
    {
        var result=new ActiveScopeSnapshot(d,d.Active.CharacterId,d.Active.Creature);
        ContractSave.Log(d.Player,"ACTIVE_SCOPE_RESOLVED",new{effectId,member=result.Member});return result;
    }
    public static async Task InActiveHand(ActiveScopeSnapshot snapshot,Func<Task> action)
    {
        var d=snapshot.Contract;
        if(d.Active.CharacterId!=snapshot.Member)throw new InvalidOperationException("Active hand changed before effect execution");
        var reserve=d.Reserve;var before=d.PileTypes.ToDictionary(t=>t,t=>reserve.Pile(t).Cards.ToArray());
        await action();
        if(before.Any(x=>!x.Value.SequenceEqual(reserve.Pile(x.Key).Cards)))throw new InvalidOperationException("VANILLA_EFFECT_CHANGED_RESERVE_BANK");
    }
}
public static class CardOwnerEffectResolver
{
    public static CharacterRuntime Resolve(ContractRuntime d,CardModel card,string effectId)
    {
        if((GenericCombatCardOwnership.Get(card)??NativePermanentCards.Get(card)) is {} native)
        {
            var member=d.Member(native.Member);
            if(card.Owner!=d.Player||!d.PileTypes.Any(t=>member.Pile(t).Cards.Contains(card))&&!member.Deck.Cards.Contains(card))throw new InvalidOperationException("Native card instance outside its bound bank");
            ContractSave.Log(d.Player,"CARD_OWNER_SCOPE_RESOLVED",new{effectId,instanceId=native.InstanceId,owner=native.Member});return member;
        }
        if(card is not StarterCard owned||owned.InstanceId.Length==0||owned.Owner!=d.Player)
            throw new InvalidOperationException("Unregistered card instance owner");
        var owner=d.Member(owned.OwnerCharacterId);
        bool found=d.PileTypes.Any(t=>owner.Pile(t).Cards.Contains(card))||owner.Deck.Cards.Contains(card)||card.DeckVersion is StarterCard permanent&&permanent.OwnerCharacterId==owner.CharacterId;
        if(!found)throw new InvalidOperationException("Card instance does not belong to the contract bank/deck");
        ContractSave.Log(d.Player,"CARD_OWNER_SCOPE_RESOLVED",new{effectId,instanceId=owned.InstanceId,owner=owner.CharacterId});return owner;
    }
    public static CharacterRuntime Resolve(ContractRuntime d,string cardInstanceId,string effectId)
    {
        var cards=new[]{d.Rin,d.Archer}.SelectMany(m=>d.PileTypes.SelectMany(t=>m.Pile(t).Cards).Concat(m.Deck.Cards)).Distinct();
        var card=cards.SingleOrDefault(c=>c is StarterCard owned?owned.InstanceId==cardInstanceId:(GenericCombatCardOwnership.Get(c)??NativePermanentCards.Get(c))?.InstanceId==cardInstanceId)??throw new InvalidOperationException("Unknown card instance ID");
        return Resolve(d,card,effectId);
    }
}
public static class DamageTargetEffectResolver
{
    public static Creature Resolve(ContractRuntime d,Creature recipient,string effectId)
    {
        if(recipient!=d.Rin.Creature&&recipient!=d.Archer.Creature&&!d.Combat.Enemies.Contains(recipient))throw new InvalidOperationException("Damage recipient outside this combat");
        ContractSave.Log(d.Player,"DAMAGE_TARGET_SCOPE_RESOLVED",new{effectId,target=recipient==d.Rin.Creature?RunEconomy.Rin:recipient==d.Archer.Creature?RunEconomy.Archer:recipient.Monster!.Id.ToString()});return recipient;
    }
}
public sealed record MemberValuePreview(string Member,int CurrentHp,int MaxHp,int AfterHp,int AfterMaxHp,bool Eligible=true)
{
    public string Text=>$"{(Member==RunEconomy.Rin?FsnLoc.Text("RIN_ROLE"):FsnLoc.Text("ARCHER_ROLE"))}: {CurrentHp}/{MaxHp} → {AfterHp}/{AfterMaxHp}"+(Eligible?"":FsnLoc.Text("UI_7BDE63943AB4"));
}
public static class MemberTargetResolver
{
    public static Func<Player,string,IReadOnlyList<MemberValuePreview>,Task<string?>>? QaChoice{get;set;}
    public static Creature Creature(Player p,string member)
    {
        ContractEffectResolver.RequireContract(p);
        if(member is not (RunEconomy.Rin or RunEconomy.Archer))throw new ArgumentException("Unknown contract member");
        if(ContractRuntime.For(p) is {Finished:false} d)return d.Member(member).Creature;
        return member==RunEconomy.Rin?p.Creature:RunEconomy.Servant(p);
    }
    public static IReadOnlyList<MemberValuePreview> Preview(Player p,Func<Creature,(int Hp,int Max)> after)
        =>new[]{RunEconomy.Rin,RunEconomy.Archer}.Select(id=>{var c=Creature(p,id);var result=after(c);return new MemberValuePreview(id,c.CurrentHp,c.MaxHp,result.Hp,result.Max);}).ToArray();
    public static IReadOnlyList<MemberValuePreview> HealPercentPreview(Player p,decimal percentage)
        =>Preview(p,c=>((int)Math.Clamp(c.CurrentHp+c.MaxHp*percentage/100m,0,c.MaxHp),c.MaxHp));
    public static IReadOnlyList<MemberValuePreview> MaxHpPreview(Player p,decimal delta)
        =>Preview(p,c=>{int next=(int)Math.Max(1,c.MaxHp+delta);return (Math.Min(next,c.CurrentHp+(int)Math.Max(0,delta)),next);});
    public static async Task<string?> Choose(Player p,string effectId,IReadOnlyList<MemberValuePreview> previews,string description,bool cancellable=true)
    {
        ContractEffectResolver.RequireContract(p);
        string? selected;
        if(QaChoice!=null)
        {
            if(!TestMode.IsOn&&!OS.GetUserDataDir().Contains("RinArcherE2AAmended-20261009"))throw new InvalidOperationException("QA selector outside isolated profile");
            selected=await QaChoice(p,effectId,previews);
        }
        else selected=await MemberTargetUi.Choose(description,previews,cancellable);
        if(selected!=null)
        {
            if(selected is not (RunEconomy.Rin or RunEconomy.Archer))throw new InvalidOperationException("Invalid member selection");
            if(previews.Any(preview=>preview.Member==selected&&!preview.Eligible))throw new InvalidOperationException("Selected member does not meet native effect conditions");
            ContractSave.Log(p,"MEMBER_TARGET_SELECTED",new{effectId,member=selected});
        }
        return selected;
    }
    public static void Persist(Player p,string effectId,string member)
    {ContractEffectResolver.RequireContract(p);_ = Creature(p,member);ContractSave.Get(p).Compatibility.MemberBindings[effectId]=member;}
    public static void Synchronize(Player p)
    {
        var archer=Creature(p,RunEconomy.Archer);var state=ContractSave.Get(p);
        state.ArcherHp=archer.CurrentHp;state.ArcherMaxHp=archer.MaxHp;ContractSave.Sync(p);
    }
}
public static class DualRewardModifierResolver
{
    public static bool HasOptionModifiers(Player p)=>p.Relics.Any(r=>GenericCompatibility.Registry.GetEffectScopes(r.Id.ToString()).Any(e=>e.Trigger is "TryModifyCardRewardOptions" or "TryModifyCardRewardOptionsLate"));
    public static void AllocateOptionModifiers(Player p,int index,string owner)
    {
        ContractEffectResolver.RequireContract(p);
        if(owner is not (RunEconomy.Rin or RunEconomy.Archer)||ContractSave.Get(p).DualRewards.Any(r=>r.RewardIndex==index&&r.RinOffer.Count>0))throw new InvalidOperationException("Reward option modifier allocation must precede hidden rolls");
        if(!ContractSave.Get(p).Compatibility.RewardOptionModifierOwners.TryAdd(index,owner))throw new InvalidOperationException("Reward option modifier already allocated");
    }
    public static List<RewardOfferCard> ApplyOptionModifiers(Player p,int index,string owner,List<RewardOfferCard> offers,CardRarityOddsType type)
    {
        if(!HasOptionModifiers(p))return offers;
        if(!ContractSave.Get(p).Compatibility.RewardOptionModifierOwners.TryGetValue(index,out var selected))throw new InvalidOperationException("Reward option modifier owner required before hidden roll");
        if(selected!=owner)return offers;
        var cards=offers.Select(offer=>{var card=(StarterCard)p.RunState.CreateCard(AlphaRewardRegistry.Card(offer.CardId),p);card.InstanceId=$"reward:{index}:{owner}:{offer.CardId}";return new CardCreationResult(card);}).ToList();
        var options=new CardCreationOptions(cards.Select(c=>c.Card),CardCreationSource.Encounter,type);
        if(MegaCrit.Sts2.Core.Hooks.Hook.TryModifyCardRewardOptions(p.RunState,p,cards,options,out var modifiers))
            NativeRewardTransactions.Track(MegaCrit.Sts2.Core.Hooks.Hook.AfterModifyingCardRewardOptions(p.RunState,modifiers));
        if(cards.Count!=offers.Count||cards.Select(c=>c.Card).OfType<StarterCard>().Any(c=>c.OwnerCharacterId!=owner)||cards.Any(c=>c.Card is not AlphaRewardCard))throw new InvalidOperationException("Native reward modifier changed owner/pool/value budget");
        return cards.Select(c=>new RewardOfferCard(((StarterCard)c.Card).SourceCardId,owner,c.Card.CurrentUpgradeLevel)).ToList();
    }
    public static RewardBudgetAllocation Allocate(Player p,int rewardIndex,int delta,string chosenOwner,bool alreadyRolled)
    {
        ContractEffectResolver.RequireContract(p);
        if(alreadyRolled||ContractSave.Get(p).DualRewards.Any(r=>r.RewardIndex==rewardIndex&&r.RinOffer.Count>0)||chosenOwner is not (RunEconomy.Rin or RunEconomy.Archer))throw new InvalidOperationException("Reward allocation must precede hidden rolls");
        var state=ContractSave.Get(p).Compatibility;
        if(state.RewardAllocations.ContainsKey(rewardIndex))throw new InvalidOperationException("Reward modifier already allocated");
        var result=new RewardBudgetAllocation(chosenOwner,delta,true);state.RewardAllocations.Add(rewardIndex,result);return result;
    }
    public static int Count(Player p,int rewardIndex,string owner,int nativeCount=3)
    {
        if(!ContractSave.Get(p).Compatibility.RewardAllocations.TryGetValue(rewardIndex,out var allocation))return nativeCount;
        if(!allocation.BeforeRoll)throw new InvalidOperationException("Reward allocation after hidden roll");
        return nativeCount+(allocation.Owner==owner?allocation.Delta:0);
    }
}
