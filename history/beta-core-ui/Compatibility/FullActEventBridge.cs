using System.Reflection;
using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;

// Exact native C models, enabled only by the signed E2B development capability.
public static class FullActEventBridge
{
    public static readonly IReadOnlySet<string> Ids=new HashSet<string>(["EVENT.JUNGLE_MAZE_ADVENTURE","EVENT.COLOSSAL_FLOWER","EVENT.NEOW","EVENT.TEZCATARA","EVENT.LOST_WISP"],StringComparer.Ordinal);
    public static IReadOnlySet<string> Ready(Player p)
    {
        if(!FullActRoomSpine.Enabled(p)||!GenericCompatibility.Registry.IsValid)return new HashSet<string>();
        var context=new CompatibilityEligibilityContext(true,true,"E2B_LOST_WISP_FIXED_DEPENDENCY",GenericCompatibility.Ready(p),null,Ids);
        return GenericCompatibility.Registry.IsRelicEligible("RELIC.LOST_WISP",context)?Ids:Ids.Where(id=>id!="EVENT.LOST_WISP").ToHashSet(StringComparer.Ordinal);
    }
    internal static readonly AsyncLocal<bool> Invoking=new();
    public static async Task Invoke(EventModel model,MethodBase original)
    {
        var p=model.Owner!;var trigger=original.Name;
        var before=Invoking.Value;Invoking.Value=true;
        try
        {
            // One named member pays the native damage budget; shared gold remains once.
            string key=model.Id+"/"+ContractSave.RoomKey(p)+"/DAMAGE_MEMBER";
            string? chosen=null;
            if(trigger is "DontNeedHelp" or "DealReachDeeperDamage")
            {
                if(!ContractSave.Get(p).Compatibility.MemberBindings.TryGetValue(key,out chosen))
                {
                    int budget=18;
                    var preview=MemberTargetResolver.Preview(p,c=>(Math.Max(0,c.CurrentHp-budget),c.MaxHp));
                    chosen=await MemberTargetResolver.Choose(p,key,preview,"选择承担原生事件生命损失的成员（整项事件至多 18 HP）",false);
                    if(chosen==null)throw new OperationCanceledException("Event member required before any effect");
                    MemberTargetResolver.Persist(p,key,chosen);
                }
            }
            // The native Claim creates exactly one Decay. Bind its permanent owner
            // before the native curse acquisition, using the existing member resolver.
            if(model is LostWisp&&trigger=="Claim")
            {
                key=model.Id+"/"+ContractSave.RoomKey(p)+"/CURSE_OWNER";
                if(!ContractSave.Get(p).Compatibility.MemberBindings.TryGetValue(key,out chosen))
                {
                    var preview=MemberTargetResolver.Preview(p,c=>(c.CurrentHp,c.MaxHp));
                    chosen=await MemberTargetResolver.Choose(p,key,preview,"选择接收原生腐朽诅咒的永久牌组（仅一张）",false);
                    if(chosen==null)throw new OperationCanceledException("Curse owner required before any effect");
                    MemberTargetResolver.Persist(p,key,chosen);
                }
            }
            using var scope=CompatibilityExecution.Bind(new(p,model.Id.ToString(),trigger,GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()),chosen==null?null:MemberTargetResolver.Creature(p,chosen),null,model is LostWisp?chosen:null));
            await (Task)original.Invoke(model,null)!;
            MemberTargetResolver.Synchronize(p);
        }
        finally{Invoking.Value=before;}
    }
}
[HarmonyPatch(typeof(EventRoom),"OnEventStateChanged")]
public static class FullActNativeEventCompletionSave
{
    static void Postfix(EventRoom __instance,EventModel eventModel)
    {
        var p=eventModel.Owner;
        if(p==null||!FullActRoomSpine.Enabled(p)||eventModel is AncientEventModel||!FullActEventBridge.Ids.Contains(eventModel.Id.ToString())||!eventModel.IsFinished)return;
        string key=ContractSave.RoomKey(p);var state=ContractSave.Get(p);
        if(__instance.IsPreFinished&&state.CompletedNativeEvents.GetValueOrDefault(key)==eventModel.Id.ToString())return;
        state.CompletedNativeEvents[key]=eventModel.Id.ToString();state.NativeEventDescriptions[key]=eventModel.Description!.GetFormattedText();
        __instance.MarkPreFinished();_=MegaCrit.Sts2.Core.Helpers.TaskHelper.RunSafely(ContractSave.Checkpoint(p,"E2B_NATIVE_EVENT_COMPLETE"));
    }
}
[HarmonyPatch(typeof(EventModel),"SetInitialEventState")]
public static class FullActNativeEventCompletionRestore
{
    static bool Prefix(EventModel __instance,bool isPreFinished)
    {
        var p=__instance.Owner;
        if(!isPreFinished||p==null||!FullActRoomSpine.Enabled(p)||__instance is AncientEventModel||!FullActEventBridge.Ids.Contains(__instance.Id.ToString()))return true;
        string key=ContractSave.RoomKey(p);var state=ContractSave.Get(p);
        if(state.CompletedNativeEvents.GetValueOrDefault(key)!=__instance.Id.ToString()||!state.NativeEventDescriptions.TryGetValue(key,out var description))throw new InvalidDataException("E2B_NATIVE_EVENT_COMPLETION_BINDING_MISMATCH");
        AccessTools.Method(typeof(EventModel),"SetEventFinished").Invoke(__instance,[EconomyNativeUi.Text(description)]);return false;
    }
}
[HarmonyPatch]
public static class FullActNativeEventEffects
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(JungleMazeAdventure),"DontNeedHelp"),AccessTools.Method(typeof(JungleMazeAdventure),"SafetyInNumbers"),AccessTools.Method(typeof(ColossalFlower),"DealReachDeeperDamage"),AccessTools.Method(typeof(LostWisp),"Claim"),AccessTools.Method(typeof(LostWisp),"Search")};
    static bool Prefix(EventModel __instance,MethodBase __originalMethod,ref Task __result)
    {
        if(FullActEventBridge.Invoking.Value||__instance.Owner==null||!FullActRoomSpine.Enabled(__instance.Owner))return true;
        __result=FullActEventBridge.Invoke(__instance,__originalMethod);return false;
    }
}
[HarmonyPatch]
public static class FullActEventRecipientIdentity
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(JungleMazeAdventure),"DontNeedHelp"),AccessTools.Method(typeof(ColossalFlower),"DealReachDeeperDamage")}
        .Select(m=>AccessTools.Method(m.GetCustomAttribute<System.Runtime.CompilerServices.AsyncStateMachineAttribute>()!.StateMachineType,"MoveNext"));
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {
        var getter=AccessTools.PropertyGetter(typeof(Player),nameof(Player.Creature));
        foreach(var i in instructions){if(i.Calls(getter)){i.opcode=System.Reflection.Emit.OpCodes.Call;i.operand=AccessTools.Method(typeof(GenericScopedIdentity),nameof(GenericScopedIdentity.PersonalCreature));}yield return i;}
    }
}
[HarmonyPatch(typeof(RoomSet),nameof(RoomSet.EnsureNextEventIsValid))]
public static class FullActUniqueNativeEventCursor
{
    static void Prefix(RoomSet __instance,RunState runState)
    {
        if(!FullActRoomSpine.Enabled(runState))return;
        // Native RoomSet deliberately allows repetition after exhausting unique IDs.
        // VisitedEventIds is a preference, while IsAllowed remains a hard condition.
        if(!__instance.events.Any(e=>e.IsAllowed(runState)))
            throw new CompatibilitySourceUnavailableException("E2B_NATIVE_EVENT_POOL_EXHAUSTED: no native eligible event even under native repetition fallback");
    }
    static void Postfix(RoomSet __instance,RunState runState)
    {
        if(!FullActRoomSpine.Enabled(runState))return;
        // Vanilla's exhausted fallthrough may point to a rejected model. Keep its
        // original unique-first scan, then bound the fallback by one native pool cycle.
        for(int i=0;i<__instance.events.Count;i++)
        {
            if(__instance.NextEvent.IsAllowed(runState))return;
            __instance.eventsVisited++;
        }
        throw new CompatibilitySourceUnavailableException("E2B_NATIVE_EVENT_POOL_EXHAUSTED: qualifications changed during native cursor selection");
    }
}

