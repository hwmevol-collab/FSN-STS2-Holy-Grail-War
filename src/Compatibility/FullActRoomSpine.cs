using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.TestSupport;
using MegaCrit.Sts2.Core.Entities.Cards;
namespace RinArcherCore;

// Native noncombat Continue may append a history entry. A completed treasure is
// already bound by the accepted act/map-coordinate ledger: re-entering its UI
// must not replace the saved transaction phase with a new entry checkpoint.
[HarmonyPatch(typeof(GenericTreasureEntryCheckpoint),"Postfix")]
public static class FullActCompletedTreasureRestore
{
    static bool Prefix()
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(FullActRoomSpine.Enabled);
        if(p==null||p.RunState.CurrentRoom is not TreasureRoom)return true;
        var ledger=GenericTreasureSource.State(p);
        return !(ledger.Complete&&ledger.GoldProcessed);
    }
}

// Native Contract room dispatch; content still requires its exact adapter readiness.
public static class FullActRoomSpine
{
    public const string Flag="E2B_FULL_ACT_ROOM_SPINE";
    public static bool Enabled(Player p)=>p.Character is RinContractCharacter&&ContractSave.Get(p).RunFlags.GetValueOrDefault(Flag);
    public static bool Enabled(RunState? run)=>run?.Players.Any(Enabled)==true;
    public static void EnableDevelopment(Player p)
    {
        if(!TestMode.IsOn&&!OS.GetUserDataDir().Contains("RinArcherE2B-20261009")&&!OS.GetUserDataDir().Contains("RinArcherE2BResolution-20261009"))
            throw new InvalidOperationException("E2B development capability requires its independent profile");
        EnablePublic(p);
    }
    public static void EnablePublic(Player p)
    {ProductionCompatibility.Enable(p);ContractSave.Get(p).RunFlags[Flag]=true;}
    public static bool IsDispatchDomain(string id)=>id is "MapPointType.Elite" or "RoomType.Elite" or "MapPointType.Boss" or "RoomType.Boss" or "MapPointType.Unknown" or "RoomType.Event" or "MapPointType.Ancient" or "RoomType.Ancient";
    public static IReadOnlyList<CardModel> NativeBossCards(Player p)=>CardCreationOptions.ForRoom(p,RoomType.Boss).GetPossibleCards(p)
        .Where(c=>c.Rarity is CardRarity.Common or CardRarity.Uncommon or CardRarity.Rare).Distinct().ToArray();
    public static RoomSet NativeRooms(IRunState run)=>(RoomSet)AccessTools.Field(typeof(ActModel),"_rooms").GetValue(run.Act)!;
    public static IReadOnlyList<EventModel> NativeEligibleEvents(Player p)
        =>NativeRooms(p.RunState).events.Where(e=>e.IsAllowed(p.RunState)).ToArray();
    public static bool NativeEventAvailable(Player p)
    {
        var rooms=NativeRooms(p.RunState);
        if(rooms.events.Count==0)return false;
        return rooms.events.Any(e=>e.IsAllowed(p.RunState)); // Native unique-first then repetition fallback.
    }
    public static bool DispatchReady(Player p,string id)
    {
        if(!Enabled(p)||!GenericCompatibility.Registry.IsValid)return false;
        if(id is "MapPointType.Ancient" or "RoomType.Ancient")return NativeRooms(p.RunState).HasAncient&&FullActAncientBridge.Budget(p,p.RunState.Act.Ancient);
        if(id=="RoomType.Event")return NativeEventAvailable(p);
        if(id=="MapPointType.Unknown")
        {
            // Native first-progress Unknown rules force Event, Event, then Monster.
            // An impossible Shop branch must not close a legal Event before RNG.
            var run=p.RunState;
            if(run.UnlockState.NumberOfRuns==0)
            {
                int n=run.MapPointHistory.SelectMany(rows=>rows).Count(point=>point.MapPointType==MapPointType.Unknown);
                if(n<2)return NativeEventAvailable(p);
                if(n==2)return RoomEligibilityResolver.IsEligible(p,"RoomType.Monster","E2B_UNKNOWN_BRANCH",true);
            }
            // Vanilla excludes Shop after Shop. Keep all budgets for possible branches;
            // this does not roll RNG, change odds or edit the native blacklist.
            var blacklist=RunManager.BuildRoomTypeBlacklist(run.CurrentMapPointHistoryEntry,Array.Empty<MapPoint>());
            return NativeEventAvailable(p)&&
                RoomEligibilityResolver.IsEligible(p,"RoomType.Monster","E2B_UNKNOWN_BRANCH",true)&&
                RoomEligibilityResolver.IsEligible(p,"RoomType.Treasure","E2B_UNKNOWN_BRANCH",true)&&
                (blacklist.Contains(RoomType.Shop)||RoomEligibilityResolver.IsEligible(p,"RoomType.Shop","E2B_UNKNOWN_BRANCH",true));
        }
        if(id is "MapPointType.Boss" or "RoomType.Boss")
        {
            if(p.RunState.CurrentActIndex>=p.RunState.Acts.Count-1&&!ReleaseFinaleBridge.Ready(p))return false;
            // Native single-owner boss card reward requests three distinct cards.
            // The accepted starter-only native pool cannot supply that budget.
            // Do not silently substitute DualReward or widen its card pool.
            if(!ContractBossRewardEngine.Budget(p))return false;
        }
        else if(id is not ("MapPointType.Elite" or "RoomType.Elite"))return false;
        var context=CompatibilityCandidateResolver.Context(p,"E2B_NATIVE_COMBAT_REWARD");
        var budgets=context.GenerationBudgets!;
        if(GenericCompatibility.Registry.GenerationBudgetRejection("POOL.NATIVE_POTIONS",budgets["POOL.NATIVE_POTIONS"],context).Length>0)return false;
        return id.EndsWith("Boss",StringComparison.Ordinal)||
            GenericCompatibility.Registry.GenerationBudgetRejection("POOL.NATIVE_RELICS",budgets["POOL.NATIVE_RELICS"],context).Length==0;
    }
    public static async Task Proceed(RunManager manager,Player p)
    {
        if(ContractSave.Get(p).RoomRewards is {} ledger)foreach(var entry in ledger.Entries)entry.Resolved=true;
        await ContractSave.Checkpoint(p,"E2B_ROOM_REWARDS_COMPLETE");
        // Native owns event-stack resumption, not the D2 map shortcut.
        NativeProceed.Value=true;
        try{await manager.ProceedFromTerminalRewardsScreen();}
        finally{NativeProceed.Value=false;}
        NMapScreen.Instance?.SetTravelEnabled(true);
    }
    internal static readonly AsyncLocal<bool> NativeProceed=new();
}

