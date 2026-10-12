using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rewards;
using MegaCrit.Sts2.Core.Entities.Cards;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.Helpers;
using System.Runtime.CompilerServices;
namespace RinArcherCore;
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Nodes.NGame),nameof(MegaCrit.Sts2.Core.Nodes.NGame.LoadRun))]
public static class ContractRunLauncherCleanup{static void Prefix()=>CoreHud.ClearLauncher();}
[HarmonyPatch(typeof(RunManager),"InitializeNewRun")]
public static class ContractNewRunHook
{
    static void Postfix(RunManager __instance)
    {
        foreach(var p in __instance.DebugOnlyGetState()!.Players.Where(p=>p.Character is RinContractCharacter))
        {
            ContractSave.InitializeGameplay(p);ContractSave.EnsureDecks(p);var s=ContractSave.Get(p);
            s.RunFlags[PublicUiMode.Flag]=D1Run.Creating?D1Run.CreatingPublicUi:!PublicUiMode.CreatingDebugRun;
            if(D1Run.Creating){s.RunFlags["QA_D1_RUN"]=true;s.RunFlags["NOT_PUBLIC_FINAL_RUN"]=true;((RunState)p.RunState).ExtraFields.StartedWithNeow=false;}
            if(D2Run.Creating){s.RunFlags["QA_D2_RUN"]=true;s.RunFlags["NOT_PUBLIC_FINAL_RUN"]=true;s.RunFlags[PublicUiMode.Flag]=D2Run.CreatingPublicUi;((RunState)p.RunState).ExtraFields.StartedWithNeow=false;}
            ContractSave.Sync(p);ContractSave.Log(p,"RUN_STARTED",new{runSeed=p.RunState.Rng.StringSeed,qaD1Run=D1Run.IsQa(p),NOT_PUBLIC_FINAL_RUN=true});
        }
    }
}
[HarmonyPatch(typeof(RunManager),"InitializeSavedRun")]
public static class ContractLoadedRunHook
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(RunManager __instance)
    {
        GenericSavedRunSignature.Validate(__instance);
        foreach(var p in __instance.DebugOnlyGetState()!.Players.Where(p=>p.Character is RinContractCharacter))
        {ContractSave.EnsureDecks(p);ContractSave.Sync(p,true);ResumeDualRewardHook.Request(p);ContractSave.Log(p,"RUN_STATE_LOADED",new{phase=ContractSave.Get(p).SavePhase});}
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.GenerateMap))]
public static class D1MapHook
{
    static void Postfix(RunManager __instance,ref Task __result){if(D1Run.IsQa(__instance.DebugOnlyGetState()))__result=After(__result,__instance);}
    static async Task After(Task original,RunManager manager)
    {
        await original;var run=manager.DebugOnlyGetState()!;
        if(run.Map is not MegaCrit.Sts2.Core.Map.SavedActMap)run.Map=new D1ActMap(run.CurrentActIndex,run.Map!.GetRowCount());
        else if(run.Map.StartingMapPoint.coord.row<0)
        {
            // v0.4.0 D1 saves keep encounter coordinates 0/1/2. Repair only the
            // legacy layout, preserving visited rooms, decks, offers and RNG state.
            run.Map=new D1ActMap(run.CurrentActIndex,run.Act.GetNumberOfRooms(run.Players.Count>1)+1);
            foreach(var p in run.Players.Where(D1Run.IsQa))ContractSave.Log(p,"D1_MAP_LAYOUT_MIGRATED",new{from=1,to=2});
        }
        NMapScreen.Instance?.SetMap(run.Map,run.Rng.Seed,true);NMapScreen.Instance?.SetTravelEnabled(true);
    }
}
[HarmonyPatch(typeof(RunManager),"CreateRoom")]
public static class D1RoomHook
{
    static bool Prefix(RunManager __instance,RoomType roomType,ref AbstractRoom __result)
    {
        var run=__instance.DebugOnlyGetState();if(!D1Run.IsQa(run))return true;
        if(roomType==RoomType.Map)return true;
        if(roomType is not (RoomType.Monster or RoomType.Elite))throw new InvalidOperationException("NOT_YET_SUPPORTED_IN_D1");
        __result=new CombatRoom(roomType==RoomType.Elite?ModelDb.Encounter<QaD1Elite>().ToMutable():ModelDb.Encounter<QaD1Normal>().ToMutable(),run);return false;
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.EnterMapCoord))]
public static class ContractTravelGate
{
    public static bool Pending(Player p)=>ContractBossRewardUi.Committing||ContractSave.Get(p).BossRewards.Any(s=>s.RoomIdentity==ContractSave.RoomKey(p)&&!s.Complete)||DualRewardUi.Committing||RunEconomy.Enabled(p)&&ContractMerchant.IsBusy(p)||ContractSave.Get(p).DualRewards.Any(s=>s.RoomIdentity==ContractSave.RoomKey(p)&&!s.Complete);
    static bool Prefix(RunManager __instance,ref Task __result)
    {
        if(__instance.DebugOnlyGetState()?.Players.Any(p=>p.Character is RinContractCharacter&&Pending(p))!=true)return true;
        __result=Task.CompletedTask;return false;
    }
}
public static class RunRewardLedger
{
    static readonly ConditionalWeakTable<Reward,RoomRewardEntry> Entries=new();
    public static void Bind(Reward reward,RoomRewardEntry entry){Entries.Remove(reward);Entries.Add(reward,entry);}
    public static async Task AfterSelect(Task<bool> original,Reward reward)
    {
        bool success=await original;
        if(success&&Entries.TryGetValue(reward,out var entry))
        {entry.Resolved=true;await ContractSave.Checkpoint(reward.Player,"REWARD_RESOLVED");}
    }
    public static Reward Restore(Player p,RoomRewardEntry entry)
    {
        Reward reward=entry.BossIndex is int boss?new ContractBossCardReward(p,ContractSave.Get(p).BossRewards.Single(s=>s.RewardIndex==boss)):entry.DualIndex is int index?new DualCardReward(p,ContractSave.Get(p).DualRewards.Single(s=>s.RewardIndex==index))
            :entry.Native.RewardType==RewardType.Potion&&entry.Native.PredeterminedModelId!=ModelId.none
            ?new PotionReward(ModelDb.GetById<PotionModel>(entry.Native.PredeterminedModelId).ToMutable(),p)
            :Reward.FromSerializable(entry.Native,p);
        if(reward is SpecialCardReward&&entry.NativeCardOwner is {} member&&entry.NativeCardInstance is {} instance)
            NativePermanentCards.Bind((CardModel)AccessTools.Field(typeof(SpecialCardReward),"_card").GetValue(reward)!,member,instance);
        Bind(reward,entry);return reward;
    }
}
[HarmonyPatch(typeof(RewardsSet),nameof(RewardsSet.WithRewardsFromRoom))]
public static class RestoreContractRoomRewards
{
    static bool Prefix(RewardsSet __instance,AbstractRoom room,ref RewardsSet __result)
    {
        var p=__instance.Player;if(p.Character is not RinContractCharacter)return true;
        var saved=ContractSave.Get(p).RoomRewards;if(saved?.RoomIdentity!=ContractSave.RoomKey(p))return true;
        __instance.EmptyForRoom(room);
        foreach(var entry in saved.Entries.Where(e=>!e.Resolved&&!(e.BossIndex is int b&&ContractSave.Get(p).BossRewards.Single(s=>s.RewardIndex==b).Complete)&&!(e.DualIndex is int i&&ContractSave.Get(p).DualRewards.Single(s=>s.RewardIndex==i).Complete)))__instance.Rewards.Add(RunRewardLedger.Restore(p,entry));
        AccessTools.Field(typeof(RewardsSet),"_isGenerated").SetValue(__instance,true);
        __result=__instance;return false;
    }
}
[HarmonyPatch(typeof(RewardsSet),nameof(RewardsSet.GenerateWithoutOffering))]
public static class ReplaceContractCardRewards
{
    static void Prefix(RewardsSet __instance,bool __runOriginal)
    {
        if(!__runOriginal)return;
        var p=__instance.Player;if(p.Character is not RinContractCharacter||__instance.Rewards.Any(r=>r is DualCardReward))return;
        if(ContractSave.Get(p).RoomRewards?.RoomIdentity==ContractSave.RoomKey(p))return;
        if(!GenericCompatibility.Enabled(p)&&(D1Run.IsQa(p)||RunEconomy.Enabled(p)))__instance.Rewards.RemoveAll(r=>r is RelicReward or PotionReward);
        
        for(int i=0;i<__instance.Rewards.Count;i++)if(__instance.Rewards[i] is CardReward card)
        {
            var options=(CardCreationOptions)AccessTools.Property(typeof(CardReward),"Options").GetValue(card)!;
            __instance.Rewards[i]=FullActRoomSpine.Enabled(p)&&__instance.Room?.RoomType==RoomType.Boss
                ?new ContractBossCardReward(p,ContractBossRewardEngine.Create(p,options.RarityOdds))
                :new DualCardReward(p,DualRewardEngine.Create(p,options.RarityOdds));
        }
    }
    static void Postfix(RewardsSet __instance,ref Task __result){if(__instance.Player.Character is RinContractCharacter&&(__instance.Room is CombatRoom||GenericCompatibility.Enabled(__instance.Player)&&__instance.Room is TreasureRoom))__result=Save(__result,__instance);}
    static async Task Save(Task original,RewardsSet set)
    {
        await original;var p=set.Player;var s=ContractSave.Get(p);
        if(s.RoomRewards?.RoomIdentity==ContractSave.RoomKey(p))return;
        s.RoomRewards=new(){RoomIdentity=ContractSave.RoomKey(p)};
        foreach(var reward in set.Rewards){var native=reward.ToSerializable();
            // Freeze already-populated native item identities. This neither enables
            // D1 potion/relic drops nor changes their native acquisition callbacks.
            if(reward is PotionReward {Potion:{} potion})native.PredeterminedModelId=potion.Id;
            if(reward is RelicReward {Relic:{} relic})native.PredeterminedModelId=relic.Id;
            var entry=new RoomRewardEntry{Native=native,DualIndex=(reward as DualCardReward)?.State.RewardIndex,BossIndex=(reward as ContractBossCardReward)?.State.RewardIndex};
            if(reward is SpecialCardReward&&AccessTools.Field(typeof(SpecialCardReward),"_card").GetValue(reward) is CardModel card&&NativePermanentCards.Get(card) is {} owner)
            {entry.NativeCardOwner=owner.Member;entry.NativeCardInstance=owner.InstanceId;}
            s.RoomRewards.Entries.Add(entry);RunRewardLedger.Bind(reward,entry);}
        await ContractSave.Checkpoint(p,"ROOM_REWARDS_CREATED");
    }
}
[HarmonyPatch(typeof(Reward),nameof(Reward.SelectUnsynchronized))]
public static class ContractRewardTakenHook
{
    static void Postfix(Reward __instance,ref Task<bool> __result)
    {
        if(__instance.Player.Character is RinContractCharacter)__result=After(__result,__instance);
    }
    static async Task<bool> After(Task<bool> original,Reward reward){var task=original;await RunRewardLedger.AfterSelect(task,reward);return await task;}
}
[HarmonyPatch(typeof(RewardsSet),nameof(RewardsSet.Offer))]
public static class ResumeDualRewardHook
{
    static RunState? resumeRun;
    public static void Request(Player p)
    {
        // Fresh victories always show loot. Only saved in-progress selections
        // resume automatically; public Master-pending loot stays in its container.
        var s=ContractSave.Get(p);
        resumeRun=s.DualRewards.Any(r=>!r.Complete&&(r.RinDecided||!PublicUiMode.IsPublic(p)))?(RunState)p.RunState:null;
    }
    static void Postfix(RewardsSet __instance)
    {
        if(MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn)return;
        if(!ReferenceEquals(resumeRun,__instance.Player.RunState))return;
        if(__instance.Rewards.OfType<DualCardReward>().FirstOrDefault(r=>!r.State.Complete) is not {} reward)return;
        resumeRun=null;_=TaskHelper.RunSafely(Open(__instance,reward));
    }
    static async Task Open(RewardsSet set,DualCardReward reward)
    {
        // Offer sets up the native rewards synchronizer after its generation/checkpoint await.
        while(set.Id<0)await MegaCrit.Sts2.Core.Nodes.NGame.Instance!.ToSignal(MegaCrit.Sts2.Core.Nodes.NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
        await MegaCrit.Sts2.Core.Nodes.NGame.Instance!.ToSignal(MegaCrit.Sts2.Core.Nodes.NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
        var button=Descendants(MegaCrit.Sts2.Core.Nodes.NGame.Instance).OfType<MegaCrit.Sts2.Core.Nodes.Rewards.NRewardButton>().First(b=>b.Reward==reward);
        // Keep the native button's claim/removal callback and the native reward synchronizer.
        await (Task)AccessTools.Method(typeof(MegaCrit.Sts2.Core.Nodes.Rewards.NRewardButton),"GetReward").Invoke(button,null)!;
    }
    static IEnumerable<Node> Descendants(Node root){foreach(var n in root.GetChildren()){yield return n;foreach(var child in Descendants(n))yield return child;}}
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.ProceedFromTerminalRewardsScreen))]
public static class D1ProceedHook
{
    static bool Prefix(RunManager __instance,ref Task __result)
    {
        if(FullActRoomSpine.NativeProceed.Value)return true;
        var run=__instance.DebugOnlyGetState();var p=run?.Players.FirstOrDefault(p=>p.Character is RinContractCharacter);if(p==null)return true;
        if(ContractTravelGate.Pending(p)){__result=Task.CompletedTask;return false;}
        if(FullActRoomSpine.Enabled(p)){__result=FullActRoomSpine.Proceed(__instance,p);return false;}
        if(D1Run.IsQa(p)&&run!.CurrentActIndex==0&&run.ActFloor==3){__result=Probe(__instance,p);return false;}
        if(D1Run.IsQa(p)){__result=CompleteRoom(__instance,p);return false;}
        if(RunEconomy.Enabled(p)){__result=CompleteRoom(__instance,p);return false;}
        return true;
    }
    static async Task Probe(RunManager manager,Player p)
    {
        if(ContractSave.Get(p).RoomRewards is {} ledger)foreach(var entry in ledger.Entries)entry.Resolved=true;
        await manager.EnterAct(1);ContractSave.Log(p,"ACT_TRANSITION",new{act=1});await ContractSave.Checkpoint(p,"AFTER_ACT_TRANSITION");NMapScreen.Instance?.SetTravelEnabled(true);NMapScreen.Instance?.Open();
    }
    static async Task CompleteRoom(RunManager manager,Player p)
    {
        if(ContractSave.Get(p).RoomRewards is {} ledger)foreach(var entry in ledger.Entries)entry.Resolved=true;
        await ContractSave.Checkpoint(p,"ON_MAP_AFTER_ROOM");NMapScreen.Instance?.SetTravelEnabled(true);NMapScreen.Instance?.Open();
    }
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Hooks.Hook),nameof(MegaCrit.Sts2.Core.Hooks.Hook.ShouldProceedToNextMapPoint))]
public static class DualRewardProceedAvailability
{
    static void Postfix(IRunState runState,ref bool __result){if(runState.Players.Any(p=>p.Character is RinContractCharacter&&ContractTravelGate.Pending(p)))__result=false;}
}
