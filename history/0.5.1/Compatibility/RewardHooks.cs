using MegaCrit.Sts2.Core.Hooks;
namespace RinArcherCore;
[HarmonyPatch(typeof(CardModel),nameof(CardModel.OnPlayWrapper))]
public static class AlphaResolvedHook
{
    static void Postfix(CardModel __instance,ref Task __result){if(__instance is StarterCard c&&ContractRuntime.For(c.Owner) is {} d)__result=After(__result,d,c);}
    static async Task After(Task original,ContractRuntime d,StarterCard c){await original;d.CompleteAlphaPlay(c);}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeTurnEnd))]
public static class AlphaEndTurnHook
{
    static void Prefix(ICombatState combatState,CombatSide side){if(side==CombatSide.Player)foreach(var d in combatState.Players.Select(ContractRuntime.For).OfType<ContractRuntime>())d.EndAlphaTurn();}
}
