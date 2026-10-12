using System.Runtime.CompilerServices;
namespace RinArcherCore;
public sealed record CombatCardOwner(string InstanceId,string Member);
public static class GenericCombatCardOwnership
{
    static readonly ConditionalWeakTable<CardModel,CombatCardOwner> Owners=new();
    static readonly ConditionalWeakTable<ContractRuntime,Counter> Counters=new();
    sealed class Counter{public int Value;}
    public static CombatCardOwner? Get(CardModel card)=>Owners.TryGetValue(card,out var owner)?owner:null;
    public static void BindPermanentClone(CardModel card,string member,string instance)
    {
        if(!NativePermanentCards.Supported(card)||card.DeckVersion==null||NativePermanentCards.Owner(card.DeckVersion)!=member)throw new InvalidOperationException("Invalid native permanent clone");
        Owners.Add(card,new(instance,member));
    }
    public static void Register(ContractRuntime d,CardModel card,CardPile destination)
    {
        if(card is StarterCard||!GenericCompatibility.Enabled(d.Player)||NativePermanentCards.Get(card)!=null)return;
        if(Get(card) is {} bound&&NativePermanentCards.Supported(card))
        {
            if(!d.PileTypes.Any(t=>ReferenceEquals(d.Member(bound.Member).Pile(t),destination))&&!ReferenceEquals(destination,d.Member(bound.Member).Deck))throw new InvalidOperationException("Native card moved into wrong member bank");
            return;
        }
        if(card.Owner!=d.Player||card.DeckVersion!=null)throw new InvalidOperationException("Unaudited generated card type cannot enter contract banks");
        string? member=new[]{d.Rin,d.Archer}.FirstOrDefault(m=>d.PileTypes.Any(t=>ReferenceEquals(m.Pile(t),destination)))?.CharacterId;
        if(member==null)throw new InvalidOperationException("Generated combat status requires an exact native bank destination");
        if(Owners.TryGetValue(card,out var existing))
        {if(existing.Member!=member)throw new InvalidOperationException("Generated combat card owner changed");return;}
        Owners.Add(card,new($"{d.Seed}:NATIVE_STATUS:{++Counters.GetOrCreateValue(d).Value}",member));
    }
}
[HarmonyPatch]
public static class GenericStatusOwnerRegistration
{
    static System.Reflection.MethodBase TargetMethod()=>GameApi.PileAdd;
    [HarmonyPriority(Priority.First)]
    static void Prefix(IEnumerable<CardModel> cards,CardPile newPile)
    {
        foreach(var card in cards.Where(c=>c is not StarterCard))
            if(ContractRuntime.For(card.Owner) is {} d&&GenericCompatibility.Enabled(d.Player))GenericCombatCardOwnership.Register(d,card,newPile);
    }
}
