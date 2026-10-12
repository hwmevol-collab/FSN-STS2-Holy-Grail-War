using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.Core.Nodes.Screens.CardLibrary;
using MegaCrit.Sts2.Core.CardSelection;
using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Multiplayer;
using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.Nodes.Screens.Overlays;
using MegaCrit.Sts2.Core.Helpers;
namespace RinArcherCore;
public enum DeckServiceAction{Upgrade,Remove}
public static class EconomyNativeUi
{
    public static LocString Text(string text)
    {LocManager.Instance.GetTable("rest_site_ui").MergeWith(new Dictionary<string,string>{{"RIN_ARCHER_D2_TEXT","{Text}"}});var result=new LocString("rest_site_ui","RIN_ARCHER_D2_TEXT");result.Add("Text",text);return result;}
    public static NPopupYesNoButton Button(Control parent,string name,string text,Vector2 position,Action pressed,string hotkey="")
    {
        var template=NGenericPopup.Create()!;
        var button=(NPopupYesNoButton)template.GetNode<NPopupYesNoButton>("VerticalPopup/YesButton").Duplicate();template.Free();
        button.Name=name;button.FocusMode=Control.FocusModeEnum.All;button.FocusBehaviorRecursive=Control.FocusBehaviorRecursiveEnum.Enabled;
        button.SetMeta("rin_archer_d2_hotkey",hotkey);parent.AddChild(button);button.Position=position;button.SetText(text);button.Enable();
        button.Connect(NClickableControl.SignalName.Released,Callable.From<NButton>(_=>pressed()));return button;
    }
    public static async Task<bool> Confirm(string header,string body,string confirm)
    {
        var popup=NGenericPopup.Create()!;popup.Name="D2Confirmation";NModalContainer.Instance!.Add(popup);
        var task=popup.WaitForConfirmation(Text(body),Text(header),Text(FsnLoc.Text("UI_2CD0F3BE8738")),Text(confirm));
        popup.TreeExiting+=()=>{if(!task.IsCompleted)AccessTools.Field(typeof(NGenericPopup),"_confirmationCompletionSource").GetValue(popup).AsCompletion()?.TrySetResult(false);};
        return await task;
    }
    static TaskCompletionSource<bool>? AsCompletion(this object? value)=>value as TaskCompletionSource<bool>;
}
[HarmonyPatch(typeof(NPopupYesNoButton),"get_Hotkeys")]
public static class D2NativeButtonHotkeys
{
    static void Postfix(NPopupYesNoButton __instance,ref string[] __result)
    {if(__instance.HasMeta("rin_archer_d2_hotkey")){string key=__instance.GetMeta("rin_archer_d2_hotkey").AsString();__result=key.Length==0?[]:[key];}}
}
public static class DualDeckCardSelector
{
    public static NCardGridSelectionScreen? Current{get;private set;}
    public static string CurrentOwner{get;private set;}=RunEconomy.Rin;
    public static List<CardModel> Candidates(Player p,Func<CardModel,bool> candidatePredicate)=>RunEconomy.Permanent(p).Where(candidatePredicate).ToList();
    public static IReadOnlyList<CardModel> LegalPermanentUnion(Player p,Func<CardModel,bool> predicate)
    {
        var cards=Candidates(p,c=>RunEconomy.IsPermanent(p,c)&&predicate(c));
        if(cards.Select(NativePermanentCards.Instance).Distinct(StringComparer.Ordinal).Count()!=cards.Count)
            throw new InvalidOperationException("Duplicate permanent instances in random union");
        return cards;
    }
    public static IReadOnlyList<CardModel> RandomPermanentUnion(Player p,int count,Func<CardModel,bool> predicate,MegaCrit.Sts2.Core.Random.Rng rng)
    {
        var eligible=LegalPermanentUnion(p,predicate).ToList();
        if(count<0||eligible.Count<count)throw new InvalidOperationException("Insufficient complete permanent mutation budget");
        var result=new List<CardModel>();
        for(int i=0;i<count;i++){var chosen=eligible[rng.NextInt(eligible.Count)];eligible.Remove(chosen);result.Add(chosen);}
        return result;
    }
    // Both D2 services have one shared target. No dormant transform/duplicate gameplay is introduced.
    public static async Task<IReadOnlyList<CardModel>> Select(Player p,DeckServiceAction actionType,int targetCount,Func<CardModel,bool> candidatePredicate,bool allowCrossOwnerSelection,string confirmText,CardSelectorPrefs? nativePrefs=null)
    {
        if(targetCount<1)throw new ArgumentOutOfRangeException(nameof(targetCount));
        var all=Candidates(p,candidatePredicate);if(all.Count==0)return [];
        CurrentOwner=all.Any(c=>NativePermanentCards.Owner(c)==RunEconomy.Rin)?RunEconomy.Rin:RunEconomy.Archer;
        bool union=targetCount>1&&allowCrossOwnerSelection;
        List<CardModel> Cards(string owner)=>union?all:all.Where(c=>NativePermanentCards.Owner(c)==owner).ToList();
        var prefs=nativePrefs??new CardSelectorPrefs(EconomyNativeUi.Text(confirmText+FsnLoc.Format("UI_19533DE6D80E", targetCount)),targetCount){Cancelable=true,RequireManualConfirmation=true};
        NCardGridSelectionScreen screen;
        if(actionType==DeckServiceAction.Upgrade)screen=NDeckUpgradeSelectScreen.ShowScreen(Cards(CurrentOwner),prefs,p.RunState);
        else{screen=NDeckCardSelectScreen.Create(Cards(CurrentOwner),prefs);NOverlayStack.Instance!.Push(screen);}
        Current=screen;screen.SetMeta("rin_archer_d2_selector",true);screen.SetMeta("rin_archer_e2a_union_selector",union);
        screen.GetNode<NCardGrid>("%CardGrid").SetAnchorAndOffset(Side.Top,0,180);
        var tabs=new List<NPopupYesNoButton>();
        bool PreviewVisible()=>actionType==DeckServiceAction.Upgrade?screen.GetNode<Control>("%UpgradeSinglePreviewContainer").Visible:screen.GetNode<Control>("%PreviewContainer").Visible;
        void Switch(string owner)
        {
            if(PreviewVisible())return;CurrentOwner=owner;var cards=Cards(owner);
            AccessTools.Field(typeof(NCardGridSelectionScreen),"_cards").SetValue(screen,cards);
            screen.GetNode<NCardGrid>("%CardGrid").SetCards(cards,PileType.None,[SortingOrders.Ascending]);
            foreach(var tab in tabs)tab.SetText(((tab.Name=="D2RinTab"?FsnLoc.Text("RIN_ROLE"):FsnLoc.Text("ARCHER_ROLE"))+(tab.Name==(owner==RunEconomy.Rin?"D2RinTab":"D2ArcherTab")?"  ✓":"")));
        }
        tabs.Add(EconomyNativeUi.Button(screen,"D2RinTab",FsnLoc.Text("RIN_ROLE"),new(455,125),()=>Switch(RunEconomy.Rin),MegaInput.viewDeckAndTabLeft));
        tabs.Add(EconomyNativeUi.Button(screen,"D2ArcherTab",FsnLoc.Text("ARCHER_ROLE"),new(900,125),()=>Switch(RunEconomy.Archer),MegaInput.viewExhaustPileAndTabRight));
        foreach(var tab in tabs)tab.CustomMinimumSize=new(340,64);
        if(union)foreach(var tab in tabs){tab.Visible=false;tab.Disable();}
        Switch(CurrentOwner);
        try
        {
            var selected=(await screen.CardsSelected()).ToList();
            if(selected.Count==0)return [];
            if(selected.Count!=targetCount||selected.Any(c=>!all.Contains(c)||!RunEconomy.IsPermanent(p,c)||!candidatePredicate(c)))throw new InvalidOperationException("Dual selector target/instance validation failed");
            if(!allowCrossOwnerSelection&&selected.Select(c=>NativePermanentCards.Owner(c)).Distinct().Count()>1)throw new InvalidOperationException("Cross-owner selection forbidden");return selected;
        }
        catch(TaskCanceledException){return [];}
        finally{if(ReferenceEquals(Current,screen))Current=null;}
    }
}
[HarmonyPatch]
public static class D2SelectorPreviewTabs
{
    static IEnumerable<System.Reflection.MethodBase> TargetMethods()=>new[]{typeof(NDeckUpgradeSelectScreen),typeof(NDeckCardSelectScreen)}.SelectMany(t=>new[]{AccessTools.Method(t,"OnCardClicked"),AccessTools.Method(t,"CancelSelection")});
    static void Postfix(NCardGridSelectionScreen __instance)
    {
        if(!__instance.HasMeta("rin_archer_d2_selector"))return;
        bool preview=(__instance.HasMeta("rin_archer_e2a_union_selector")&&__instance.GetMeta("rin_archer_e2a_union_selector").AsBool())||(__instance is NDeckUpgradeSelectScreen?__instance.GetNode<Control>("%UpgradeSinglePreviewContainer").Visible:__instance.GetNode<Control>("%PreviewContainer").Visible);
        foreach(var name in new[]{"D2RinTab","D2ArcherTab"})if(__instance.GetNodeOrNull<NPopupYesNoButton>(name) is {} tab){tab.Visible=!preview;if(preview)tab.Disable();else tab.Enable();}
    }
}




