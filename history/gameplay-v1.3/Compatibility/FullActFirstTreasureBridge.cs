using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Models.Relics;
using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;

// Exact fixed first-run dependency only. Gorget remains C and is never admitted
// to normal random rewards/shops/pools by this adapter.
public static class FullActFirstTreasureBridge
{
    public const string Id="RELIC.GORGET";
    public static bool Ready(Player p)=>FullActRoomSpine.Enabled(p)&&GenericCompatibility.Registry.IsValid
        &&p.RunState.UnlockState.NumberOfRuns==0
        &&(p.RunState.MapPointHistory.SelectMany(h=>h).Count(h=>h.HasRoomOfType(RoomType.Treasure))<=1
           ||ContractSave.Get(p).CompatibleTreasures.Any(t=>!t.Complete&&t.RoomIdentity==$"{p.RunState.CurrentActIndex}:{p.RunState.CurrentMapCoord}"&&t.RolledRelics.SequenceEqual(new[]{Id})));
    public static bool SourceAllowed(string source)=>source is "NATIVE_FIRST_TREASURE_FIXED_REWARD" or "TREASURE_ROLL" or "TREASURE_RESTORE" or "NATIVE_OBTAIN";
}

[HarmonyPatch(typeof(Gorget),nameof(Gorget.AfterRoomEntered))]
public static class FullActGorgetPersonalEffect
{
    static readonly Dictionary<Player,Gorget> Pending=[];
    static bool Prefix(Gorget __instance,AbstractRoom room,ref Task __result)
    {
        if(!FullActRoomSpine.Enabled(__instance.Owner)||room is not CombatRoom)return true;
        Pending[__instance.Owner]=__instance;__result=Task.CompletedTask;return false;
    }
    internal static async Task ApplyPending(CombatState combat)
    {
        foreach(var p in combat.Players)
        {
            if(!Pending.Remove(p,out var relic))continue;
            var d=ContractRuntime.For(p)??throw new InvalidOperationException("Gorget requires initialized Contract");
            var target=d.Active.Creature; // Combat-start personal effects use selected Starting Active.
            relic.Flash();await PowerCmd.Apply<PlatingPower>(new MegaCrit.Sts2.Core.GameActions.Multiplayer.ThrowingPlayerChoiceContext(),target,relic.DynamicVars["PlatingPower"].BaseValue,target,null);
            d.Log("GORGET_FIXED_SOURCE_NATIVE_EFFECT",new{recipient=d.Active.CharacterId,amount=relic.DynamicVars["PlatingPower"].BaseValue});
        }
    }
}
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeCombatStart))]
public static class FullActGorgetStartingActive
{
    static void Postfix(CombatState combatState,ref Task __result)=>__result=After(__result,combatState);
    static async Task After(Task original,CombatState combat){await original;await FullActGorgetPersonalEffect.ApplyPending(combat);}
}

// Reserve is a real Contract player body. Keep the native player's first-turn
// exceptions without rewriting Creature.Player / IsPlayer globally.
[HarmonyPatch(typeof(PlatingPower),nameof(PlatingPower.BeforeSideTurnStart))]
public static class FullActGorgetInitialPlating
{
    static bool Prefix(PlatingPower __instance,ref Task __result)
    {if(ContractRuntime.For(__instance.Owner) is not {} d||!FullActRoomSpine.Enabled(d.Player))return true;__result=Task.CompletedTask;return false;}
}
[HarmonyPatch(typeof(PlatingPower),nameof(PlatingPower.AfterSideTurnStart))]
public static class FullActGorgetFirstTurnPlating
{
    static bool Prefix(PlatingPower __instance,ref Task __result)
    {if(ContractRuntime.For(__instance.Owner) is not {} d||!FullActRoomSpine.Enabled(d.Player)||d.Player.PlayerCombatState!.TurnNumber!=1)return true;__result=Task.CompletedTask;return false;}
}
