using System.Reflection;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;

// Room-entry personal procs run before the starting-member choice in native STS2.
public static class VanillaCombatEntry
{
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<CombatState,List<(AbstractModel Model,MethodBase Method,object[] Args)>> Pending=new();
    [ThreadStatic] internal static bool Replaying;
    public static bool Deferred(AbstractModel model,MethodBase method,object[] args)
    {
        var p=GenericCompatibility.Player(model);
        if(p==null||!GenericCompatibility.Enabled(p)||method.Name!="AfterRoomEntered"||args.FirstOrDefault() is not CombatRoom room||room.IsPreFinished)return false;
        if(!GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()).Any(r=>r.Trigger==method.Name&&r.Scope is "ACTIVE_AT_TRIGGER" or "ACTIVE_HAND"))return false;
        if(ContractRuntime.For(p) is {StartingSelected:true,Finished:false} d&&ReferenceEquals(d.Combat,room.CombatState))
        {
            string key="NATIVE_ENTRY:"+model.Id;
            if(d.CombatFlags.GetValueOrDefault(key))return true;
            d.CombatFlags[key]=true;return false;
        }
        if(Replaying)throw new InvalidOperationException("Room-entry replay requires the selected combat");
        var list=Pending.GetOrCreateValue(room.CombatState);
        if(!list.Any(x=>ReferenceEquals(x.Model,model)&&x.Method==method))list.Add((model,method,args));
        return true;
    }
    public static async Task Replay(ContractRuntime d)
    {
        if(!Pending.TryGetValue(d.Combat,out var list))return;
        Pending.Remove(d.Combat);
        foreach(var item in list)
        {
            Task task;Replaying=true;try{task=(Task)item.Method.Invoke(item.Model,item.Args)!;}finally{Replaying=false;}
            await task;
        }
    }
}
[HarmonyPatch]
public static class VanillaCombatEntryDeferral
{
    static IEnumerable<MethodBase> TargetMethods()=>GenericCompatibility.NativeMethods().Where(m=>m.Name=="AfterRoomEntered");
    [HarmonyPriority(Priority.First)]
    static bool Prefix(AbstractModel __instance,MethodBase __originalMethod,object[] __args,ref Task __result)
    {if(!VanillaCombatEntry.Deferred(__instance,__originalMethod,__args))return true;__result=Task.CompletedTask;return false;}
}
