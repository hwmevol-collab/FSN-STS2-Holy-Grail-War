using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Entities.RestSite;
using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
namespace RinArcherCore;
[HarmonyPatch(typeof(RunManager),nameof(RunManager.GenerateMap))]
public static class D2MapHook
{
    static void Postfix(RunManager __instance,ref Task __result){if(D2Run.IsQa(__instance.DebugOnlyGetState()))__result=After(__result,__instance);}
    static async Task After(Task original,RunManager manager){await original;var run=manager.DebugOnlyGetState()!;if(run.Map is not MegaCrit.Sts2.Core.Map.SavedActMap)run.Map=new D2ActMap(run.Map!.GetRowCount());NMapScreen.Instance?.SetMap(run.Map,run.Rng.Seed,true);NMapScreen.Instance?.SetTravelEnabled(true);}
}
[HarmonyPatch(typeof(RunManager),"CreateRoom")]
public static class D2RoomHook
{
    static bool Prefix(RunManager __instance,RoomType roomType,ref AbstractRoom __result)
    {var run=__instance.DebugOnlyGetState();if(!D2Run.IsQa(run)||roomType!=RoomType.Monster)return true;__result=new CombatRoom(ModelDb.Encounter<QaD1Normal>().ToMutable(),run);return false;}
}
[HarmonyPatch(typeof(RestSiteOption),nameof(RestSiteOption.Generate))]
public static class D2RestOptions
{
    static bool Prefix(Player player,ref List<RestSiteOption> __result)
    {if(!RunEconomy.Enabled(player))return true;__result=RunEconomy.Campfire(player).Completed?[]:[new HealRestSiteOption(player),new SmithRestSiteOption(player)];return false;}
}
[HarmonyPatch(typeof(RestSiteOption),"get_IsEnabled")]
public static class D2RestEnabled
{
    static void Postfix(RestSiteOption __instance,ref bool __result)
    {var p=RunEconomy.Owner(__instance);if(__instance is HealRestSiteOption&&RunEconomy.Enabled(p))__result=RunEconomy.CanFocus(p,RunEconomy.Rin)||RunEconomy.CanFocus(p,RunEconomy.Archer);}
}
[HarmonyPatch(typeof(SmithRestSiteOption),"get_IsEnabled")]
public static class D2SmithEnabled
{
    static void Postfix(SmithRestSiteOption __instance,ref bool __result)
    {var p=RunEconomy.Owner(__instance);if(RunEconomy.Enabled(p))__result=!RunEconomy.Campfire(p).Completed&&RunEconomy.Permanent(p).Any(c=>c.IsUpgradable);}
}
[HarmonyPatch(typeof(HealRestSiteOption),"get_Description")]
public static class D2RestDescription
{
    static void Postfix(HealRestSiteOption __instance,ref LocString __result)
    {var p=RunEconomy.Owner(__instance);if(RunEconomy.Enabled(p))__result=EconomyNativeUi.Text(FsnLoc.Text("UI_CE896109AF07"));}
}
[HarmonyPatch(typeof(HealRestSiteOption),nameof(HealRestSiteOption.OnSelect))]
public static class D2RestAction
{
    static bool Prefix(HealRestSiteOption __instance,ref Task<bool> __result){var p=RunEconomy.Owner(__instance);if(!RunEconomy.Enabled(p))return true;__result=FocusedRestUi.Select(p);return false;}
}
[HarmonyPatch(typeof(SmithRestSiteOption),nameof(SmithRestSiteOption.OnSelect))]
public static class D2SmithAction
{
    static bool Prefix(SmithRestSiteOption __instance,ref Task<bool> __result){var p=RunEconomy.Owner(__instance);if(!RunEconomy.Enabled(p))return true;__result=Select(__instance,p);return false;}
    static async Task<bool> Select(SmithRestSiteOption option,Player p)
    {ContractSave.Log(p,"SMITH_SELECTOR_OPENED",new{targetCount=1});var cards=await DualDeckCardSelector.Select(p,DeckServiceAction.Upgrade,1,c=>c.IsUpgradable,true,FsnLoc.Text("UI_1DA320E241D7"));if(cards.Count==0)return false;var card=cards[0];ContractSave.Log(p,"SMITH_OPENED",new{owner=NativePermanentCards.Owner(card),cardId=NativePermanentCards.Id(card),instanceId=NativePermanentCards.Instance(card),upgradeBefore=card.CurrentUpgradeLevel,upgradeAfter=card.CurrentUpgradeLevel+1});AccessTools.Field(typeof(SmithRestSiteOption),"_selection").SetValue(option,cards);var commit=RunEconomy.Smith(p,cards[0]);NativeRewardTransactions.Track(commit);return await commit;}
}
[HarmonyPatch(typeof(RestSiteRoom),nameof(RestSiteRoom.EnterInternal))]
public static class D2CampfireEnter
{
    static void Postfix(RestSiteRoom __instance,ref Task __result)=>__result=After(__result);
    static async Task After(Task original)
    {await original;var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(RunEconomy.Enabled);if(p==null)return;var c=RunEconomy.Campfire(p);if(!c.Entered){c.Entered=true;ContractSave.Get(p).Economy.CampfiresVisited++;ContractSave.Log(p,"CAMPFIRE_ENTERED",new{roomIdentity=c.RoomIdentity});await ContractSave.Checkpoint(p,"CAMPFIRE_ENTERED");}if(!c.Completed&&!new HealRestSiteOption(p).IsEnabled&&!new SmithRestSiteOption(p).IsEnabled)AccessTools.Method(typeof(NRestSiteRoom),"ShowProceedButton").Invoke(NRestSiteRoom.Instance,null);}
}
// Native Heal's combat-ending guard assumes every friendly persistent body is a Player.
// Widen only that guard for the registered out-of-combat Archer service body.
[HarmonyPatch]
public static class D2ServiceHealGuard
{
    static MethodBase TargetMethod()=>AccessTools.Method(typeof(CreatureCmd),nameof(CreatureCmd.Heal)).GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.NonPublic|BindingFlags.Instance)!;
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {var list=instructions.ToList();var getter=AccessTools.PropertyGetter(typeof(Creature),nameof(Creature.IsPlayer));var index=list.FindIndex(c=>c.Calls(getter));if(index<0)throw new InvalidOperationException("Native Heal ending guard changed");list[index].opcode=OpCodes.Call;list[index].operand=AccessTools.Method(typeof(RunEconomy),nameof(RunEconomy.HealEndingGuard));return list;}
}

