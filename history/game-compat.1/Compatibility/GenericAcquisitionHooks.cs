using System.Reflection;
using MegaCrit.Sts2.Core.Entities.Potions;
using MegaCrit.Sts2.Core.Entities.Relics;
using MegaCrit.Sts2.Core.Factories;
namespace RinArcherCore;

public sealed class CompatibilitySourceUnavailableException(string message):InvalidOperationException(message);

[HarmonyPatch]
public static class GenericPotionSourceBeforeUsePresentation
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(ModelDb).Assembly.GetTypes().Where(t=>!t.IsAbstract&&typeof(PotionModel).IsAssignableFrom(t))
        .Select(t=>AccessTools.PropertyGetter(t,nameof(PotionModel.PassesCustomUsabilityCheck))).Distinct();
    static void Postfix(PotionModel __instance,ref bool __result)
    {
        if(!__instance.IsMutable||!GenericCompatibility.Enabled(__instance.Owner))return;
        __result=__result&&PotionEligibilityResolver.IsEligible(__instance.Owner,__instance.Id.ToString(),"NATIVE_POTION_USE_PRESENTATION",true);
    }
}

[HarmonyPatch]
public static class GenericPotionFactoryContext
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(PotionFactory).GetMethods(BindingFlags.Public|BindingFlags.Static)
        .Where(m=>m.Name.StartsWith("CreateRandomPotion",StringComparison.Ordinal));
    static void Prefix(Player player,out IDisposable? __state)
    {
        __state=GenericCompatibility.Enabled(player)
            ?CompatibilityExecution.Bind(new(player,"NATIVE_POTION_FACTORY","Generate",[],null,null)):null;
    }
    static void Postfix(IDisposable? __state)=>__state?.Dispose();
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}

[HarmonyPatch(typeof(PotionFactory),nameof(PotionFactory.GetPotionOptions))]
public static class GenericNativePotionCandidates
{
    static void Postfix(Player player,ref IEnumerable<PotionModel> __result)
    {
        if(!GenericCompatibility.Enabled(player))return;
        __result=PotionEligibilityResolver.Prepare(player,"NATIVE_POTION_FACTORY",__result,0).Candidates;
    }
}
#if GAME_0107
[HarmonyPatch(typeof(PotionFactory),"CreateRandomPotion")]
#else
[HarmonyPatch(typeof(PotionFactory),"CreateRandomPotions")]
#endif
public static class GenericNativePotionWholeBudget
{
    static void Prefix(IEnumerable<PotionModel> options,int count)
    {
        var frame=CompatibilityExecution.Current;
        // The native factory has no Player argument. The caller's already-filtered
        // options are validated when a generic source frame is present.
        if(frame==null||!GenericCompatibility.Enabled(frame.Player))return;
        var values=options.ToArray();
        foreach(var rarity in new[]{PotionRarity.Common,PotionRarity.Uncommon,PotionRarity.Rare})
            if(values.Where(p=>p.Rarity==rarity).Distinct().Count()<count)
                throw new CompatibilitySourceUnavailableException("Native distinct potion batch budget unavailable before RNG: "+rarity);
    }
}
[HarmonyPatch]
public static class GenericNativeRelicCandidates
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(RelicGrabBag).GetMethods(BindingFlags.Public|BindingFlags.Instance).Where(m=>m.Name is "PullFromFront" or "PullFromBack"&&m.GetParameters().Length==3);
    static void Prefix(RelicGrabBag __instance,RelicRarity rarity,IRunState runState,ref Func<RelicModel,bool> filter)
    {
        var p=runState.Players.FirstOrDefault(p=>GenericCompatibility.Enabled(p)&&ReferenceEquals(p.RelicGrabBag,__instance));
        if(p==null&&ReferenceEquals(runState.SharedRelicGrabBag,__instance)&&runState.Players.All(p=>p.Character is RinContractCharacter))p=runState.Players.FirstOrDefault(GenericCompatibility.Enabled);
        if(p==null)return;
        var native=filter;var context=CompatibilityCandidateResolver.Context(p,"NATIVE_RELIC_GRAB_BAG");
        var original=NativeSourceBudgetResolver.NativeRelicBranch(__instance,rarity,runState,native).ToArray();
        if(original.Length>0&&!original.Any(r=>GenericCompatibility.Registry.IsRelicEligible(r.Id.ToString(),context)))
            throw new CompatibilitySourceUnavailableException("Native rarity budget has no compatible candidate before presentation: "+rarity);
        filter=r=>native(r)&&GenericCompatibility.Registry.IsRelicEligible(r.Id.ToString(),context);
    }
}
[HarmonyPatch]
public static class GenericNativeEventCandidates
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(ModelDb).Assembly.GetTypes().Where(t=>!t.IsAbstract&&typeof(EventModel).IsAssignableFrom(t))
        .Select(t=>AccessTools.Method(t,nameof(EventModel.IsAllowed))).Distinct();
    static void Postfix(EventModel __instance,IRunState runState,ref bool __result)
    {
        var p=runState.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p==null)return;
        __result=EventEligibilityResolver.IsEligible(p,__instance.Id.ToString(),"NATIVE_EVENT_CANDIDATE",__result);
    }
}
[HarmonyPatch(typeof(PotionCmd),nameof(PotionCmd.TryToProcure),[typeof(PotionModel),typeof(Player),typeof(int)])]
public static class GenericPotionAcquisitionBackstop
{
    static void Prefix(PotionModel potion,Player player)
    {
        if(GenericCompatibility.Enabled(player)&&!PotionEligibilityResolver.IsEligible(player,potion.Id.ToString(),"NATIVE_PROCURE",true))
            throw new CompatibilitySourceUnavailableException("Unprepared potion acquisition source: "+GenericCompatibility.Registry.RejectionReason(potion.Id.ToString(),CompatibilityCandidateResolver.Context(player,"NATIVE_PROCURE"),"potions"));
    }
    static void Postfix(Player player,PotionModel potion,ref Task<PotionProcureResult> __result)
    {if(GenericCompatibility.Enabled(player))__result=After(__result,player,potion);}
    static async Task<PotionProcureResult> After(Task<PotionProcureResult> original,Player p,PotionModel potion)
    {var result=await original;if(result.success)ContractSave.Log(p,"COMPAT_CONTENT_ACQUIRED",new{contentId=potion.Id.ToString(),source="NATIVE_POTION_PROCURE"});return result;}
}
[HarmonyPatch(typeof(RelicCmd),nameof(RelicCmd.Obtain),[typeof(RelicModel),typeof(Player),typeof(int)])]
public static class GenericRelicAcquisitionBackstop
{
    [HarmonyPriority(Priority.First)]
    static void Prefix(RelicModel relic,Player player)
    {
        if(GenericCompatibility.Enabled(player)&&!RelicEligibilityResolver.IsEligible(player,relic.Id.ToString(),"NATIVE_OBTAIN",true))
            throw new CompatibilitySourceUnavailableException("Unprepared relic acquisition source: "+GenericCompatibility.Registry.RejectionReason(relic.Id.ToString(),CompatibilityCandidateResolver.Context(player,"NATIVE_OBTAIN"),"relics"));
    }
}
