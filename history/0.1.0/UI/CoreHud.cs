using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.GameActions;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.Models.Acts;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.TestSupport;
using System.Text.Json;
namespace RinArcherCore;
public static class JewelChoice
{
    public static bool? TestChoice;
    public static Action<bool>? PendingDecision;
    public static Task<bool> Ask(StarterCard card)
    {
        if(TestMode.IsOn)return Task.FromResult(TestChoice??false);
        var result=new TaskCompletionSource<bool>();
        var layer=new CanvasLayer{Layer=110};NGame.Instance!.AddChild(layer);
        var panel=new PanelContainer{Position=new(360,180),CustomMinimumSize=new(560,220)};layer.AddChild(panel);
        var box=new VBoxContainer();panel.AddChild(box);
        box.AddChild(new Label{Text=$"{card.Title}\nUse 1 Rin Jewel for this card?\nJewel remaining: {ContractRuntime.For(card.Owner)!.Jewel}/3"});
        void Resolve(bool boost){if(!result.TrySetResult(boost))return;PendingDecision=null;layer.QueueFree();}
        PendingDecision=Resolve;
        var yes=new Button{Text="Use 1 Jewel",CustomMinimumSize=new(0,48)};var no=new Button{Text="Do not use Jewel",CustomMinimumSize=new(0,48)};
        box.AddChild(yes);box.AddChild(no);yes.Pressed+=()=>Resolve(true);no.Pressed+=()=>Resolve(false);no.GrabFocus();
        return result.Task;
    }
}
public static class CoreHud
{
    static CanvasLayer? launcher;
    public static Action<string>? PendingStarting;
    public static void RefreshReserve(ContractRuntime d)
    {
        if(MegaCrit.Sts2.Core.Nodes.Rooms.NCombatRoom.Instance?.Ui is not {} ui)return;
        var definition=CardBanks.Reserve[PileType.Hand];
        // Ritsu's extra-hand visuals follow CardPileCmd presentation, while hand banking uses
        // silent reference transfers. Remount only the view; never draw or reconstruct CardModels.
        var existing=ui.GetChildren().OfType<STS2RitsuLib.CardPiles.Nodes.NModExtraHand>().FirstOrDefault(h=>h.Definition==definition);
        var position=existing?.Position??new Vector2(660,510);
        if(existing!=null){ui.RemoveChild(existing);existing.QueueFree();}
        var hand=STS2RitsuLib.CardPiles.Nodes.NModExtraHand.Create(definition);hand.Position=position;ui.AddChild(hand);hand.Initialize(d.Player);
        hand.AddChild(new Label{Text=$"{d.Reserve.CharacterId.Replace("CHAR_","")} RESERVE HAND · VIEW ONLY",Position=new(0,-32),MouseFilter=Control.MouseFilterEnum.Ignore});
    }
    public static Task<string> ChooseStarting(ContractRuntime d)
    {
        var result=new TaskCompletionSource<string>();
        var layer=new CanvasLayer{Layer=100};NGame.Instance!.AddChild(layer);
        var panel=new PanelContainer{Position=new(250,130),CustomMinimumSize=new(780,350)};layer.AddChild(panel);
        var box=new VBoxContainer();panel.AddChild(box);
        box.AddChild(new Label{Text="RIN / ARCHER - STARTING ACTIVE\nNOT_SHIPPING_CONTENT · QA_PAIR_BASIC\nBoth opening hands already contain 5 independent card instances."});
        box.AddChild(new Label{Text="Rin: "+string.Join(", ",d.Rin.Hand.Cards.Select(c=>c.Title))+"\nArcher: "+string.Join(", ",d.Archer.Hand.Cards.Select(c=>c.Title))});
        void Resolve(string id){if(!result.TrySetResult(id))return;PendingStarting=null;layer.QueueFree();}
        PendingStarting=Resolve;
        var rin=new Button{Text="Start as Rin · Turn 1 Mana +1",CustomMinimumSize=new(0,56)};
        var archer=new Button{Text="Start as Archer · Turn 1 Mana +0",CustomMinimumSize=new(0,56)};
        box.AddChild(rin);box.AddChild(archer);rin.Pressed+=()=>Resolve("CHAR_RIN");archer.Pressed+=()=>Resolve("CHAR_ARCHER");archer.GrabFocus();
        return result.Task;
    }
    public static void Attach(ContractRuntime d)
    {
        var layer=new CanvasLayer{Layer=70};NGame.Instance!.AddChild(layer);
        var panel=new PanelContainer{Position=new(12,85),CustomMinimumSize=new(310,360)};layer.AddChild(panel);
        var box=new VBoxContainer();panel.AddChild(box);
        var text=new Label{Text="Rin / Archer",MouseFilter=Control.MouseFilterEnum.Ignore};text.AddThemeFontSizeOverride("font_size",17);box.AddChild(text);
        var swap=new Button{Text="Switch",CustomMinimumSize=new(0,48)};box.AddChild(swap);
        swap.Pressed+=()=>{if(!swap.Disabled)RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new SwitchAction(d));};
        var timer=new Godot.Timer{WaitTime=0.2,Autostart=true};layer.AddChild(timer);
        timer.Timeout+=()=>{
            if(d.Finished){text.Text=d.Defeated?"CONTRACT_DEFEAT":"ENEMY_CONTRACT_DEFEAT";swap.Disabled=true;return;}
            string Line(CharacterRuntime f)=>$"{f.CharacterId.Replace("CHAR_","")} {f.ActiveState}\nHP {f.Creature.CurrentHp}/{f.Creature.MaxHp} · BLOCK {f.Creature.Block}\nHAND {f.Hand.Cards.Count} DRAW {f.DrawPile.Cards.Count}\nDISCARD {f.Discard.Cards.Count} EXHAUST {f.Exhaust.Cards.Count}";
            text.Text=$"TURN {d.Turn} · NOT_SHIPPING_CONTENT\nACTIVE {d.Active.CharacterId}\nRESERVE {d.Reserve.CharacterId}\nENERGY {d.Energy}/3 · MANA {d.Mana}/10\nJEWEL {d.Jewel}/3\nSWITCH {(d.FreeSwitchAvailable?"READY":"USED")}\nINDEPENDENT ACTION {(d.IndependentActionAvailable?"READY":"USED")}\n\n{Line(d.Rin)}\n\n{Line(d.Archer)}\n\nENEMY ACTIVE {d.Enemy?.ActiveId}\nSTATE {d.Enemy?.NextStep} · MANA {d.Enemy?.Mana}/6\n{d.Enemy?.Intent}\nSEED {d.Seed}\nReserve Hand: view only";
            swap.Text=$"Switch to {d.Reserve.CharacterId.Replace("CHAR_","")}";
            swap.Disabled=!d.FreeSwitchAvailable||d.Player.PlayerCombatState?.Phase!=PlayerTurnPhase.Play||d.Switching||JewelChoice.PendingDecision!=null;
        };
    }
    public static async Task StartQa()
    {
        launcher?.QueueFree();launcher=null;
        var game=NGame.Instance!;
        NModalContainer.Instance?.Clear();TestMode.IsOn=false;
        SaveManager.Instance.MarkFtueAsComplete("combat_rules_ftue");
        await game.StartNewSingleplayerRun(ModelDb.Character<RinContractCharacter>(),false,[ModelDb.Act<Overgrowth>(),ModelDb.Act<Hive>(),ModelDb.Act<Glory>()],[],"RINARCHERQA",GameMode.Standard);
        await RunManager.Instance.EnterRoomDebug(RoomType.Monster,model:ModelDb.Encounter<QaPairBasic>().ToMutable(),showTransition:false);
    }
    public static void AttachLauncher()
    {
        var game=NGame.Instance!;var layer=new CanvasLayer{Layer=65};launcher=layer;game.AddChild(layer);
        var button=new Button{Text="Rin / Archer · Milestone A QA",Position=new(18,640),CustomMinimumSize=new(350,48)};layer.AddChild(button);
        button.Pressed+=()=>{layer.QueueFree();TaskHelper.RunSafely(StartQa());};
    }
}
[HarmonyPatch(typeof(NGame),"LoadMainMenu")]
public static class QaLauncherHook
{
    static void Postfix(ref Task __result)=>__result=After(__result);
    static async Task After(Task task)
    {
        await task;
        if(CommandLineHelper.HasArg("rin-archer-tests"))return;
        CoreHud.AttachLauncher();
        if(CommandLineHelper.HasArg("rin-archer-qa"))_ = TaskHelper.RunSafely(CoreHud.StartQa());
    }
}
