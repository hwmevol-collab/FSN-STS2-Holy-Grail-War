using System.Reflection;
using MegaCrit.Sts2.Core.Rewards;
namespace RinArcherCore;
public static class VanillaCardAcquisition
{
    public static string? Member(Player p)
    {
        if(CompatibilityExecution.Current is not {} f||f.Player!=p)return null;
        if(f.DeckMember!=null)return f.DeckMember;
        if(f.PersonalRecipient!=null)return new[]{RunEconomy.Rin,RunEconomy.Archer}.FirstOrDefault(m=>MemberTargetResolver.Creature(p,m)==f.PersonalRecipient);
        return null;
    }
    public static void Bind(CardModel card,Player p,string? selected=null)
    {
        if(card is StarterCard s)
        {
            if(s.InstanceId.Length==0||RunEconomy.Permanent(p).Any(c=>c!=card&&NativePermanentCards.Instance(c)==s.InstanceId))s.InstanceId="native-add:"+s.OwnerCharacterId+":"+(++ContractSave.Get(p).NextPermanentInstance);
            return;
        }
        if(NativePermanentCards.Get(card)!=null)return;
        string member=selected??Member(p)??throw new InvalidOperationException("Native permanent acquisition requires member before result generation");
        NativePermanentCards.Bind(card,member,"native-add:"+member+":"+(++ContractSave.Get(p).NextPermanentInstance));
    }
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.Add),[typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool)])]
public static class VanillaPermanentAddBinding
{
    [HarmonyPriority(Priority.First+100)]
    static void Prefix(IEnumerable<CardModel> cards,ref CardPile newPile)
    {
        var list=cards.ToArray();if(list.Length==0||list[0].Owner is not {} p||!GenericCompatibility.Enabled(p))return;
        if(newPile.Type!=PileType.Deck&&!ReferenceEquals(newPile,ContractSave.Deck(p,RunEconomy.Archer)))return;
        foreach(var card in list)VanillaCardAcquisition.Bind(card,p);
        var owners=list.Select(NativePermanentCards.Owner).Distinct().ToArray();
        if(owners.Length!=1)throw new InvalidOperationException("Native permanent batch has mixed member owners");
        newPile=ContractSave.Deck(p,owners[0]);
    }
}
[HarmonyPatch(typeof(RunState),nameof(RunState.CloneCard))]
public static class VanillaPermanentCloneBinding
{
    static void Postfix(CardModel __0,CardModel __result)
    {
        var card=__0;
        if(card.Owner is not {} p||!GenericCompatibility.Enabled(p)||!RunEconomy.Permanent(p).Contains(card))return;
        if(__result is StarterCard s)s.InstanceId="native-copy:"+s.OwnerCharacterId+":"+(++ContractSave.Get(p).NextPermanentInstance);
        else VanillaCardAcquisition.Bind(__result,p,NativePermanentCards.Owner(card));
    }
}
[HarmonyPatch(typeof(RewardsCmd),nameof(RewardsCmd.OfferCustom))]
public static class VanillaSpecialRewardOwner
{
    static void Prefix(Player player,IEnumerable<Reward> rewards)
    {
        if(!GenericCompatibility.Enabled(player)||CompatibilityExecution.Current?.Player!=player)return;
        foreach(var reward in rewards.OfType<SpecialCardReward>())
            VanillaCardAcquisition.Bind((CardModel)AccessTools.Field(typeof(SpecialCardReward),"_card").GetValue(reward)!,player);
    }
}
