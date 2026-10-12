using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.Nodes.Screens.Overlays;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Cards.Holders;
using MegaCrit.Sts2.Core.Entities.Cards;
using MegaCrit.Sts2.Core.TestSupport;
using MegaCrit.Sts2.Core.Entities.CardRewardAlternatives;
using MegaCrit.Sts2.Core.Entities.Rewards;
namespace RinArcherCore;

// A native one-selection screen adapter. Permanent acquisition uses the shared deck service.
public static class ContractBossRewardUi
{
    public static Action<string?>? Pending{get;private set;}
    public static IReadOnlyList<RewardOfferCard> Offer{get;private set;}=[];
    public static bool Committing{get;private set;}
    public static NCardRewardSelectionScreen? Screen{get;private set;}
    public static readonly Queue<string?> TestChoices=[];
    static Action? close;
    public static void CloseCommitted(){var action=close;close=null;action?.Invoke();}
    public static async Task<DualRewardDecision> Ask(Player p,ContractBossRewardState state)
    {
        if(TestMode.IsOn)return new(TestChoices.Count>0?TestChoices.Dequeue():null);
        if(Screen!=null)throw new InvalidOperationException("Boss reward screen already open");
        var cards=state.Offer.Select(o=>new CardCreationResult(p.RunState.CreateCard(AlphaRewardRegistry.Card(o.CardId),p))).ToArray();
        var screen=NCardRewardSelectionScreen.ShowScreen(cards,[new("Skip",PostAlternateCardRewardAction.EndSelectionAndDoNotCompleteReward)])!;
        Screen=screen;Offer=state.Offer;var selected=screen.OptionSelected();
        screen.GetNode<NCommonBanner>("UI/Banner").label.SetTextAutoSize("Boss 奖励 · 共选择 0–1 张\n"+string.Join(" · ",state.Offer.Select(o=>(o.Owner==RunEconomy.Rin?"凛：":"Archer：")+AlphaRewardRegistry.Card(o.CardId).Title)));
        var button=screen.GetNode<Control>("UI/RewardAlternatives").GetChildren().OfType<NCardRewardAlternativeButton>().Single();
        Pending=id=>{if(selected.IsCompleted)return;if(id==null)button.EmitSignal(MegaCrit.Sts2.Core.Nodes.GodotExtensions.NClickableControl.SignalName.Released,button);else{var i=state.Offer.FindIndex(c=>c.CardId==id);if(i<0)throw new ArgumentException("Unoffered Boss card");var holder=screen.GetCardHolder(cards[i].Card);holder.EmitSignal(NCardHolder.SignalName.Pressed,holder);}};
        void Clear(){if(Screen!=screen)return;Screen=null;Pending=null;Offer=[];Committing=false;}
        void Close(){Clear();if(GodotObject.IsInstanceValid(screen)&&screen.IsInsideTree())NOverlayStack.Instance!.Remove(screen);}
        screen.TreeExiting+=Clear;
        int? result=await selected;Pending=null;
        if(result==null){Clear();return new(null,true);}
        Committing=true;foreach(var card in cards)screen.GetCardHolder(card.Card).SetClickable(false);button.Disable();close=Close;
        return new(result<cards.Length?state.Offer[result.Value].CardId:null);
    }
}
[HarmonyPatch(typeof(NCardRewardSelectionScreen),"SelectCard")]
public static class BossRewardCardInputGate{static bool Prefix(NCardRewardSelectionScreen __instance)=>__instance!=ContractBossRewardUi.Screen||ContractBossRewardUi.Pending!=null&&!ContractBossRewardUi.Committing;}
[HarmonyPatch(typeof(NCardRewardSelectionScreen),"OnAlternateRewardSelected")]
public static class BossRewardSkipInputGate{static bool Prefix(NCardRewardSelectionScreen __instance)=>__instance!=ContractBossRewardUi.Screen||ContractBossRewardUi.Pending!=null&&!ContractBossRewardUi.Committing;}
