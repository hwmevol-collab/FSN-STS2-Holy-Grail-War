using MegaCrit.Sts2.Core.Nodes.Screens;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Screens.CardLibrary;
namespace RinArcherCore;
// Native detail, upgrade toggle and sort controls continue to use real permanent instances.
public static class DualDeckBrowser
{
    public static string Owner(NDeckViewScreen screen)=>screen.HasMeta("contract_deck_owner")?screen.GetMeta("contract_deck_owner").AsString():RunEconomy.Rin;
    public static Player Player(NDeckViewScreen screen)=>(Player)AccessTools.Field(typeof(NDeckViewScreen),"_player").GetValue(screen)!;
    public static void Select(NDeckViewScreen screen,string owner)
    {
        screen.SetMeta("contract_deck_owner",owner);
        AccessTools.Field(typeof(NCardsViewScreen),"_cards").SetValue(screen,ContractSave.Deck(Player(screen),owner).Cards.ToList());
        AccessTools.Method(typeof(NDeckViewScreen),"DisplayCards").Invoke(screen,null);
        foreach(var id in new[]{RunEconomy.Rin,RunEconomy.Archer})
            screen.GetNode<NPopupYesNoButton>(id==RunEconomy.Rin?"ContractRinDeckTab":"ContractArcherDeckTab").SetText((id==RunEconomy.Rin?"凛":"Archer")+$" · {ContractSave.Deck(Player(screen),id).Cards.Count}"+(owner==id?"  ✓":""));
    }
    [HarmonyPatch(typeof(NDeckViewScreen),"_Ready")]
    static class Attach
    {
        static void Postfix(NDeckViewScreen __instance)
        {
            var s=__instance;var p=Player(s);if(p.Character is not RinContractCharacter)return;
            var rin=EconomyNativeUi.Button(s,"ContractRinDeckTab","凛",new(725,105),()=>Select(s,RunEconomy.Rin),MegaCrit.Sts2.Core.ControllerInput.MegaInput.viewDeckAndTabLeft);
            var archer=EconomyNativeUi.Button(s,"ContractArcherDeckTab","Archer",new(965,105),()=>Select(s,RunEconomy.Archer),MegaCrit.Sts2.Core.ControllerInput.MegaInput.viewExhaustPileAndTabRight);
            foreach(var b in new[]{rin,archer}){b.CustomMinimumSize=new(210,48);b.Size=new(210,48);}
            var reserve=ContractSave.Deck(p,RunEconomy.Archer);
            void Refresh(){if(GodotObject.IsInstanceValid(s)&&s.IsInsideTree())Select(s,Owner(s));}
            reserve.ContentsChanged+=Refresh;s.TreeExiting+=()=>reserve.ContentsChanged-=Refresh;
            Select(s,RunEconomy.Rin);
        }
    }
    [HarmonyPatch(typeof(NDeckViewScreen),"OnPileContentsChanged")]
    static class RefreshNative
    {
        static bool Prefix(NDeckViewScreen __instance)
        {if(Player(__instance).Character is not RinContractCharacter)return true;Select(__instance,Owner(__instance));return false;}
    }
}
