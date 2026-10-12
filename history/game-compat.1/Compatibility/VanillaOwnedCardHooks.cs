using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
namespace RinArcherCore;

public static class VanillaOwnedCardHooks
{
    public static IEnumerable<MethodInfo> Methods()=>typeof(ModelDb).Assembly.GetTypes().Where(t=>!t.IsAbstract&&(typeof(CardModel).IsAssignableFrom(t)||typeof(EnchantmentModel).IsAssignableFrom(t)))
        .SelectMany(t=>t.GetMethods(BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.DeclaredOnly))
        .Where(m=>!m.ContainsGenericParameters&&!m.Name.StartsWith("get_")&&!m.Name.StartsWith("set_")&&m.GetMethodBody()!=null);
    public static Creature PersonalCreature(Player player)=>GenericScopedIdentity.PersonalCreature(player);
}
[HarmonyPatch]
public static class VanillaOwnedCardCallbackScope
{
    static IEnumerable<MethodBase> TargetMethods()=>VanillaOwnedCardHooks.Methods();
    static void Prefix(AbstractModel __instance,MethodBase __originalMethod,out IDisposable? __state)
    {
        __state=null;if(!__instance.IsMutable)return;
        CardModel? card=__instance as CardModel??(__instance is EnchantmentModel enchantment?enchantment.Card:null);
        if(card==null||card.Owner is not {} p||!GenericCompatibility.Enabled(p)||ContractRuntime.For(p) is not {Finished:false} d)return;
        string? member=(GenericCombatCardOwnership.Get(card)??NativePermanentCards.Get(card))?.Member;
        if(member==null)return;
        __state=CompatibilityExecution.Bind(new(p,card.Id.ToString(),__originalMethod.Name,[],d.Member(member).Creature,null));
    }
    static void Postfix(IDisposable? __state)=>__state?.Dispose();
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}
[HarmonyPatch]
public static class VanillaOwnedCardPersonalIdentity
{
    static IEnumerable<MethodBase> TargetMethods()=>VanillaOwnedCardHooks.Methods()
        .Select(m=>m.GetCustomAttribute<AsyncStateMachineAttribute>() is {} s?AccessTools.Method(s.StateMachineType,"MoveNext"):m)
        .Where(m=>!m.ContainsGenericParameters&&PatchProcessor.GetOriginalInstructions(m).Any(i=>i.Calls(AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature))))).Distinct();
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature));
        foreach(var i in instructions){if(i.Calls(getter)){i.opcode=OpCodes.Call;i.operand=AccessTools.Method(typeof(VanillaOwnedCardHooks),nameof(VanillaOwnedCardHooks.PersonalCreature));}yield return i;}
    }
}
