using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
namespace RinArcherCore;

// Redirect identity reads only in audited model code. Engine Player/Creature
// identity, hook listener enumeration and native serialization remain authoritative.
[HarmonyPatch]
public static class GenericScopedIdentityHooks
{
    static bool Prepare()=>GenericCompatibility.Registry.IsValid;
    static IEnumerable<MethodBase> TargetMethods()
    {
        var methods=GenericCompatibility.NativeMethods().OfType<MethodInfo>().ToList();
        foreach(var dependency in GenericCompatibility.Registry.Entries
            .Where(e=>e.Classification is "NATIVE_SAFE" or "GENERIC_ADAPTER")
            .SelectMany(e=>e.PowerDependencies??[]))
        {
            var type=typeof(ModelDb).Assembly.GetType(dependency.ModelType)??throw new InvalidOperationException("Audited power type missing");
            foreach(string name in dependency.Hooks)
                methods.AddRange(type.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly).Where(m=>m.Name==name));
        }
        Type Root(Type type){while(type.IsNested)type=type.DeclaringType!;return type;}
        var visited=new HashSet<MethodBase>();
        void Visit(MethodInfo method,Type modelType)
        {
            var target=method.GetCustomAttribute<AsyncStateMachineAttribute>() is {} machine?AccessTools.Method(machine.StateMachineType,"MoveNext"):method;
            if(target.GetMethodBody()==null||!visited.Add(target))return;
            foreach(var instruction in PatchProcessor.GetOriginalInstructions(target))
                if(instruction.operand is MethodInfo helper&&helper.DeclaringType!=null&&Root(helper.DeclaringType)==modelType&&!helper.ContainsGenericParameters)Visit(helper,modelType);
        }
        foreach(var method in methods)Visit(method,Root(method.DeclaringType!));
        return visited;
    }
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var creature=AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature));
        var player=AccessTools.PropertyGetter(typeof(Creature),nameof(Creature.Player));
        foreach(var instruction in instructions)
        {
            if(instruction.Calls(creature))
            {instruction.opcode=OpCodes.Call;instruction.operand=AccessTools.Method(typeof(GenericScopedIdentity),nameof(GenericScopedIdentity.PersonalCreature));}
            else if(instruction.Calls(player))
            {instruction.opcode=OpCodes.Call;instruction.operand=AccessTools.Method(typeof(GenericScopedIdentity),nameof(GenericScopedIdentity.MemberPlayer));}
            yield return instruction;
        }
    }
}
