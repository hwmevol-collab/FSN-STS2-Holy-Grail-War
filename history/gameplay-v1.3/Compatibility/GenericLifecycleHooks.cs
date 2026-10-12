using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeCombatStart))]
public static class GenericCombatStartOrder
{
    static readonly AsyncLocal<bool> Dispatching=new();
    static bool Prefix(IRunState runState,CombatState combatState,ref Task __result)
    {
        if(Dispatching.Value||!combatState.Players.Any(GenericCompatibility.Enabled))return true;
        __result=Start(runState,combatState);return false;
    }
    static async Task Start(IRunState run,CombatState combat)
    {
        foreach(var p in combat.Players.Where(GenericCompatibility.Enabled))
        {
            var d=await ContractRuntime.Initialize(p,combat,new ThrowingPlayerChoiceContext());
            string selected=TestMode.IsOn?RunEconomy.Archer:await StartingActiveChoiceUi.Choose(d);
            d.SelectStartingActive(selected);d.DeferActiveOpeningForNativeDraw();if(!TestMode.IsOn)CoreHud.Attach(d);
        }
        Dispatching.Value=true;
        try{await Hook.BeforeCombatStart(run,combat);}
        finally{Dispatching.Value=false;}
    }
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.Draw),[typeof(PlayerChoiceContext),typeof(decimal),typeof(Player),typeof(bool)])]
public static class GenericActiveDrawGuard
{
    static void Prefix(Player player)
    {
        if(CompatibilityExecution.Current is {ActiveSnapshot:{} active} frame&&frame.Player==player&&frame.Rows.Any(r=>r.Scope=="ACTIVE_HAND")&&active.Contract.Active.CharacterId!=active.Member)
            throw new InvalidOperationException("ACTIVE_HAND_TRIGGER_BINDING_CHANGED");
    }
}
