using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
namespace RinArcherCore;
// The permanent Contract pool contains both members. Native rarity / multiplayer /
// in-combat / original-ID filters still run; only the original member supplies cards.
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Factories.CardFactory),nameof(MegaCrit.Sts2.Core.Factories.CardFactory.GetDefaultTransformationOptions))]
public static class VanillaTransformPool
{
    static bool Prefix(CardModel original,bool isInCombat,ref IEnumerable<CardModel> __result)
    {
        if(original is not StarterCard card||!GenericCompatibility.Enabled(original.Owner))return true;
        var options=AlphaRewardRegistry.Pool(card.OwnerCharacterId).Select(x=>AlphaRewardRegistry.Card(x.Id));
        __result=(IEnumerable<CardModel>)AccessTools.Method(typeof(MegaCrit.Sts2.Core.Factories.CardFactory),"GetFilteredTransformationOptions").Invoke(null,[original,options,isInCombat])!;
        return false;
    }
}
[HarmonyPatch]
public static class VanillaTransformSelection
{
    static MethodBase TargetMethod()=>AccessTools.Method(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckForTransformation))
        .GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.Instance|BindingFlags.NonPublic)!;
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Cards));
        foreach(var i in instructions){if(i.Calls(getter)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(GenericRandomPermanentUnion),nameof(GenericRandomPermanentUnion.Cards));}yield return i;}
    }
}
[HarmonyPatch(typeof(CardPile),"get_IsCombatPile")]
public static class VanillaPermanentBankLifetime
{
    static bool Prefix(CardPile __instance,ref bool __result)
    {if(CardBanks.ArcherDeck==null||__instance.Type!=CardBanks.ArcherDeck.PileType)return true;__result=false;return false;}
}
[HarmonyPatch(typeof(CardTransformation),nameof(CardTransformation.GetReplacement))]
public static class VanillaTransformOwner
{
    static void Postfix(CardTransformation __instance,CardModel? __result)
    {
        var original=__instance.Original;
        if(__result==null||original.Owner is not {} p||!GenericCompatibility.Enabled(p)||!RunEconomy.IsPermanent(p,original))return;
        string member=NativePermanentCards.Owner(original),instance=NativePermanentCards.Instance(original);
        if(__result is StarterCard s){if(s.OwnerCharacterId!=member)throw new InvalidOperationException("Transform changed member");s.InstanceId=instance;}
        else NativePermanentCards.Bind(__result,member,instance);
    }
}
[HarmonyPatch]
public static class VanillaTransformBankType
{
    static MethodBase TargetMethod()=>AccessTools.Method(typeof(CardCmd),nameof(CardCmd.Transform),[typeof(IEnumerable<CardTransformation>),typeof(MegaCrit.Sts2.Core.Random.Rng),typeof(MegaCrit.Sts2.Core.Nodes.CommonUi.CardPreviewStyle)])
        .GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.Instance|BindingFlags.NonPublic)!;
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Type));
        foreach(var i in instructions){if(i.Calls(getter)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(ContractMerchant),nameof(ContractMerchant.NativeRemovalPileType));}yield return i;}
    }
}
