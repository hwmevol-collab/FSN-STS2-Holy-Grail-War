using MegaCrit.Sts2.Core.Hooks;
namespace RinArcherCore;
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforePowerAmountChanged))]
public static class ExpansionPowerBefore
{
    static void Prefix(PowerModel power,Creature target)=>ExpansionPowerAfter.Mark(power,target.Powers.Any(p=>p.GetType()==power.GetType()&&p.Amount>0));
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterPowerAmountChanged))]
public static class ExpansionPowerAfter
{
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<PowerModel,Presence> before=new();
    sealed class Presence{public bool Present;}
    internal static void Mark(PowerModel power,bool present)=>before.GetOrCreateValue(power).Present=present;
    static void Postfix(ICombatState combatState,PlayerChoiceContext choiceContext,PowerModel power,decimal amount,Creature? applier,ref Task __result)
    {
        var d=combatState.Players.Select(ContractRuntime.For).OfType<ContractRuntime>().FirstOrDefault();if(d==null)return;
        bool fresh=before.TryGetValue(power,out var previous)&&!previous.Present;Mark(power,true);
        __result=After(__result,d,choiceContext,power,amount,applier,fresh);
    }
    static async Task After(Task task,ContractRuntime d,PlayerChoiceContext ctx,PowerModel power,decimal amount,Creature? applier,bool fresh){await task;await d.ObservePowerChange(ctx,power,amount,applier,fresh);}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterBlockGained))]
public static class ExpansionOwnBlock
{
    static void Postfix(ICombatState combatState,Creature creature,decimal amount,CardModel? cardSource,ref Task __result)
    {if(ContractRuntime.For(creature) is {} d)__result=After(__result,d,creature,amount,cardSource);}
    static async Task After(Task task,ContractRuntime d,Creature target,decimal amount,CardModel? card){await task;await d.OwnBlockEvent(target,amount,card);}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterDamageGiven))]
public static class ExpansionHits
{
    static void Postfix(PlayerChoiceContext choiceContext,Creature? dealer,DamageResult results,ValueProp props,Creature target,ref Task __result)
    {if(dealer!=null&&ContractRuntime.For(dealer) is {} d)__result=After(__result,d,choiceContext,dealer,results,props,target);}
    static async Task After(Task task,ContractRuntime d,PlayerChoiceContext ctx,Creature dealer,DamageResult hit,ValueProp props,Creature target){await task;await d.ActualArcherHit(ctx,dealer,hit,props,target);}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterDamageReceived))]
public static class ExpansionDefense
{
    static void Postfix(PlayerChoiceContext choiceContext,Creature target,DamageResult result,ValueProp props,Creature? dealer,ref Task __result)
    {if(ContractRuntime.For(target) is {} d)__result=After(__result,d,choiceContext,target,result,props,dealer);}
    static async Task After(Task task,ContractRuntime d,PlayerChoiceContext ctx,Creature target,DamageResult hit,ValueProp props,Creature? dealer){await task;await d.ActualArcherDefense(ctx,target,hit,props,dealer);}
}
// Clamp after native Strength/Weak/etc. Native damage/block history stores Int32 and Creature saturates at this boundary.
[HarmonyPatch(typeof(Hook),nameof(Hook.ModifyDamage))]
public static class ExpansionDamageBound
{
    static void Postfix(Creature? dealer,ref decimal __result){if(dealer!=null&&ContractRuntime.For(dealer) is {} d&&__result>ContractRuntime.NativeValueLimit)__result=d.Bound(new System.Numerics.BigInteger(__result));}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.ModifyBlock))]
public static class ExpansionBlockBound
{
    static void Postfix(Creature target,ref decimal __result){if(ContractRuntime.For(target) is {} d&&__result>ContractRuntime.NativeValueLimit)__result=d.Bound(new System.Numerics.BigInteger(__result));}
}
// Native run statistics accumulate actual HP lost with unchecked Int32 addition.
// Saturate the statistic at its storage boundary without changing any combat damage.
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Entities.Players.ExtraPlayerFields),"set_DamageDealt")]
public static class ExpansionDamageStatisticBound
{
    static void Prefix(MegaCrit.Sts2.Core.Entities.Players.ExtraPlayerFields __instance,ref int value)
    {
        if(value<0&&CombatManager.Instance.DebugOnlyGetState()?.Players.Any(p=>ReferenceEquals(p.ExtraFields,__instance)&&ContractRuntime.For(p)!=null)==true)value=int.MaxValue;
    }
}
