using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.Models.Acts;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.Helpers;
using BaseLib.Patches.Content;
namespace RinArcherCore;
public sealed class QaD1Normal:EncounterModel,ICustomModel,ILocalizationProvider
{
    public List<(string,string)> Localization=>[("title","D1 普通契约验收"),("loss","D1 普通契约验收中败北")];
    public QaD1Normal(){CustomContentDictionary.RegisterType(GetType());}
    public override RoomType RoomType=>RoomType.Monster;
    public override bool IsDebugEncounter=>true;
    public override bool ShouldGiveRewards=>true;
    public override IEnumerable<MonsterModel> AllPossibleMonsters=>[ModelDb.Monster<QaMaster>(),ModelDb.Monster<QaServant>()];
    protected override IReadOnlyList<(MonsterModel,string?)> GenerateMonsters()=>[(ModelDb.Monster<QaMaster>().ToMutable(),null),(ModelDb.Monster<QaServant>().ToMutable(),null)];
}
public sealed class QaD1Elite:EncounterModel,ICustomModel,ILocalizationProvider
{
    public List<(string,string)> Localization=>[("title","D1 精英路径验收"),("loss","D1 精英路径验收中败北")];
    public QaD1Elite(){CustomContentDictionary.RegisterType(GetType());}
    public override RoomType RoomType=>RoomType.Elite;
    public override bool IsDebugEncounter=>true;
    public override bool ShouldGiveRewards=>true;
    public override IEnumerable<MonsterModel> AllPossibleMonsters=>[ModelDb.Monster<QaMaster>(),ModelDb.Monster<QaServant>()];
    protected override IReadOnlyList<(MonsterModel,string?)> GenerateMonsters()=>[(ModelDb.Monster<QaMaster>().ToMutable(),null),(ModelDb.Monster<QaServant>().ToMutable(),null)];
}
public sealed class D1ActMap:ActMap
{
    protected override MapPoint?[,] Grid{get;}=new MapPoint?[7,3];
    public override MapPoint StartingMapPoint{get;}=new(3,-1){PointType=MapPointType.Monster};
    public override MapPoint BossMapPoint{get;}=new(3,3){PointType=MapPointType.Boss};
    public D1ActMap(int act)
    {
        MapPoint last=StartingMapPoint;
        for(int row=0;row<3;row++){var point=new MapPoint(3,row){PointType=act==0&&row==2?MapPointType.Elite:MapPointType.Monster};Grid[3,row]=point;last.AddChildPoint(point);last=point;}
        startMapPoints.Add(Grid[3,0]!);
        // The detached boss is a native map anchor, never a playable D1 destination.
    }
}
public static class D1Run
{
    public static bool Creating;
    public static bool IsQa(Player p)=>p.Character is RinContractCharacter&&ContractSave.Get(p).RunFlags.GetValueOrDefault("QA_D1_RUN");
    public static bool IsQa(RunState? run)=>run!=null&&run.Players.Any(IsQa);
    public static async Task Start(string seed="RINARCHERD1")
    {
        var game=NGame.Instance!;CoreHud.ClearLauncher();NModalContainer.Instance?.Clear();MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn=false;
        SaveManager.Instance.MarkFtueAsComplete("combat_rules_ftue");Creating=true;
        try
        {
            var run=await game.StartNewSingleplayerRun(ModelDb.Character<RinContractCharacter>(),true,[ModelDb.Act<Overgrowth>(),ModelDb.Act<Hive>(),ModelDb.Act<Glory>()],[],seed,GameMode.Standard);
            await ContractSave.Checkpoint(run.Players[0],"ON_MAP");NMapScreen.Instance?.SetTravelEnabled(true);NMapScreen.Instance?.Open();
        }
        finally{Creating=false;}
    }
    public static void AttachLauncher(CanvasLayer layer)
    {
        var button=new Button{Text="Rin / Archer · D1 Run Integration",Position=new(870,585),CustomMinimumSize=new(395,48)};layer.AddChild(button);
        button.Pressed+=()=>{layer.QueueFree();TaskHelper.RunSafely(Start());};
    }
}
