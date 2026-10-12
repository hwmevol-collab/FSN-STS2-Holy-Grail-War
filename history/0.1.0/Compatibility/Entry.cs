using Godot;
using HarmonyLib;
using MegaCrit.Sts2.Core.Modding;
using MegaCrit.Sts2.Core.Helpers;
using System.Reflection;
namespace RinArcherCore;

[ModInitializer(nameof(Initialize))]
public static class Entry
{
    public static void Initialize()
    {
        CardBanks.Register();
        ContractSave.Register();
        new Harmony("Murasame.RinArcherCore").PatchAll(Assembly.GetExecutingAssembly());
        GD.Print("[RIN_ARCHER] BOOT: game=0.107.1 BaseLib=3.4.7 RitsuLib=0.6.6-compat-0.107.1");
    }
}
[HarmonyPatch(typeof(OneTimeInitialization), nameof(OneTimeInitialization.ExecuteDeferred))]
public static class BootProbe
{
    static void Postfix()
    {
        GD.Print("[RIN_ARCHER] GODOT_VERSION=" + Engine.GetVersionInfo()["string"]);
        System.IO.File.WriteAllText(System.IO.Path.Combine(System.IO.Path.GetDirectoryName(OS.GetExecutablePath())!, "rin-archer-boot.txt"),
            "BOOT_PASS\nGODOT=" + Engine.GetVersionInfo()["string"]);
    }
}
