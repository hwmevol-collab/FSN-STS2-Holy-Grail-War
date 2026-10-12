using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.Models.Cards;
namespace RinArcherCore;

// Exact initial shop subset; native models, unlocks, rarity, pricing and effects.
// More complex colorless generation/powers stay closed until separately adapted.
public static class NativePermanentCards
{
    static readonly ConditionalWeakTable<CardModel,CombatCardOwner> Owners=new();
    public static readonly Type[] Types=[typeof(Finesse),typeof(FlashOfSteel),typeof(DarkShackles),typeof(MasterOfStrategy),typeof(HandOfGreed)];
    public static bool Supported(CardModel card)=>Types.Contains(card.GetType())&&card.Pool is ColorlessCardPool;
    public static CombatCardOwner? Get(CardModel card)=>Owners.TryGetValue(card,out var owner)?owner:null;
    public static string Owner(CardModel card)=>card is StarterCard s?s.OwnerCharacterId:Get(card)?.Member??throw new InvalidOperationException("Unbound permanent member");
    public static string Instance(CardModel card)=>card is StarterCard s?s.InstanceId:Get(card)?.InstanceId??throw new InvalidOperationException("Unbound permanent instance");
    public static string Id(CardModel card)=>card is StarterCard s?s.SourceCardId:card.Id.ToString();
    public static void Bind(CardModel card,string member,string instance)
    {
        if(!Supported(card)||member is not (RunEconomy.Rin or RunEconomy.Archer)||instance.Length==0)throw new InvalidOperationException("Unaudited permanent card");
        if(Get(card) is {} previous){if(previous.Member!=member||previous.InstanceId!=instance)throw new InvalidOperationException("Permanent card identity changed");return;}
        Owners.Add(card,new(instance,member));
    }
    public static void Restore(Player p,string member,CardModel card,int index)
    {
        if(Get(card)!=null)return;
        var saved=member==RunEconomy.Rin?ContractSave.Get(p).Master.PermanentDeck:ContractSave.Get(p).Servant.PermanentDeck;
        if(index>=saved.Count||saved[index].CardId!=card.Id.ToString()||saved[index].OwnerCharacterId!=member||saved[index].UpgradeLevel!=card.CurrentUpgradeLevel)
            throw new InvalidOperationException("Native permanent card differs from saved authoritative pile");
        Bind(card,member,saved[index].InstanceId);
    }
}
