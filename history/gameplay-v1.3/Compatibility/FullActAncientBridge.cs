using System.Reflection;
using MegaCrit.Sts2.Core.Events;
using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Models.Acts;
using MegaCrit.Sts2.Core.Unlocks;
namespace RinArcherCore;

public static class FullActAncientBridge
{
    internal static readonly AsyncLocal<Player?> Generating=new();
    public static bool Supported(string id)=>id is "EVENT.NEOW" or "EVENT.TEZCATARA";
    public static bool Allowed(Player p,RelicModel relic)=>RelicEligibilityResolver.IsEligible(p,relic.Id.ToString(),"E2B_NATIVE_ANCIENT_OPTION",true);
    public static bool Budget(Player p,AncientEventModel ancient)
    {
        if(!Supported(ancient.Id.ToString())||!GenericCompatibility.Registry.IsValid)return false;
        IEnumerable<EventOption> Pool(string name)=>(IEnumerable<EventOption>)AccessTools.Property(ancient.GetType(),name).GetValue(ancient)!;
        bool Ready(EventOption o)=>o.Relic is {} r&&Allowed(p,r);
        return ancient is Neow?Pool("CurseOptions").Count(Ready)>=1&&Pool("PositiveOptions").Count(Ready)>=2:
            new[]{"OptionPool1","OptionPool2","OptionPool3"}.All(n=>Pool(n).Any(Ready));
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.GenerateRooms))]
public static class FullActAncientGenerationContext
{
    static void Prefix(RunManager __instance,out Player? __state){__state=FullActAncientBridge.Generating.Value;FullActAncientBridge.Generating.Value=__instance.DebugOnlyGetState()?.Players.FirstOrDefault(FullActRoomSpine.Enabled);}
    static void Postfix(Player? __state)=>FullActAncientBridge.Generating.Value=__state;
    static Exception? Finalizer(Exception? __exception,Player? __state){FullActAncientBridge.Generating.Value=__state;return __exception;}
}
[HarmonyPatch]
public static class FullActNativeAncientCandidates
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(Overgrowth),nameof(ActModel.GetUnlockedAncients)),AccessTools.Method(typeof(Underdocks),nameof(ActModel.GetUnlockedAncients)),AccessTools.Method(typeof(Hive),nameof(ActModel.GetUnlockedAncients))};
    static void Postfix(ref IEnumerable<AncientEventModel> __result)
    {
        if(FullActAncientBridge.Generating.Value is not {} p)return;
        var native=__result.ToArray();__result=native.Where(a=>FullActAncientBridge.Budget(p,a)).ToArray();
        if(native.Length>0&&!__result.Any())throw new CompatibilitySourceUnavailableException("E2B_NATIVE_ANCIENT_BUDGET_UNAVAILABLE_BEFORE_RNG");
    }
}
[HarmonyPatch(typeof(ActModel),nameof(ActModel.SetSharedAncientSubset))]
public static class FullActNativeSharedAncientCandidates
{
    static void Prefix(ActModel __instance,ref List<AncientEventModel> sharedAncientSubset)
    {if(__instance is Hive&&FullActAncientBridge.Generating.Value is {} p)sharedAncientSubset=sharedAncientSubset.Where(a=>FullActAncientBridge.Budget(p,a)).ToList();}
}
[HarmonyPatch]
public static class FullActNativeAncientOptionPools
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.PropertyGetter(typeof(Tezcatara),"OptionPool1"),AccessTools.PropertyGetter(typeof(Tezcatara),"OptionPool2"),AccessTools.PropertyGetter(typeof(Tezcatara),"OptionPool3")};
    static void Postfix(Tezcatara __instance,ref List<EventOption> __result)
    {var p=__instance.IsMutable?__instance.Owner:FullActAncientBridge.Generating.Value;if(p!=null&&FullActRoomSpine.Enabled(p))__result=__result.Where(o=>o.Relic is {} r&&FullActAncientBridge.Allowed(p,r)).ToList();}
}
[HarmonyPatch(typeof(RelicModel),nameof(RelicModel.IsAllowedAtNeow))]
public static class FullActNativeNeowOptionEligibility
{
    static void Postfix(RelicModel __instance,Player player,ref bool __result)
    {if(FullActRoomSpine.Enabled(player))__result=__result&&FullActAncientBridge.Allowed(player,__instance);}
}
[HarmonyPatch(typeof(RunManager),"InitializeNewRun")]
public static class FullActIndependentRunInitialization
{
    public static bool Requested()=>OS.GetUserDataDir().Contains("RinArcherE2BResolution-20261009")&&
        !E2ARun.Creating&&!D1Run.Creating&&!D2Run.Creating&&!PublicUiMode.CreatingDebugRun&&
        (OS.GetCmdlineArgs().Any(a=>a is "--resolution-full" or "--resolution-manual")||OS.GetUserDataDir().Replace('\\','/').Contains("/manual/"));
    [HarmonyPriority(Priority.First)]
    static void Postfix(RunManager __instance)
    {
        if(MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn||!Requested())return;
        foreach(var p in __instance.DebugOnlyGetState()!.Players.Where(p=>p.Character is RinContractCharacter))
        {ContractSave.EnsureDecks(p);FullActRoomSpine.EnableDevelopment(p);ContractSave.Get(p).RunFlags[PublicUiMode.Flag]=true;ContractSave.Sync(p);}
    }
}
