using MegaCrit.Sts2.Core.Nodes.Screens.MainMenu;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
namespace RinArcherCore;
[HarmonyPatch(typeof(NMainMenu),"DisplayLoadSaveError")]
public static class GenericMigrationUi
{
    static bool Prefix()
    {
        var notice=GenericSavedRunSignature.ConsumeNotice();if(notice==null)return true;
        CoreHud.ClearLauncher();
        var popup=NErrorPopup.Create("Rin / Archer · 存档版本不符",GenericSavedRunSignature.MigrationDisplayNotice??notice,showReportBugButton:false)!;
        popup.SetMeta("compat_migration_required",true);
        NModalContainer.Instance!.Add(popup);NModalContainer.Instance.ShowBackstop();return false;
    }
}
