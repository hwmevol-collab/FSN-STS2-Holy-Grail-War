using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Rewards;
using MegaCrit.Sts2.Core.Nodes.Screens.Overlays;
namespace RinArcherCore;
// Native reward buttons remain responsible for claiming/removing their items.
// Finish their async callbacks before native menu teardown frees the container.
public static class NativeRewardTransactions
{
    static readonly HashSet<Task> Active=[];
    public static void Track(Task task){Active.RemoveWhere(t=>t.IsCompleted);Active.Add(task);}
    public static bool Pending=>Active.Any(t=>!t.IsCompleted);
    public static async Task PrepareForExit()
    {
        var game=NGame.Instance!;
        while(DualRewardUi.Committing&&Pending)await game.ToSignal(game.GetTree(),SceneTree.SignalName.ProcessFrame);
        if(DualRewardUi.NativeScreen is {} screen&&GodotObject.IsInstanceValid(screen)&&screen.IsInsideTree())
            NOverlayStack.Instance!.Remove(screen);
        if(DualDeckCardSelector.Current is {} selector&&GodotObject.IsInstanceValid(selector)&&selector.IsInsideTree())NOverlayStack.Instance!.Remove(selector);
        FocusedRestUi.Cancel();
        await Task.WhenAll(Active.ToArray());
        Active.Clear();
    }
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Nodes.RestSite.NRestSiteButton),"SelectOption")]
public static class D2TrackNativeCampfireSelection
{static void Postfix(MegaCrit.Sts2.Core.Entities.RestSite.RestSiteOption option,Task __result){if(RunEconomy.Enabled(RunEconomy.Owner(option)))NativeRewardTransactions.Track(__result);}}
[HarmonyPatch(typeof(NRewardButton),"GetReward")]
public static class TrackContractNativeRewardButton
{
    static void Postfix(NRewardButton __instance,Task __result)
    {if(__instance.Reward?.Player.Character is RinContractCharacter)NativeRewardTransactions.Track(__result);}
}
[HarmonyPatch(typeof(NGame),nameof(NGame.ReturnToMainMenu))]
public static class FinishContractRewardBeforeNativeMenu
{
    static bool preparing;
    static bool Prefix(NGame __instance,ref Task __result)
    {
        if(preparing||DualRewardUi.NativeScreen==null&&!NativeRewardTransactions.Pending)return true;
        __result=Finish(__instance);return false;
    }
    static async Task Finish(NGame game)
    {
        preparing=true;
        try{await NativeRewardTransactions.PrepareForExit();await game.ReturnToMainMenu();}
        finally{preparing=false;}
    }
}
