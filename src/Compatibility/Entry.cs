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
        var harmony=new Harmony("Murasame.RinArcherCore");
        var selectors=new[]{typeof(VanillaPermanentBankLifetime),typeof(VanillaDeckGenericSelection),typeof(GenericNativeDeckSelection),typeof(VanillaEnchantmentSelection),typeof(VanillaTransformOwner)};
        // Patch small async command wrappers before compiling model MoveNext detours.
        foreach(var type in selectors)harmony.CreateClassProcessor(type).Patch();
        foreach(var type in Assembly.GetExecutingAssembly().GetTypes().Where(t=>!selectors.Contains(t)&&t.IsDefined(typeof(HarmonyPatch),false)))harmony.CreateClassProcessor(type).Patch();
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
