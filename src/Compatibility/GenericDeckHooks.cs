using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.CardSelection;
namespace RinArcherCore;

[HarmonyPatch]
public static class GenericRandomPermanentUnion
{
    static bool Prepare()=>GenericCompatibility.Registry.IsValid;
    static IEnumerable<MethodBase> TargetMethods()
    {
        foreach(var method in GenericCompatibility.NativeMethods().OfType<MethodInfo>())
        {
            var entry=GenericCompatibility.Registry.Entries.First(e=>e.ModelType==method.DeclaringType!.FullName);
            if(!entry.Effects.Any(e=>e.Trigger==method.Name&&e.Scope is "RANDOM_PERMANENT_CARD_UNION" or "CHOOSE_DECK"))continue;
            var machine=method.GetCustomAttribute<AsyncStateMachineAttribute>();
            var target=machine==null?method:AccessTools.Method(machine.StateMachineType,"MoveNext");
            if(VanillaExpandedAdapters.Audited(entry.ContentId)&&!PatchProcessor.GetOriginalInstructions(target).Any(i=>i.Calls(AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Cards)))))continue;
            yield return target;
        }
    }
    public static IReadOnlyList<CardModel> Cards(CardPile pile)
    {
        if(CompatibilityExecution.Current is {} frame&&GenericCompatibility.Enabled(frame.Player)&&ReferenceEquals(pile,frame.Player.Deck))
            return frame.DeckMember is {} member?ContractSave.Deck(frame.Player,member).Cards:DualDeckCardSelector.LegalPermanentUnion(frame.Player,_=>true);
        return pile.Cards;
    }
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Cards));int count=0;
        foreach(var instruction in instructions)
        {
            if(instruction.Calls(getter)){instruction.opcode=OpCodes.Call;instruction.operand=AccessTools.Method(typeof(GenericRandomPermanentUnion),nameof(Cards));count++;}
            yield return instruction;
        }
        if(count==0)throw new InvalidOperationException("RANDOM_PERMANENT_CARD_UNION native getter changed");
    }
}
[HarmonyPatch]
public static class GenericNativeDeckSelection
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckForUpgrade)),AccessTools.Method(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckForRemoval))};
    [HarmonyPriority(Priority.First+200)]
    static bool Prefix(Player player,CardSelectorPrefs prefs,MethodBase __originalMethod,object[] __args,ref Task<IEnumerable<CardModel>> __result)
    {
        if(!GenericCompatibility.Enabled(player)||CompatibilityExecution.Current is not {} frame||!frame.Rows.Any(r=>r.Scope=="DUAL_DECK_SELECTOR"))return true;
        var action=__originalMethod.Name==nameof(CardSelectCmd.FromDeckForUpgrade)?DeckServiceAction.Upgrade:DeckServiceAction.Remove;
        var additional=__args.OfType<Func<CardModel,bool>>().FirstOrDefault();
        bool Predicate(CardModel card)=>(action==DeckServiceAction.Upgrade?card.IsUpgradable:card.IsRemovable)&&(additional==null||additional(card));
        __result=Select(player,action,prefs,Predicate);return false;
    }
    static async Task<IEnumerable<CardModel>> Select(Player player,DeckServiceAction action,CardSelectorPrefs prefs,Func<CardModel,bool> predicate)
    {
        var union=DualDeckCardSelector.LegalPermanentUnion(player,predicate);
        if(CardSelectCmd.Selector!=null)return await CardSelectCmd.Selector.GetSelectedCards(union,prefs.MinSelect,prefs.MaxSelect);
        return await DualDeckCardSelector.Select(player,action,prefs.MaxSelect,predicate,true,prefs.Prompt.GetFormattedText(),prefs);
    }
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.RemoveFromDeck),[typeof(IReadOnlyList<CardModel>),typeof(bool)])]
public static class GenericPermanentRemovalOwner
{
    static void Prefix(out Player? __state)
    {
        __state=ContractMerchant.RemovalOwner.Value;
        if(CompatibilityExecution.Current is {} frame&&frame.Rows.Any(r=>r.Scope=="DUAL_DECK_SELECTOR"))ContractMerchant.RemovalOwner.Value=frame.Player;
    }
    static void Postfix(Player? __state)=>ContractMerchant.RemovalOwner.Value=__state;
    static Exception? Finalizer(Exception? __exception,Player? __state){ContractMerchant.RemovalOwner.Value=__state;return __exception;}
}
