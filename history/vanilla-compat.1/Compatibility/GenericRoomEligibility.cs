using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
namespace RinArcherCore;

public static class RoomEligibilityResolver
{
    public static bool IsEligible(Player p,string id,string source,bool nativeAllowed)
    {
        if(FullActRoomSpine.Enabled(p)&&FullActRoomSpine.IsDispatchDomain(id))
            return nativeAllowed&&FullActRoomSpine.DispatchReady(p,id);
        if(!GenericCompatibility.Registry.IsRoomEligible(id,CompatibilityCandidateResolver.Context(p,source,nativeAllowed)))return false;
        if(!GenericCompatibility.Enabled(p))return p.Character is not RinContractCharacter;
        string name=id.Split('.').Last();
        try
        {
            if(name=="Shop"&&!GenericMerchantStock.CompleteBudget(p))return false;
            if(name=="Treasure")GenericTreasureSource.ValidateBudget(p);
            return true;
        }
        catch(CompatibilitySourceUnavailableException){return false;}
    }
    public static bool MapPoint(Player p,MapPointType type,bool nativeAllowed=true)
        =>IsEligible(p,"MapPointType."+type,"NATIVE_MAP_CANDIDATE",nativeAllowed);
}
[HarmonyPatch(typeof(NMapPoint),"set_State")]
public static class GenericMapSourceBeforePresentation
{
    static void Postfix(NMapPoint __instance)
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);
        if(p!=null&&__instance.State==MapPointState.Travelable&&!RoomEligibilityResolver.MapPoint(p,__instance.Point.PointType))
            __instance.State=MapPointState.Untravelable;
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.EnterMapCoord))]
public static class GenericMapSourceBeforeVisit
{
    [HarmonyPriority(Priority.First)]
    static bool Prefix(RunManager __instance,MapCoord coord,ref Task __result)
    {
        var run=__instance.DebugOnlyGetState();var p=run?.Players.FirstOrDefault(GenericCompatibility.Enabled);
        if(p==null)return true;
        if(run!.Map?.GetPoint(coord) is {} point&&RoomEligibilityResolver.MapPoint(p,point.PointType))return true;
        __result=Task.CompletedTask;return false;
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.EnterMapCoordDebug))]
public static class GenericDebugSourceBeforeVisit
{
    static bool Prefix(RunManager __instance,RoomType roomType,MapPointType pointType,ref Task __result)
    {
        var p=__instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p==null)return true;
        bool eligible=RoomEligibilityResolver.IsEligible(p,"RoomType."+roomType,"NATIVE_DEBUG_ACQUISITION_SOURCE",true)
            &&(pointType==MapPointType.Unassigned||RoomEligibilityResolver.MapPoint(p,pointType));
        if(eligible)return true;__result=Task.FromException(new CompatibilitySourceUnavailableException("Room source unavailable before visit/presentation: "+roomType));return false;
    }
}
