using MegaCrit.Sts2.Core.Nodes.Relics;
namespace FateStayNight;
[HarmonyPatch(typeof(NRelicInventory),"OnRelicClicked")]
public static class SealIconInputPatch{
    static bool Prefix(RelicModel model){if(model is not CommandSeals||Duo.For(model.Owner) is not {} d||d.Combat==null)return true;Art.ToggleSealChoices(d);return false;}
}