// Native monsters use TargetingAllOpponents even for an ordinary FRONT attack.
// Map each native contract entity to its existing Active body once; explicit
// authored enemy-contract BOTH/LOCKED attacks continue through Targeting.
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Commands.Builders.AttackCommand),"GetPossibleTargets")]
public static class FullActNativeFrontAttack
{
    static void Postfix(MegaCrit.Sts2.Core.Commands.Builders.AttackCommand __instance,ref IReadOnlyList<Creature> __result)
    {
        if(__instance.Attacker?.IsEnemy!=true||!__instance.IsMultiTargeted)return;
        __result=__result.Select(c=>ContractRuntime.For(c) is {} d&&d.Enemy==null&&FullActRoomSpine.Enabled(d.Player)?d.Active.Creature:c).Distinct().ToArray();
    }
}

// The native card UI carries the selected ordinary enemy in CurrentTarget.
// Reuse the existing resolver and damage service for every hit of that play.
[HarmonyPatch(typeof(Targeting),nameof(Targeting.Damage))]
public static class FullActNativeCardTarget
{
    static bool Prefix(ContractRuntime d,ref ContractTarget type,CardModel? card,bool enemy,ref Creature? locked,ref Task __result)
    {
        if(!enemy||type!=ContractTarget.FRONT||d.Enemy!=null||!FullActRoomSpine.Enabled(d.Player)||card?.CurrentTarget is not {} target)return true;
        if(!target.IsAlive){__result=Task.CompletedTask;return false;}
        if(target.IsAlive&&d.Combat.Enemies.Contains(target)){type=ContractTarget.ANY_CONTRACT_MEMBER;locked=target;}
        return true;
    }
}
[HarmonyPatch(typeof(CardModel),"get_TargetType")]
public static class FullActProjectedFrontSelection
{
    static void Postfix(CardModel __instance,ref TargetType __result)
    {
        bool front=__instance is KanshouBakuya||__instance is AlphaRewardCard a&&a.SourceCardId is "RIN-C04" or "RIN-C10" or "RIN-U01" or "RIN-U04" or "RIN-U06" or "RIN-U14" or "RIN-R07" or "ARC-C03" or "ARC-U01" or "ARC-U02" or "ARC-U15" or "ARC-R03" or "ARC-R07";
        if(front&&__instance.IsMutable&&__instance.Owner is {} p&&FullActRoomSpine.Enabled(p)&&ContractRuntime.For(p) is {Enemy:null})__result=TargetType.AnyEnemy;
    }
}
[HarmonyPatch(typeof(Targeting),nameof(Targeting.Resolve))]
public static class FullActNativeFrontPowerTarget
{
    static bool Prefix(ContractRuntime d,ContractTarget type,bool enemy,ref IReadOnlyList<Creature> __result)
    {
        if(!enemy||type!=ContractTarget.FRONT||d.Enemy!=null||!FullActRoomSpine.Enabled(d.Player))return true;
        var target=PileType.Play.GetPile(d.Player).Cards.Select(c=>c.CurrentTarget).FirstOrDefault(c=>c!=null&&c.IsAlive&&d.Combat.Enemies.Contains(c));
        if(target==null)return true;__result=[target];return false;
    }
}
[HarmonyPatch(typeof(StarterCard),"Hit")]
public static class FullActNativeWeakTarget
{
    static void Postfix(StarterCard __instance,PlayerChoiceContext ctx,bool weak,ref Task __result)
    {
        if(weak&&FullActRoomSpine.Enabled(__instance.Owner)&&ContractRuntime.For(__instance.Owner) is {Enemy:null} d&&__instance.CurrentTarget is {} target)__result=After(__result,ctx,d,__instance,target);
    }
    static async Task After(Task original,PlayerChoiceContext ctx,ContractRuntime d,StarterCard card,Creature target)
    {await original;if(target.IsAlive)await PowerCmd.Apply<MegaCrit.Sts2.Core.Models.Powers.WeakPower>(ctx,target,1,d.Rin.Creature,card);}
}

