using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Cards.Holders;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.addons.mega_text;
namespace RinArcherCore;

// Presentation models only: no auto-registration in pools/library, no run/combat
// CreateCard, pile, instance ID, CardSelectCmd, OnChosen, or card-play transaction.
public abstract class StartingMemberChoice : CustomCardModel
{
    protected StartingMemberChoice():base(0,CardType.Skill,CardRarity.Basic,TargetType.None,false,autoAdd:false){}
    public abstract string Member{get;}
    public override string Title=>Member==RunEconomy.Rin?FsnLoc.Text("UI_260D2B21B76B"):FsnLoc.Text("ARCHER_ROLE");
    public string ChoiceDescription=>Member==RunEconomy.Rin?FsnLoc.Text("UI_F9FA8BB46C6F"):FsnLoc.Text("UI_CBAC323222F7");
    public override CardPoolModel Pool=>ModelDb.CardPool<RinArcherPool>();
    public override Texture2D? CustomPortrait=>PlaceholderVisuals.CardTexture(Member==RunEconomy.Rin);
    public override List<(string,string)> Localization=>[("title",Title),("description",ChoiceDescription),("selectionScreenPrompt",FsnLoc.Text("UI_BA303B7B3CF5"))];
    protected override bool IsPlayable=>false;
    public override int MaxUpgradeLevel=>0;
    protected override Task OnPlay(PlayerChoiceContext choiceContext,CardPlay play)=>throw new InvalidOperationException("Presentation choice must never be played");
}
public sealed class StartingMasterChoice:StartingMemberChoice{public override string Member=>RunEconomy.Rin;}
public sealed class StartingServantChoice:StartingMemberChoice{public override string Member=>RunEconomy.Archer;}

public static class StartingActiveChoiceUi
{
    public static NChooseACardSelectionScreen? Current{get;private set;}
    public static bool IsPresentation(NChooseACardSelectionScreen screen)
        =>AccessTools.Field(typeof(NChooseACardSelectionScreen),"_cards").GetValue(screen) is IReadOnlyList<CardModel> cards&&cards.Count==2&&cards.All(c=>c is StartingMemberChoice);
    public static async Task<string> Choose(ContractRuntime contract)
    {
        var cards=new CardModel[]{ModelDb.Card<StartingMasterChoice>().ToMutable(),ModelDb.Card<StartingServantChoice>().ToMutable()};
        foreach(var card in cards)card.Owner=contract.Player;
        var screen=NChooseACardSelectionScreen.ShowScreen(cards,false)??throw new InvalidOperationException("Native starting choice scene unavailable");
        Current=screen;
        screen.GetNode<NCommonBanner>("Banner").label.SetTextAutoSize(FsnLoc.Text("UI_4686EC1D0004"));
        foreach(var holder in screen.GetNode<Control>("CardRow").GetChildren().OfType<NGridCardHolder>())
        {
            var card=(StartingMemberChoice)holder.CardModel;
            var view=holder.CardNode??throw new InvalidOperationException("Native starting choice card view missing");
            view.GetNode<MegaRichTextLabel>("%DescriptionLabel").Text=card.ChoiceDescription;
            view.GetNode<MegaLabel>("%TypeLabel").Text=FsnLoc.Text("UI_30D8633555AA");
            foreach(var name in new[]{"%EnergyIcon","%EnergyLabel","%UnplayableEnergyIcon","%StarIcon","%StarLabel"})
                view.GetNodeOrNull<CanvasItem>(name)?.Hide();
            view.SetMeta("ContractChoiceHiddenCosts",true);
        }
        if(!GameApi.IsDirectionalNavigation)screen.GetViewport().GuiReleaseFocus();
        try
        {
            var selected=(await screen.CardsSelected()).Single() as StartingMemberChoice??throw new InvalidOperationException("Invalid starting choice presentation");
            return selected.Member;
        }
        finally{if(ReferenceEquals(Current,screen))Current=null;}
    }
}
[HarmonyPatch(typeof(NChooseACardSelectionScreen),"get_DefaultFocusedControl")]
public static class StartingChoiceNativeFocus
{
    static void Postfix(NChooseACardSelectionScreen __instance,ref Control? __result)
    {if(StartingActiveChoiceUi.IsPresentation(__instance)&&!GameApi.IsDirectionalNavigation)__result=null;}
}
// Native SelectHolder uses SetResult, so a second release in the same frame must
// not execute it again. This guard is scoped to these two transient UI cards.
[HarmonyPatch(typeof(NChooseACardSelectionScreen),"SelectHolder")]
public static class StartingChoiceSingleCommit
{
    static bool Prefix(NChooseACardSelectionScreen __instance,bool ____screenComplete)
        =>!StartingActiveChoiceUi.IsPresentation(__instance)||!____screenComplete;
}

// NCard.Model itself calls this when rendering a normal card. The native scene
// stays intact, but these presentation-only models must never become discovered
// gameplay cards in either the player run state or progress/history save.
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Saves.SaveManager),nameof(MegaCrit.Sts2.Core.Saves.SaveManager.MarkCardAsSeen))]
public static class StartingChoiceNoDiscovery
{
    static bool Prefix(CardModel card)=>card is not StartingMemberChoice;
}

// NCard is pooled. Native cost refresh updates text/icons, but never restores
// the label visibility hidden by this presentation. Restore only our own state
// when the same view is rebound to an ordinary gameplay card.
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Nodes.Cards.NCard),"UpdateEnergyCostVisuals")]
public static class StartingChoicePooledCostRestore
{
    static void Prefix(MegaCrit.Sts2.Core.Nodes.Cards.NCard __instance)
    {
        if(__instance.Model is StartingMemberChoice||!__instance.HasMeta("ContractChoiceHiddenCosts"))return;
        __instance.GetNode<CanvasItem>("%EnergyLabel").Show();
        __instance.GetNode<CanvasItem>("%StarLabel").Show();
        __instance.RemoveMeta("ContractChoiceHiddenCosts");
    }
}