// Exact Decay representation for the LostWisp native transaction only. It shares
// the accepted owned-card/deck/save pipeline and is absent from ordinary pools.
[Pool(typeof(RinArcherPool))]
public sealed class FullActOwnedDecay():StarterCard(CardType.Curse,TargetType.None,-1,false,CardRarity.Curse)
{
    [MegaCrit.Sts2.Core.Saves.Runs.SavedProperty] public string NativeCurseOwner{get;set;}=RunEconomy.Rin;
    public override string SourceCardId=>"VANILLA_DECAY";
    public override string OwnerCharacterId=>NativeCurseOwner;
    public override int MaxUpgradeLevel=>0;
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Unplayable];
    public override bool HasTurnEndInHandEffect=>true;
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new DamageVar(2m,ValueProp.Unpowered|ValueProp.Move)];
    protected override string NameText=>"腐朽";
    protected override string RulesText=>"无法打出。回合结束时，若此牌在手牌中，其所属成员受到 2 点伤害。";
    protected override Task OnTurnEndInHand(PlayerChoiceContext context)=>CreatureCmd.Damage(context,Runtime.Member(OwnerCharacterId).Creature,DynamicVars.Damage,this);
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.AddCursesToDeck))]
public static class FullActLostWispCurseOwner
{
    static bool Prefix(IEnumerable<CardModel> curses,Player owner,ref Task<IEnumerable<MegaCrit.Sts2.Core.Entities.Cards.CardPileAddResult>> __result)
    {
        if(!FullActRoomSpine.Enabled(owner)||CompatibilityExecution.Current is not {ContentId:"EVENT.LOST_WISP",Trigger:"Claim",DeckMember:{} member})return true;
        var native=curses.ToArray();
        if(native.Length!=1||native[0] is not MegaCrit.Sts2.Core.Models.Cards.Decay)throw new InvalidDataException("E2B_LOST_WISP_NATIVE_CURSE_BUDGET_CHANGED");
        __result=Add(owner,member);return false;
    }
    static async Task<IEnumerable<MegaCrit.Sts2.Core.Entities.Cards.CardPileAddResult>> Add(Player p,string member)
    {
        var card=(FullActOwnedDecay)p.RunState.CreateCard(ModelDb.Card<FullActOwnedDecay>(),p);
        card.NativeCurseOwner=member;card.InstanceId="native-decay:"+member+":"+ContractSave.RoomKey(p);
        var results=new[]{await CardPileCmd.Add(card,ContractSave.Deck(p,member))};
        CardCmd.PreviewCardPileAdd(results,2f);return results;
    }
}
