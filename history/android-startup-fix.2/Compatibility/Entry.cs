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
        ReleaseCompatibilityGate.Check();
        if(!ReleaseCompatibilityGate.Compatible)
        {
            var gate=new Harmony("Murasame.RinArcherCore.CompatibilityNotice");
            gate.CreateClassProcessor(typeof(ReleaseEmbarkGate)).Patch();
            gate.CreateClassProcessor(typeof(ReleaseSelectionGate)).Patch();
            gate.CreateClassProcessor(typeof(ReleaseContinueGate)).Patch();
            gate.CreateClassProcessor(typeof(ReleaseVersionNotice)).Patch();
            GD.Print("[RIN_ARCHER] Disabled incompatible build: "+ReleaseCompatibilityGate.Reason);
            return;
        }
        CardBanks.Register();
        ContractSave.Register();
        new Harmony("Murasame.RinArcherCore").PatchAll(Assembly.GetExecutingAssembly());
        GD.Print("[RIN_ARCHER] BOOT: game="+ReleaseCompatibilityGate.Actual+" compatibility=PASS");
    }
}
[HarmonyPatch(typeof(OneTimeInitialization), nameof(OneTimeInitialization.ExecuteDeferred))]
public static class BootProbe
{
    static void Postfix()
    {
        GD.Print("[RIN_ARCHER] GODOT_VERSION=" + Engine.GetVersionInfo()["string"]);

    }
}