// Native hand flush may batch owned cards with the already accepted temporary
// Status instances. Validate their existing binding, then reuse the original
// destination routing. Different members and permanent foreign cards still fail.
[HarmonyPatch(typeof(OwnerPileRouteHook),"Prefix")]
public static class FullActNativeStatusBatch
{
    static bool Prefix(IEnumerable<CardModel> cards,ref CardPile newPile,ref bool skipVisuals,ref bool __result)
    {
        var list=cards.ToArray();
        if(list.Length==0||!list.Any(c=>c is not StarterCard)||list[0].Owner is not {} p||ContractRuntime.For(p) is not {} d||d.Switching||!FullActRoomSpine.Enabled(p))return true;
        var owners=list.Select(c=>c is StarterCard s?s.OwnerCharacterId:(GenericCombatCardOwnership.Get(c)??NativePermanentCards.Get(c))?.Member).ToArray();
        bool ExactNative(CardModel c)=>c.GetType().Assembly==typeof(ModelDb).Assembly&&(NativePermanentCards.Get(c)!=null||GenericCombatCardOwnership.Get(c)!=null);
        if(owners.Any(o=>o==null)||owners.Distinct().Count()!=1||list.Any(c=>c.Owner!=p)||list.Any(c=>c is not StarterCard&&!(c.Type==CardType.Status&&c.DeckVersion==null)&&!ExactNative(c)))throw new InvalidOperationException("Mixed owner pile operation rejected");
        var owner=d.Member(owners[0]!);
        if(newPile.Type==PileType.Deck||ReferenceEquals(newPile,d.Archer.Deck))
        {if(list.Any(c=>c is not StarterCard&&NativePermanentCards.Get(c)==null))throw new InvalidOperationException("Native combat-only card cannot enter a permanent deck");newPile=owner.Deck;}
        if(d.PileTypes.Contains(newPile.Type)&&owner!=d.Active){newPile=owner.Pile(newPile.Type);skipVisuals=true;}
        __result=true;return false;
    }
}

[HarmonyPatch(typeof(ActModel),nameof(ActModel.PullNextEvent))]
public static class FullActNativeEventExhaustionGuard
{
    static void Prefix(RunState runState)
    {
        var p=runState.Players.FirstOrDefault(FullActRoomSpine.Enabled);if(p==null)return;
        if(!FullActRoomSpine.NativeEventAvailable(p))
            throw new CompatibilitySourceUnavailableException("E2B_NATIVE_EVENT_POOL_EMPTY: native has no eligible fallback");
    }
    static void Postfix(RunState runState,EventModel __result)
    {
        var p=runState.Players.FirstOrDefault(FullActRoomSpine.Enabled);if(p==null)return;
        if(!__result.IsAllowed(runState))throw new CompatibilitySourceUnavailableException("E2B_NATIVE_EVENT_EXHAUSTION_REJECTED");
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.ToSave))]
public static class FullActNativeSaveBoundary
{
    static void Prefix(RunManager __instance)
    {
        foreach(var p in __instance.DebugOnlyGetState()?.Players.Where(FullActRoomSpine.Enabled)??[])
            ContractSave.Sync(p);
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.EnterAct))]
public static class FullActNativeTransitionCheckpoint
{
    static void Postfix(RunManager __instance,ref Task __result)
    {if(FullActRoomSpine.Enabled(__instance.DebugOnlyGetState()))__result=After(__result,__instance);}
    static async Task After(Task original,RunManager manager)
    {
        await original;
        foreach(var p in manager.DebugOnlyGetState()!.Players.Where(FullActRoomSpine.Enabled))
        {
            // Native EnterAct has entered MapRoom: a legal native save boundary.
            await ContractSave.Checkpoint(p,"E2B_NATIVE_ACT_ENTERED");
            ContractSave.Log(p,"E2B_ACT_ENTERED",new{act=p.RunState.CurrentActIndex,map=p.RunState.Map?.GetType().Name,
                ancientPresent=FullActRoomSpine.NativeRooms(p.RunState).HasAncient,
                ancientBlocked=FullActRoomSpine.NativeRooms(p.RunState).HasAncient&&!FullActAncientBridge.Budget(p,p.RunState.Act.Ancient),fullRunAccepted=false});
        }
    }
}
