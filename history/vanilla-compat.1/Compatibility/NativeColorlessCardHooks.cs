using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Commands.Builders;
namespace RinArcherCore;

// Bind only these five native OnPlay tasks. No native character or model ID changes.
[HarmonyPatch]
public static class NativeColorlessPlayScope
{
    [ThreadStatic] static bool invoking;
    static IEnumerable<MethodBase> TargetMethods()=>NativePermanentCards.Types.Select(t=>AccessTools.Method(t,"OnPlay"));
    static bool Prefix(CardModel __instance,PlayerChoiceContext choiceContext,CardPlay cardPlay,MethodBase __originalMethod,ref Task __result)
    {
        if(invoking||ContractRuntime.For(__instance.Owner) is not {Finished:false} d||GenericCombatCardOwnership.Get(__instance) is not {} owner)return true;
        __result=Play(__instance,d,owner,choiceContext,cardPlay,__originalMethod);return false;
    }
    static async Task Play(CardModel card,ContractRuntime d,CombatCardOwner owner,PlayerChoiceContext ctx,CardPlay play,MethodBase method)
    {
        if(d.Active.CharacterId!=owner.Member)throw new InvalidOperationException("Native card played outside its bank");
        using var binding=CompatibilityExecution.Bind(new(d.Player,card.Id.ToString(),"OnPlay",[],d.Member(owner.Member).Creature,null));
        Task original;invoking=true;try{original=(Task)method.Invoke(card,[ctx,play])!;}finally{invoking=false;}
        await original;
        ContractSave.Log(d.Player,"NATIVE_COLORLESS_RESOLVED",new{cardId=card.Id.ToString(),owner=owner.Member,instanceId=owner.InstanceId});
    }
}
[HarmonyPatch]
public static class NativeColorlessPersonalIdentity
{
    static IEnumerable<MethodBase> TargetMethods()=>NativePermanentCards.Types.Select(t=>AccessTools.Method(t,"OnPlay").GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType).Select(t=>AccessTools.Method(t,"MoveNext"));
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature));
        foreach(var c in instructions){if(c.Calls(getter)){c.opcode=OpCodes.Call;c.operand=AccessTools.Method(typeof(GenericScopedIdentity),nameof(GenericScopedIdentity.PersonalCreature));}yield return c;}
    }
}
[HarmonyPatch(typeof(AttackCommand),nameof(AttackCommand.FromCard))]
public static class NativeColorlessAttackOwner
{
    static void Postfix(AttackCommand __instance,CardModel card)
    {if(NativePermanentCards.Supported(card)&&GenericCombatCardOwnership.Get(card) is {} owner&&ContractRuntime.For(card.Owner) is {Finished:false} d)AccessTools.Property(typeof(AttackCommand),nameof(AttackCommand.Attacker)).SetValue(__instance,d.Member(owner.Member).Creature);}
}
[HarmonyPatch(typeof(CardModel),"get_IsPlayable")]
public static class NativeColorlessPlayableOwner
{
    static void Postfix(CardModel __instance,ref bool __result)
    {if(GenericCombatCardOwnership.Get(__instance) is {} owner&&NativePermanentCards.Supported(__instance)&&ContractRuntime.For(__instance.Owner) is {} d)__result&=d.StartingSelected&&!d.Finished&&d.Active.CharacterId==owner.Member;}
}
