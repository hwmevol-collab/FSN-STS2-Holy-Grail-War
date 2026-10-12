using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Screens.MainMenu;
using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;
using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.Saves;
namespace RinArcherCore;

public static class ReleaseCompatibilityGate
{
    public static bool Compatible {get;private set;}
    public static string Actual {get;private set;}="unknown";
    public static string Reason {get;private set;}="";
    public static void Check()
    {
        Compatible=false;Actual="unknown";Reason="";
        try{Actual=VanillaCompatibilityRegistry.InstalledSignature().GameVersion;Compatible=GenericCompatibility.Registry.IsValid;Reason=GenericCompatibility.Registry.FailureReason;}
        catch(Exception e) when(e is not OutOfMemoryException)
        {
            Reason=e.GetType().Name+": "+e.Message;
            GD.PrintErr("[RIN_ARCHER] COMPATIBILITY_CHECK_FAILED "+e);
        }
        GD.Print("[RIN_ARCHER] COMPATIBILITY_GATE "+System.Text.Json.JsonSerializer.Serialize(new{Compatible,Actual,Reason}));
    }
    public static void Show()
    {
        bool zh=LocManager.Instance.Language=="zhs";
        string title=zh?"凛 / Archer：游戏版本不兼容":"Rin / Archer: incompatible game version";
        string body=zh?$"当前游戏：{Actual}\n支持版本：v0.107.1（已验证构建 59260271）\n\n当前构建未通过兼容检查，凛 / Archer 的新游戏和继续游戏已暂停。请更新 MOD 至支持当前游戏的版本，或使用已验证的游戏及依赖版本。\n\n原存档未修改。\n诊断：{Reason}":$"Current game: {Actual}\nSupported: v0.107.1 (verified build 59260271)\n\nThis build failed the compatibility check. Rin / Archer new runs and Continue are blocked. Update the mod for your game version, or use the verified game and dependency versions.\n\nExisting saves have not been modified.\nDiagnostic: {Reason}";
        var popup=NErrorPopup.Create(title,body,showReportBugButton:false);
        if(popup!=null){NModalContainer.Instance?.Add(popup);NModalContainer.Instance?.ShowBackstop();}
    }
}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class ReleaseSelectionGate
{
    [HarmonyPriority(Priority.First)]
    static bool Prefix(CharacterModel characterModel)
    {if(ReleaseCompatibilityGate.Compatible||characterModel is not RinContractCharacter)return true;ReleaseCompatibilityGate.Show();return false;}
}
[HarmonyPatch(typeof(NCharacterSelectScreen),"OnEmbarkPressed")]
public static class ReleaseEmbarkGate
{
    [HarmonyPriority(Priority.First)]
    static bool Prefix(NCharacterSelectScreen __instance)
    {if(ReleaseCompatibilityGate.Compatible||__instance.Lobby.LocalPlayer.character is not RinContractCharacter)return true;ReleaseCompatibilityGate.Show();return false;}
}
[HarmonyPatch(typeof(NMainMenu),"OnContinueButtonPressed")]
public static class ReleaseContinueGate
{
    [HarmonyPriority(Priority.First)]
    static bool Prefix()
    {
        if(ReleaseCompatibilityGate.Compatible)return true;
        var saved=SaveManager.Instance.LoadRunSave();
        if(saved.SaveData?.Players.Any(p=>p.CharacterId==ModelDb.Character<RinContractCharacter>().Id)!=true)return true;
        ReleaseCompatibilityGate.Show();return false;
    }
}
[HarmonyPatch(typeof(NGame),"LoadMainMenu")]
public static class ReleaseVersionNotice
{
    static bool shown;
    static void Postfix(ref Task __result){if(!ReleaseCompatibilityGate.Compatible&&!shown){shown=true;__result=After(__result);}}
    static async Task After(Task original){await original;ReleaseCompatibilityGate.Show();}
}
