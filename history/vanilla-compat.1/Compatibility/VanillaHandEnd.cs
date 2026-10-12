using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
namespace RinArcherCore;

// A bank is frozen; the native wrapper moves an eligible front-hand card to Play.
[HarmonyPatch(typeof(CardModel),nameof(CardModel.OnTurnEndInHandWrapper))]
public static class VanillaHandEnd
{
    [ThreadStatic] static bool invoking;
    static bool Prefix(CardModel __instance,PlayerChoiceContext choiceContext,MethodBase __originalMethod,ref Task __result)
    {
        if(invoking||ContractRuntime.For(__instance.Owner) is not {Finished:false} d)return true;
        var owner=CardOwnerEffectResolver.Resolve(d,__instance,"TURN_END_IN_HAND");
        if(owner!=d.Active||!owner.Hand.Cards.Contains(__instance)){__result=Task.CompletedTask;return false;}
        __result=End(__instance,owner,d,choiceContext,__originalMethod);return false;
    }
    static async Task End(CardModel card,CharacterRuntime owner,ContractRuntime d,PlayerChoiceContext ctx,MethodBase method)
    {
        using var binding=CompatibilityExecution.Bind(new(d.Player,card.Id.ToString(),"OnTurnEndInHand",[],owner.Creature,null));
        Task task;invoking=true;try{task=(Task)method.Invoke(card,[ctx])!;}finally{invoking=false;}
        await task;
    }
}
[HarmonyPatch]
public static class VanillaHandEndIdentity
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(ModelDb).Assembly.GetTypes().Where(t=>!t.IsAbstract&&typeof(CardModel).IsAssignableFrom(t))
        .SelectMany(t=>t.GetMethods(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.Public|BindingFlags.DeclaredOnly))
        .Where(m=>m.Name=="OnTurnEndInHand")
        .Select(m=>m.GetCustomAttribute<AsyncStateMachineAttribute>() is {} state?AccessTools.Method(state.StateMachineType,"MoveNext"):m);
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature));
        foreach(var i in instructions){if(i.Calls(getter)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(GenericScopedIdentity),nameof(GenericScopedIdentity.PersonalCreature));}yield return i;}
    }
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Models.Cards.Regret),nameof(CardModel.BeforeSideTurnEnd))]
public static class VanillaRegretFrozenHand
{
    static bool Prefix(CardModel __instance,ref Task __result)
    {
        if(ContractRuntime.For(__instance.Owner) is not {Finished:false} d)return true;
        if(!d.Active.Hand.Cards.Contains(__instance)){__result=Task.CompletedTask;return false;}
        return true;
    }
}
