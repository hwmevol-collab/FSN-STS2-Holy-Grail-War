using System.Reflection;
namespace RinArcherCore;

[HarmonyPatch]
public static class GenericMemberTriggerHooks
{
    static bool Prepare()=>GenericCompatibility.Registry.IsValid;
    static IEnumerable<MethodBase> TargetMethods()=>GenericCompatibility.NativeMethods().OfType<MethodInfo>()
        .Where(m=>m.ReturnType==typeof(Task)&&m.Name is not ("AfterObtained" or "OnUse")&&
            GenericCompatibility.Registry.Entries.First(e=>e.ModelType==m.DeclaringType!.FullName).Effects.Any(e=>e.Trigger==m.Name&&e.Scope=="CHOOSE_MEMBER"));
    [HarmonyPriority(Priority.First)]
    static bool Prefix(AbstractModel __instance,MethodBase __originalMethod,object[] __args,ref Task __result)
    {
        var p=GenericCompatibility.Player(__instance);
        if(p==null||!GenericCompatibility.Enabled(p)||GenericMemberEffects.IsPrepared(__instance))return true;
        __result=Run(p,__instance,__originalMethod,__args);return false;
    }
    static async Task Run(Player p,AbstractModel model,MethodBase method,object[] args)
    {
        if(!NativeMemberConditionContext.AnyEligible(p,model,method.Name,args))
        {
            await NativeMemberConditionContext.RunWithoutPersonalEffect(model,method.Name,async()=>await GenericMemberEffects.InvokePrepared(model,async()=>{await (Task)method.Invoke(model,args)!;return true;}));return;
        }
        // Automatic native procs are mandatory. Manual acquisition/potion actions
        // can cancel before commitment; cancelling a proc must not stall counters.
        if(!await GenericMemberEffects.Prepare(p,model,method.Name,false,args))return;
        await GenericMemberEffects.InvokePrepared(model,async()=>{await (Task)method.Invoke(model,args)!;return true;});
        MemberTargetResolver.Synchronize(p);
    }
}
