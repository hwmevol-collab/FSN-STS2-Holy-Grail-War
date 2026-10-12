using System.Reflection;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;

// Readiness remains separate from classification and native acquisition legality.
public static class GenericCompatibility
{
    static VanillaCompatibilityRegistry? registry;
    static readonly ConditionalWeakTable<Player,HashSet<string>> QaReady=new();
    public static VanillaCompatibilityRegistry Registry=>registry??=VanillaCompatibilityRegistry.LoadEmbedded(VanillaCompatibilityRegistry.InstalledSignature());
    public static bool Enabled(Player p)=>p.Character is RinContractCharacter&&(QaReady.TryGetValue(p,out _)||ContractSave.Get(p).RunFlags.GetValueOrDefault(ProductionCompatibility.Flag));
    public static IReadOnlySet<string> Ready(Player p)=>QaReady.TryGetValue(p,out var ready)?ready:Enabled(p)?ProductionCompatibility.ReadyIds:new HashSet<string>();
    internal static void ClearIsolated(Player p)=>QaReady.Remove(p);
    public static void EnableIsolated(Player p,IEnumerable<string> validatedIds)
    {
        if(!TestMode.IsOn&&!OS.GetUserDataDir().Contains("RinArcherE2AAmended-20261009"))throw new InvalidOperationException("Isolated E2A readiness outside QA profile");
        ContractEffectResolver.RequireContract(p);
        if(!Registry.IsValid)throw new InvalidOperationException("VANILLA_COMPATIBILITY_VERSION_MISMATCH: "+Registry.FailureReason);
        var state=ContractSave.Get(p).Compatibility;
        if(state.MatrixSignature.Length>0&&state.MatrixSignature!=Registry.MatrixSignature)throw new InvalidOperationException("COMPATIBILITY_SAVE_MIGRATION_REQUIRED");
        QaReady.Remove(p);QaReady.Add(p,validatedIds.ToHashSet(StringComparer.Ordinal));
        state.MatrixRevision=CompatibilityMatrixFingerprint.Revision;state.MatrixSignature=Registry.MatrixSignature;
    }
    public static IEnumerable<MethodBase> NativeMethods()
    {
        foreach(var entry in Registry.Entries.Where(e=>(e.Classification is "NATIVE_SAFE" or "GENERIC_ADAPTER"||E2CCustomAdapters.Audited(e.ContentId))&&e.ModelType!=null))
        {
            var type=typeof(ModelDb).Assembly.GetType(entry.ModelType!);if(type==null)continue;
            foreach(var name in entry.Effects.Where(e=>!e.Trigger.StartsWith("POWER_DEPENDENCY/")).Select(e=>e.Trigger).Distinct(StringComparer.Ordinal))
                foreach(var method in type.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly).Where(m=>m.Name==name&&!m.ContainsGenericParameters))yield return method;
        }
    }
    public static Player? Player(AbstractModel model)=>model switch{RelicModel relic=>relic.Owner,PotionModel potion=>potion.Owner,EventModel ev=>ev.Owner,_=>null};
    public static EffectScopeBinding? Resolve(AbstractModel model,MethodBase method,object[] args)
    {
        var p=Player(model);if(p==null||!Enabled(p))return null;
        string id=model.Id.ToString();var rows=Registry.GetEffectScopes(id).Where(e=>e.Trigger==method.Name).ToArray();if(rows.Length==0)return null;
        var d=ContractRuntime.For(p);ActiveScopeSnapshot? active=d is {Finished:false}?ActiveCharacterEffectResolver.Capture(d,id+"/"+method.Name):null;
        Creature? recipient=null;
        var scopes=rows.Select(r=>r.Scope).ToHashSet(StringComparer.Ordinal);
        if(scopes.Contains("CHOOSE_MEMBER")||FriendlyPotionTargeting.ChoosesHand(model,method.Name))
        {
            if(NativeMemberConditionContext.UsesNativeRecipient(model,method.Name))recipient=p.Creature;
            else
            {
                if(!ContractSave.Get(p).Compatibility.MemberBindings.TryGetValue(id+"/"+method.Name,out var member))throw new InvalidOperationException("MEMBER_BINDING_REQUIRED_BEFORE_EFFECT: "+id);
                recipient=MemberTargetResolver.Creature(p,member);
            }
        }
        else if(scopes.Contains("CARD_OWNER")&&d!=null)
        {
            var card=args.OfType<CardPlay>().Select(play=>play.Card).FirstOrDefault()??args.OfType<CardModel>().FirstOrDefault();
            if(card!=null)recipient=CardOwnerEffectResolver.Resolve(d,card,id+"/"+method.Name).Creature;
        }
        if(recipient==null&&scopes.Contains("DAMAGE_TARGET")&&d!=null)
        {
            var target=args.OfType<DamageResult>().Select(result=>result.Receiver).FirstOrDefault();
            target??=method.GetParameters().Select((param,i)=>(param,i)).Where(x=>x.param.Name is "target" or "creature").Select(x=>args[x.i]).OfType<Creature>().FirstOrDefault();
            if(target!=null)recipient=DamageTargetEffectResolver.Resolve(d,target,id+"/"+method.Name);
        }
        if(recipient==null&&(scopes.Contains("ACTIVE_AT_TRIGGER")||scopes.Contains("ACTIVE_HAND")))recipient=active?.Creature??p.Creature;
        string? deckMember=null;
        if(scopes.Contains("CHOOSE_DECK")&&!ContractSave.Get(p).Compatibility.MemberBindings.TryGetValue(id+"/"+method.Name,out deckMember))throw new InvalidOperationException("DECK_BINDING_REQUIRED_BEFORE_EFFECT: "+id);
        return new(p,id,method.Name,rows,recipient,active,deckMember);
    }
}
[HarmonyPatch]
public static class GenericVanillaHookScope
{
    static bool Prepare()=>GenericCompatibility.Registry.IsValid;
    static IEnumerable<MethodBase> TargetMethods()=>GenericCompatibility.NativeMethods();
    static void Prefix(AbstractModel __instance,MethodBase __originalMethod,object[] __args,bool __runOriginal,out IDisposable? __state)
    {var binding=__runOriginal?GenericCompatibility.Resolve(__instance,__originalMethod,__args):null;__state=binding==null?null:CompatibilityExecution.Bind(binding);}
    static void Postfix(IDisposable? __state)=>__state?.Dispose();
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}
public static class GenericScopedIdentity
{
    public static Creature PersonalCreature(Player player)
    {
        if(CompatibilityExecution.Current is {PersonalRecipient:{} target} binding&&ReferenceEquals(binding.Player,player)
            &&(target==ContractRuntime.For(player)?.Rin.Creature||target==ContractRuntime.For(player)?.Archer.Creature||target==RunEconomy.Servant(player)))return target;
        return player.Creature;
    }
    public static Player? MemberPlayer(Creature creature)
    {
        if(creature.Player is {} native)return native;
        if(CompatibilityExecution.Current is {} binding&&creature.Side==CombatSide.Player
            &&(binding.PersonalRecipient==creature||ContractRuntime.For(binding.Player) is {} dual
                &&(creature==dual.Rin.Creature||creature==dual.Archer.Creature)))return binding.Player;
        return null;
    }
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Hooks.Hook),nameof(MegaCrit.Sts2.Core.Hooks.Hook.ModifyDamage))]
public static class GenericDamageDispatchIdentity
{
    static void Prefix(Creature? target,Creature? dealer,CardModel? cardSource,out IDisposable? __state)
    {
        __state=null;
        var p=cardSource?.Owner??ContractRuntime.For(target!)?.Player??ContractRuntime.For(dealer!)?.Player;
        if(p==null||!GenericCompatibility.Enabled(p))return;
        var d=ContractRuntime.For(p);if(d==null)return;
        Creature? recipient=cardSource is StarterCard?CardOwnerEffectResolver.Resolve(d,cardSource,"NATIVE_DAMAGE_DISPATCH").Creature:
            target==d.Rin.Creature||target==d.Archer.Creature?target:dealer==d.Rin.Creature||dealer==d.Archer.Creature?dealer:null;
        __state=CompatibilityExecution.Bind(new(p,"ENGINE_NATIVE_DAMAGE_DISPATCH","ModifyDamage",[],recipient,null));
    }
    static void Postfix(IDisposable? __state)=>__state?.Dispose();
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}
