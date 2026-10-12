using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Cards.Holders;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.Nodes.Screens.Overlays;
using MegaCrit.Sts2.Core.Entities.CardRewardAlternatives;
using MegaCrit.Sts2.Core.Entities.Rewards;
using MegaCrit.Sts2.Core.TestSupport;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.addons.mega_text;
namespace RinArcherCore;
public readonly record struct DualRewardDecision(string? CardId,bool Cancelled=false);
public static class DualRewardUi
{
    public static Action<string?>? Pending;
    public static string? CurrentOwner;
    public static IReadOnlyList<RewardOfferCard> CurrentOffer=[];
    public static bool Committing{get;private set;}
    public static NCardRewardSelectionScreen? NativeScreen{get;private set;}
    public static NCardRewardAlternativeButton? SaveExitButton{get;private set;}
    static Action? closeCommitted;
    public static void CloseCommitted(){var close=closeCommitted;closeCommitted=null;close?.Invoke();}
    public static readonly Queue<string?> TestChoices=[];
    public static async Task<DualRewardDecision> Ask(Player p,DualRewardState reward,string owner)
    {
        if(TestMode.IsOn)return new(TestChoices.Count>0?TestChoices.Dequeue():null);
        if(NativeScreen!=null)throw new InvalidOperationException("Dual reward selection already open");
        var offer=reward.Offer(owner).ToArray();
        // Previews never enter a permanent deck; acquisition stays in the existing transaction.
        var options=offer.Select(o=>new CardCreationResult(p.RunState.CreateCard(AlphaRewardRegistry.Card(o.CardId),p))).ToArray();
        bool qa=!PublicUiMode.IsPublic(p);
        var alternatives=new List<CardRewardAlternative>{new("Skip",PostAlternateCardRewardAction.EndSelectionAndDoNotCompleteReward)};
        if(qa)alternatives.Add(new("Skip",PostAlternateCardRewardAction.EndSelectionAndCompleteReward));
        var screen=NCardRewardSelectionScreen.ShowScreen(options,alternatives)!;
        NativeScreen=screen;CurrentOwner=owner;CurrentOffer=offer;
        var selection=screen.OptionSelected();
        var s=ContractSave.Get(p);bool rin=owner=="CHAR_RIN";
        screen.GetNode<NCommonBanner>("UI/Banner").label.SetTextAutoSize(FsnLoc.Format("UI_4B0F58DBB1AF", (rin?FsnLoc.Text("UI_D4C06B733FE9"):"2 / 2 · "+FsnLoc.Text("ARCHER_ROLE")), p.Creature.CurrentHp, p.Creature.MaxHp, s.ArcherHp, s.ArcherMaxHp));
        var buttons=screen.GetNode<Control>("UI/RewardAlternatives").GetChildren().OfType<NCardRewardAlternativeButton>().ToArray();
        SaveExitButton=qa?buttons[1]:null;
        if(SaveExitButton is {} saveExit){saveExit.Name="D1SaveExit";saveExit.GetNode<MegaLabel>("Label").SetTextAutoSize(FsnLoc.Text("UI_58ACEA9E7E2E"));}
        // Native alternatives have distinct hotkeys (cancel / tab-right).
        Action<string?> handler=id=>{
            if(selection.IsCompleted)return;
            if(id==null)buttons[0].EmitSignal(NClickableControl.SignalName.Released,buttons[0]);
            else {int i=Array.FindIndex(offer,o=>o.CardId==id);if(i<0)throw new InvalidOperationException("Card is not in current offer");var holder=screen.GetCardHolder(options[i].Card);holder.EmitSignal(NCardHolder.SignalName.Pressed,holder);}
        };
        Pending=handler;
        void Clear(){if(NativeScreen!=screen)return;Pending=null;NativeScreen=null;SaveExitButton=null;CurrentOwner=null;CurrentOffer=[];Committing=false;}
        void Close(){Clear();if(GodotObject.IsInstanceValid(screen)&&screen.IsInsideTree())NOverlayStack.Instance!.Remove(screen);}
        screen.TreeExiting+=Clear;
        int? index=await selection;Pending=null;
        if(index==null)
        {
            // _ExitTree resolves the native selection. Never mutate the overlay
            // stack from that teardown callback or resume its reward button there.
            Clear();await NGame.Instance!.ToSignal(NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
            return new(null,true);
        }
        Committing=true;
        // NGridCardHolder is pooled; never disable its hitbox, whose enabled state
        // is retained on reuse. Native clickability plus the scoped input gates lock selection.
        foreach(var option in options)screen.GetCardHolder(option.Card).SetClickable(false);
        foreach(var button in buttons)button.Disable();
        if(qa&&index==options.Length+1)
        {
            await ContractSave.Checkpoint(p,reward.Phase.ToString());Close();
            _=TaskHelper.RunSafely(ReturnAfterFrame());return new(null,true);
        }
        // Keep the native overlay until the deck/phase checkpoint completes.
        closeCommitted=Close;
        return new(index<options.Length?offer[index.Value].CardId:null);
    }
    static async Task ReturnAfterFrame()
    {
        var game=NGame.Instance!;await game.ToSignal(game.GetTree(),SceneTree.SignalName.ProcessFrame);
        await game.ReturnToMainMenu();
    }
}
[HarmonyPatch(typeof(NCardRewardSelectionScreen),"SelectCard")]
public static class NativeDualRewardCardInputGate
{
    static bool Prefix(NCardRewardSelectionScreen __instance)=>__instance!=DualRewardUi.NativeScreen||DualRewardUi.Pending!=null&&!DualRewardUi.Committing;
}
[HarmonyPatch(typeof(NCardRewardSelectionScreen),"OnAlternateRewardSelected")]
public static class NativeDualRewardAlternativeInputGate
{
    static bool Prefix(NCardRewardSelectionScreen __instance)=>__instance!=DualRewardUi.NativeScreen||DualRewardUi.Pending!=null&&!DualRewardUi.Committing;
}
