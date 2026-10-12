using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Models.Relics;
using MegaCrit.Sts2.Core.Rooms;
using System.Reflection;
namespace RinArcherCore;
public static class VanillaRelicRecipientAnchor
{
    sealed record Recipient(CombatState Combat,Creature Creature);
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<AbstractModel,Recipient> Targets=new();
    public static Creature Resolve(AbstractModel model,ContractRuntime d)
    {
        if(Targets.TryGetValue(model,out var r)&&ReferenceEquals(r.Combat,d.Combat))return r.Creature;
        Targets.Remove(model);Targets.Add(model,new(d.Combat,d.Active.Creature));return d.Active.Creature;
    }
}

[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeSideTurnStart))]
public static class VanillaMemberBlockLifecycle
{
    [ThreadStatic] static bool invoking;
    static bool Prefix(ICombatState combatState,CombatSide side,MethodBase __originalMethod,object[] __args,ref Task __result)
    {
        if(invoking||side!=CombatSide.Player||!combatState.Players.Any(GenericCompatibility.Enabled))return true;
        __result=Run(combatState,__originalMethod,__args);return false;
    }
    static async Task Run(ICombatState combat,MethodBase method,object[] args)
    {
        foreach(var d in combat.Players.Where(GenericCompatibility.Enabled).Select(ContractRuntime.For).OfType<ContractRuntime>().Where(d=>!d.Finished&&d.Turn>1))
        {
            string key="BLOCK_CLEAR:"+d.Turn;
            if(d.CombatFlags.GetValueOrDefault(key))continue;
            d.CombatFlags[key]=true;
            foreach(var member in new[]{d.Rin,d.Archer})await (Task)AccessTools.Method(typeof(Creature),"ClearBlock").Invoke(member.Creature,null)!;
        }
        Task task;invoking=true;try{task=(Task)method.Invoke(null,args)!;}finally{invoking=false;}
        await task;
    }
}
[HarmonyPatch(typeof(EternalFeather),nameof(RelicModel.AfterRoomEntered))]
public static class VanillaFeatherDeckAndMember
{
    static bool Prefix(EternalFeather __instance,AbstractRoom room,ref Task __result)
    {if(!GenericCompatibility.Enabled(__instance.Owner))return true;__result=Heal(__instance,room);return false;}
    static async Task Heal(EternalFeather relic,AbstractRoom room)
    {
        if(room is not RestSiteRoom)return;
        var p=relic.Owner;if(!GenericMemberEffects.IsPrepared(relic)&&!await GenericMemberEffects.Prepare(p,relic,"AfterRoomEntered",false))return;
        string member=ContractSave.Get(p).Compatibility.MemberBindings[relic.Id+"/AfterRoomEntered"];
        int count=ContractSave.Deck(p,member).Cards.Count/relic.DynamicVars.Cards.IntValue;
        relic.Flash();await CreatureCmd.Heal(MemberTargetResolver.Creature(p,member),relic.DynamicVars.Heal.BaseValue*count);
        MemberTargetResolver.Synchronize(p);
    }
}
[HarmonyPatch(typeof(RunEconomy),"PreviewOne")]
public static class VanillaRestFocusScope
{
    internal static readonly AsyncLocal<Creature?> Focus=new();
    static void Prefix(Creature c,bool focus,out Creature? __state){__state=Focus.Value;Focus.Value=focus?c:null;}
    static void Postfix(Creature? __state)=>Focus.Value=__state;
    static Exception? Finalizer(Exception? __exception,Creature? __state){Focus.Value=__state;return __exception;}
}
[HarmonyPatch(typeof(RegalPillow),nameof(RelicModel.ModifyRestSiteHealAmount))]
public static class VanillaPillowSingleBudget
{
    static bool Prefix(RegalPillow __instance,Creature creature,decimal amount,ref decimal __result)
    {if(!GenericCompatibility.Enabled(__instance.Owner))return true;__result=amount+(VanillaRestFocusScope.Focus.Value==creature?__instance.DynamicVars.Heal.BaseValue:0);return false;}
}
