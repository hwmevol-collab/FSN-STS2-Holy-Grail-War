using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.Models.Acts;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
public sealed class E2AActMap:ActMap
{
    protected override MapPoint?[,] Grid{get;}
    public override MapPoint StartingMapPoint{get;}=new(3,0){PointType=MapPointType.Monster};
    public override MapPoint BossMapPoint{get;}
    public E2AActMap(int rows,bool optionalServices=false)
    {
        Grid=new MapPoint?[7,rows];BossMapPoint=new(3,rows){PointType=MapPointType.Boss};
        MapPoint previous=StartingMapPoint;
        MapPointType[] route=[MapPointType.Monster,MapPointType.Treasure,MapPointType.Monster,MapPointType.RestSite,MapPointType.Shop,MapPointType.Monster];
        for(int row=1;row<=route.Length;row++){var point=new MapPoint(3,row){PointType=route[row-1]};Grid[3,row]=point;previous.AddChildPoint(point);previous=point;}
        if(optionalServices)
        {
            // A closed fixed-reward/budget source cannot strand the short route.
            Grid[3,1]!.AddChildPoint(Grid[3,3]!);
            Grid[3,3]!.AddChildPoint(Grid[3,6]!);
            Grid[3,4]!.AddChildPoint(Grid[3,6]!);
        }
        startMapPoints.Add(Grid[3,1]!);
    }
}
public static class E2ARun
{
    public const string Flag="QA_E2A_GENERIC_COMPATIBILITY";
    public static bool Creating{get;private set;}
    public static bool IsQa(RunState? run)=>run?.Players.Any(p=>p.Character is RinContractCharacter&&ContractSave.Get(p).RunFlags.GetValueOrDefault(Flag))==true;
    public static async Task Start(string seed="RINARCHERE2A")
    {
        if(!OS.GetUserDataDir().Contains("RinArcherE2AAmended-20261009"))throw new InvalidOperationException("E2A candidate route requires isolated QA profile");
        CoreHud.ClearLauncher();TestMode.IsOn=false;
        foreach(string ftue in new[]{"combat_rules_ftue","merchant_ftue","rest_site_ftue","obtain_relic_ftue","treasure_ftue","potion_ftue","obtain_potion_ftue","map_select_ftue"})SaveManager.Instance.MarkFtueAsComplete(ftue);
        Creating=true;
        try
        {
            // QA-only native unlock fixture. The native first-run treasure path
            // has a fixed Custom Gorget and is separately tested as unavailable;
            // it must never be silently substituted with a compatible relic.
            var run=RunState.CreateForNewRun([Player.CreateForNewRun<RinContractCharacter>(MegaCrit.Sts2.Core.Unlocks.UnlockState.all,1)],new ActModel[]{ModelDb.Act<Overgrowth>(),ModelDb.Act<Hive>(),ModelDb.Act<Glory>()}.Select(a=>a.ToMutable()).ToList(),[],GameMode.Standard,0,seed);
            RunManager.Instance.SetUpNewSingleplayer(run,true,null);await (Task)AccessTools.Method(typeof(NGame),"StartRun").Invoke(NGame.Instance,[run])!;
            var p=run.Players[0];await PlayerCmd.GainGold(700,p);await ContractSave.Checkpoint(p,"E2A_CONTROLLED_ROUTE_ON_MAP");
            NMapScreen.Instance?.SetTravelEnabled(true);NMapScreen.Instance?.Open();
        }
        finally{Creating=false;}
    }
}
[HarmonyPatch(typeof(RunManager),"InitializeNewRun")]
public static class E2AControlledRunInitialization
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(RunManager __instance)
    {
        if(!E2ARun.Creating)return;
        foreach(var p in __instance.DebugOnlyGetState()!.Players.Where(p=>p.Character is RinContractCharacter))
        {
            var s=ContractSave.Get(p);s.RunFlags[E2ARun.Flag]=true;s.RunFlags[PublicUiMode.Flag]=true;((RunState)p.RunState).ExtraFields.StartedWithNeow=false;
            GenericCompatibility.EnableIsolated(p,GenericCompatibility.Registry.Entries.Where(e=>e.Classification is "NATIVE_SAFE" or "GENERIC_ADAPTER").Select(e=>e.ContentId));
        }
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.GenerateMap))]
public static class E2AControlledMap
{
    static void Postfix(RunManager __instance,ref Task __result){if(E2ARun.IsQa(__instance.DebugOnlyGetState()))__result=After(__result,__instance);}
    static async Task After(Task original,RunManager manager)
    {
        await original;var run=manager.DebugOnlyGetState()!;
        if(run.Map is not SavedActMap)run.Map=new E2AActMap(run.Map!.GetRowCount());
        NMapScreen.Instance?.SetMap(run.Map,run.Rng.Seed,true);NMapScreen.Instance?.SetTravelEnabled(true);
    }
}
[HarmonyPatch(typeof(RunManager),"CreateRoom")]
public static class E2AControlledCombat
{
    static bool Prefix(RunManager __instance,RoomType roomType,ref AbstractRoom __result)
    {
        var run=__instance.DebugOnlyGetState();if(!E2ARun.IsQa(run)||roomType!=RoomType.Monster)return true;
        __result=new CombatRoom(ModelDb.Encounter<QaD1Normal>().ToMutable(),run);return false;
    }
}
