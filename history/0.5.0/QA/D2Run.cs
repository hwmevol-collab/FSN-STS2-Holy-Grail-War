using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.Models.Acts;
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.Helpers;
namespace RinArcherCore;
public sealed class D2ActMap:ActMap
{
    protected override MapPoint?[,] Grid{get;}
    public override MapPoint StartingMapPoint{get;}=new(3,0){PointType=MapPointType.Monster};
    public override MapPoint BossMapPoint{get;}
    public D2ActMap(int rows)
    {
        if(rows<7)throw new ArgumentOutOfRangeException(nameof(rows));Grid=new MapPoint?[7,rows];BossMapPoint=new(3,rows){PointType=MapPointType.Boss};
        MapPoint last=StartingMapPoint;
        MapPointType[] types=[MapPointType.RestSite,MapPointType.Monster,MapPointType.Shop,MapPointType.Monster,MapPointType.Shop];
        for(int row=1;row<=types.Length;row++){var point=new MapPoint(3,row){PointType=types[row-1]};Grid[3,row]=point;last.AddChildPoint(point);last=point;}
        startMapPoints.Add(Grid[3,1]!);
    }
}
public static class D2Run
{
    public static bool Creating;
    public static bool CreatingPublicUi=true;
    public static bool IsQa(RunState? run)=>run!=null&&run.Players.Any(RunEconomy.Enabled);
    public static async Task Start(string seed="RINARCHERD2",bool publicUi=true)
    {
        CoreHud.ClearLauncher();NModalContainer.Instance?.Clear();MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn=false;
        foreach(var ftue in new[]{"combat_rules_ftue","merchant_ftue","rest_site_ftue"})SaveManager.Instance.MarkFtueAsComplete(ftue);
        Creating=true;CreatingPublicUi=publicUi;
        try
        {
            var run=await NGame.Instance!.StartNewSingleplayerRun(ModelDb.Character<RinContractCharacter>(),true,[ModelDb.Act<Overgrowth>(),ModelDb.Act<Hive>(),ModelDb.Act<Glory>()],[],seed,GameMode.Standard);
            var p=run.Players[0];await PlayerCmd.GainGold(500,p);
            ContractSave.Log(p,"QA_GOLD_INJECTION",new{amount=500,NOT_PUBLIC_BALANCE=true});await ContractSave.Checkpoint(p,"D2_ON_MAP");
            NMapScreen.Instance?.SetTravelEnabled(true);NMapScreen.Instance?.Open();
        }
        finally{Creating=false;CreatingPublicUi=true;}
    }
    public static void AttachLauncher(CanvasLayer layer)
    {
        var b=new Button{Text="Rin / Archer · D2 Campfire / Merchant",Position=new(870,530),CustomMinimumSize=new(395,48)};layer.AddChild(b);
        b.Pressed+=()=>{layer.QueueFree();TaskHelper.RunSafely(Start());};
    }
}
