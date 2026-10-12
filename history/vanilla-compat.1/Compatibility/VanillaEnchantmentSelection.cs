using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.CardSelection;
namespace RinArcherCore;
[HarmonyPatch(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckForEnchantment),[typeof(Player),typeof(EnchantmentModel),typeof(int),typeof(Func<CardModel,bool>),typeof(CardSelectorPrefs)])]
public static class VanillaEnchantmentSelection
{
    [HarmonyPriority(Priority.First+200)]
    static bool Prefix(Player player,EnchantmentModel enchantment,int amount,Func<CardModel?,bool>? additionalFilter,CardSelectorPrefs prefs,ref Task<IEnumerable<CardModel>> __result)
    {
        if(!GenericCompatibility.Enabled(player)||CompatibilityExecution.Current is not {} f||!f.Rows.Any(r=>r.Scope=="DUAL_DECK_SELECTOR"))return true;
        var cards=DualDeckCardSelector.LegalPermanentUnion(player,c=>enchantment.CanEnchant(c)&&(additionalFilter?.Invoke(c)??true));
        __result=CardSelectCmd.FromDeckForEnchantment(cards,enchantment,amount,prefs);return false;
    }
}
[HarmonyPatch]
public static class VanillaEnchantmentBankValidation
{
    static IEnumerable<MethodBase> TargetMethods()
    {
        yield return AccessTools.Method(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckForEnchantment),[typeof(IReadOnlyList<CardModel>),typeof(EnchantmentModel),typeof(int),typeof(CardSelectorPrefs)])
            .GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.Instance|BindingFlags.NonPublic)!;
        // The native Any validation lives in a compiler-generated predicate, not MoveNext.
        foreach(var t in typeof(CardSelectCmd).GetNestedTypes(BindingFlags.Public|BindingFlags.NonPublic).Where(t=>!t.ContainsGenericParameters))
            foreach(var m in t.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly).Where(m=>!m.ContainsGenericParameters&&m.Name.Contains("FromDeckForEnchantment")&&m.GetMethodBody()!=null))
                if(PatchProcessor.GetOriginalInstructions(m).Any(i=>i.Calls(AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Type)))))yield return m;
    }
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var type=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Type));var cards=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Cards));
        foreach(var i in instructions)
        {
            if(i.Calls(type)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(ContractMerchant),nameof(ContractMerchant.NativeRemovalPileType));}
            else if(i.Calls(cards)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(GenericRandomPermanentUnion),nameof(GenericRandomPermanentUnion.Cards));}
            yield return i;
        }
    }
}
