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
        var d=ContractRuntime.For(card.Owner)!;bool free=d.AlphaPowers.ContainsKey("RIN-R04")&&!d.FreeJewelBoostUsed;
        box.AddChild(new Label{Text=$"{card.Title}\n是否使用 Jewel Boost？{(free?"本回合首次免费，仍需要至少 1 宝石。":"将消耗 1 宝石。")}\n剩余宝石：{d.Jewel}/3"});
        void Resolve(bool boost){if(result.Task.IsCompleted)return;PendingDecision=null;layer.QueueFree();result.TrySetResult(boost);}
        PendingDecision=Resolve;
        var yes=new Button{Text=free?"使用 Jewel Boost · 本次免费":"使用 Jewel Boost · 消耗 1 宝石",CustomMinimumSize=new(0,48)};var no=new Button{Text="不使用宝石",CustomMinimumSize=new(0,48)};
        box.AddChild(yes);box.AddChild(no);yes.Pressed+=()=>Resolve(true);no.Pressed+=()=>Resolve(false);no.GrabFocus();
        Action<bool> handler=Resolve;layer.TreeExiting+=()=>{result.TrySetResult(false);if(PendingDecision==handler)PendingDecision=null;};
        return result.Task;
    }
}
public static class CoreHud
{
    static CanvasLayer? launcher;
    static CanvasLayer? combatHud;
    static CardModel[] reserveCards=[];
    static string? reserveMember;
    static string? reserveLanguage;
    public static Action<string>? PendingStarting;
    public static void ClearLauncher(){if(launcher!=null&&GodotObject.IsInstanceValid(launcher))launcher.QueueFree();launcher=null;}
    public static void DetachCombat(){if(combatHud!=null&&GodotObject.IsInstanceValid(combatHud))combatHud.QueueFree();combatHud=null;}
    // Display names only: all runtime, card-owner and enemy IDs remain unchanged.
    static string CharacterName(string? id)=>id switch{"CHAR_RIN"=>FsnLoc.Text("RIN_ROLE"),"CHAR_ARCHER"=>FsnLoc.Text("ARCHER_ROLE"),QaMaster.EnemyId=>"敌方御主",QaServant.EnemyId=>"敌方从者",_=>id??"—"};
    public static void RefreshReserve(ContractRuntime d)
    {
        if(MegaCrit.Sts2.Core.Nodes.Rooms.NCombatRoom.Instance?.Ui is not {} ui)return;
        var definition=CardBanks.Reserve[PileType.Hand];
        // Ritsu's extra-hand visuals follow CardPileCmd presentation, while hand banking uses
        // silent reference transfers. Remount only the view; never draw or reconstruct CardModels.
        var existing=ui.GetChildren().OfType<STS2RitsuLib.CardPiles.Nodes.NModExtraHand>().FirstOrDefault(h=>h.Definition==definition);
        var cards=d.Reserve.Hand.Cards.ToArray();
        string language=MegaCrit.Sts2.Core.Localization.LocManager.Instance.Language;
        if(existing!=null&&reserveMember==d.Reserve.CharacterId&&reserveLanguage==language&&reserveCards.SequenceEqual(cards))return;
        var position=existing?.Position??new Vector2(690,445);
        if(existing!=null){ui.RemoveChild(existing);existing.QueueFree();}
        var hand=STS2RitsuLib.CardPiles.Nodes.NModExtraHand.Create(definition);hand.Position=position;ui.AddChild(hand);hand.Initialize(d.Player);
        var reserveLabel=PresentationTheme.Label(FsnLoc.Format("RESERVE_HAND_HEADER",CharacterName(d.Reserve.CharacterId)),16,PresentationTheme.Paper);reserveLabel.Position=new(0,105);hand.AddChild(reserveLabel);
        reserveCards=cards;reserveMember=d.Reserve.CharacterId;reserveLanguage=language;
    }
    public static Task<string> ChooseStarting(ContractRuntime d)
    {
        var result=new TaskCompletionSource<string>();
        var layer=new CanvasLayer{Layer=100};NGame.Instance!.AddChild(layer);
        var panel=new PanelContainer{Position=new(250,130),CustomMinimumSize=new(780,350)};layer.AddChild(panel);
        var box=new VBoxContainer();panel.AddChild(box);
        box.AddChild(new Label{Text=$"凛 / 弓兵 — 选择开场前场角色\n{(PublicUiMode.IsPublic(d.Player)?"契约开场":D1Run.IsQa(d.Player)?"QA_D1_RUN · NOT_PUBLIC_FINAL_RUN":"开发期验收 · 非正式内容 · 基础敌方契约")}\n凛生命 {d.Rin.Creature.CurrentHp}/{d.Rin.Creature.MaxHp} · Archer HP {d.Archer.Creature.CurrentHp}/{d.Archer.Creature.MaxHp}\n双方已各自独立抽取 5 张开场手牌；每场重新选择前场，不会再次抽牌。"});
        box.AddChild(new Label{Text="凛的开场手牌："+string.Join("、",d.Rin.Hand.Cards.Select(c=>c.Title))+"\n弓兵的开场手牌："+string.Join("、",d.Archer.Hand.Cards.Select(c=>c.Title))});
        void Resolve(string id){if(result.Task.IsCompleted)return;PendingStarting=null;layer.QueueFree();result.TrySetResult(id);}
        PendingStarting=Resolve;
        var rin=new Button{Text="以凛开场 · 第 1 回合基础供魔：契约魔力 +1",CustomMinimumSize=new(0,56)};
        var archer=new Button{Text="以弓兵开场 · 第 1 回合不触发基础供魔：契约魔力 +0",CustomMinimumSize=new(0,56)};
        box.AddChild(rin);box.AddChild(archer);rin.Pressed+=()=>Resolve("CHAR_RIN");archer.Pressed+=()=>Resolve("CHAR_ARCHER");archer.GrabFocus();
        return result.Task;
    }
    public static void Attach(ContractRuntime d)
    {
        bool publicUi=PublicUiMode.IsPublic(d.Player);
        QaTargetTag.Attach(d);
        combatHud?.QueueFree();var layer=new CanvasLayer{Layer=70};combatHud=layer;NGame.Instance!.AddChild(layer);
        var reservePile=CardBanks.Bank(PileType.Hand,d.Player);bool refreshQueued=false;
        void HandChanged()
        {
            if(refreshQueued)return;refreshQueued=true;
            Callable.From(()=>{refreshQueued=false;if(combatHud==layer&&!d.Finished&&GodotObject.IsInstanceValid(layer))RefreshReserve(d);}).CallDeferred();
        }
        reservePile.ContentsChanged+=HandChanged;
        layer.TreeExiting+=()=>reservePile.ContentsChanged-=HandChanged;
        RefreshReserve(d);
        bool debugVisible=!publicUi,debugKeyHeld=false;
        var panel=new PanelContainer{Name="ContractDebugHud",Position=new(12,85),CustomMinimumSize=new(310,360),Visible=debugVisible};layer.AddChild(panel);
        var box=new VBoxContainer();panel.AddChild(box);
        var text=new Label{Text="凛 / 弓兵",MouseFilter=Control.MouseFilterEnum.Ignore};text.AddThemeFontSizeOverride("font_size",17);box.AddChild(text);
        var swap=new Button{Text=FsnLoc.Text(d.Reserve==d.Rin?"SWITCH_RIN":"SWITCH_ARCHER"),CustomMinimumSize=new(0,48)};box.AddChild(swap);
        swap.Pressed+=()=>{if(!swap.Disabled)RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new SwitchAction(d));};
        var alphaPanel=new PanelContainer{Name="ContractQaControls",Position=new(350,65),CustomMinimumSize=new(560,80),Visible=debugVisible&&!publicUi};layer.AddChild(alphaPanel);
        var alphaBox=new VBoxContainer();alphaPanel.AddChild(alphaBox);var alphaText=new Label();alphaBox.AddChild(alphaText);
        var helpers=new HBoxContainer();alphaBox.AddChild(helpers);
        var guard=new Button{Text="QA：Guard Master",CustomMinimumSize=new(245,44)};helpers.AddChild(guard);
        var suppress=new Button{Text="QA：压制 FIELD",CustomMinimumSize=new(245,44)};helpers.AddChild(suppress);
        guard.Pressed+=()=>RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new QaAlphaAction(d,false));
        suppress.Pressed+=()=>RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new QaAlphaAction(d,true));
        var reserveDebuff=new Button{Text="ARC_PRECISION QA：后备敌方 Weak 1",CustomMinimumSize=new(0,44),Visible=d.CombatFlags.GetValueOrDefault("QA_RESERVE_DEBUFF_TARGET")};alphaBox.AddChild(reserveDebuff);
        reserveDebuff.Pressed+=()=>RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new QaReserveDebuffAction(d));
        var gameplay=new PanelContainer{Name="ContractGameplayHud",Position=new(12,90),Visible=!debugVisible};layer.AddChild(gameplay);
        var gameplayBox=new VBoxContainer();gameplay.AddChild(gameplayBox);
        var gameplayText=new Label{Name="ContractGameplayStatus",MouseFilter=Control.MouseFilterEnum.Ignore};gameplayText.AddThemeFontSizeOverride("font_size",17);gameplayBox.AddChild(gameplayText);
        var gameplaySwap=new Button{Name="ContractSwitch",Text=FsnLoc.Text(d.Reserve==d.Rin?"SWITCH_RIN":"SWITCH_ARCHER"),CustomMinimumSize=new(270,44)};gameplayBox.AddChild(gameplaySwap);
        gameplaySwap.Pressed+=()=>{if(!gameplaySwap.Disabled)RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new SwitchAction(d));};
        var presentationHud=ContractPresentationHud.Attach(d,gameplay,gameplayText,gameplaySwap);
        var timer=new Godot.Timer{WaitTime=0.2,Autostart=true};layer.AddChild(timer);
        timer.Timeout+=()=>{
            // Native full-page card views take precedence over every combat-only overlay.
            layer.Visible=!DualDeckBrowser.IsOpen&&!(NGame.Instance?.GetInspectCardScreen().IsVisibleInTree()??false);
            presentationHud.Update();
            // Silent removals/order changes intentionally omit native pile events.
            // Reconcile only this read-only view; Ritsu refreshes cost/upgrade visuals.
            if(!d.Finished)RefreshReserve(d);
            bool debugKey=Input.IsPhysicalKeyPressed(Key.F8);
            if(debugKey&&!debugKeyHeld){debugVisible=!debugVisible;panel.Visible=debugVisible;alphaPanel.Visible=debugVisible&&!publicUi;gameplay.Visible=!debugVisible;}
            debugKeyHeld=debugKey;
            if(debugVisible)
            {
            gameplayText.Text=$"前排：{(d.Active==d.Rin?"凛":"弓兵")} · 回合 {d.Turn}\n凛生命 {d.Rin.Creature.CurrentHp}/{d.Rin.Creature.MaxHp} · 格挡 {d.Rin.Creature.Block}\n弓兵生命 {d.Archer.Creature.CurrentHp}/{d.Archer.Creature.MaxHp} · 格挡 {d.Archer.Creature.Block}\n契约魔力 {d.Mana}/10 · 宝石 {d.Jewel}/3\n独立行动：{(d.IndependentActionAvailable?"可用":"已使用")}";
            if(d.PendingReinforcement.Active||d.U10Charges>0)gameplayText.Text+=$"\n投影强化：强化投影等待 {(d.PendingReinforcement.Active?1:0)} · 术式额度 {d.U10Charges}";
            if(d.U15Pending)gameplayText.Text+="\n术式接续：下一张弓兵耗能牌费用降低1点";
            if(d.SelfReinforcement>0)gameplayText.Text+=$"\n自用强化：下次直接伤害或自身格挡 +{d.SelfReinforcement}";
            if(d.AlphaPowers.ContainsKey("RIN-R11"))gameplayText.Text+=$"\n下次宝石强化倍率：{(d.BoostMultiplier>ContractRuntime.NativeValueLimit?"超过原生数值范围":d.BoostMultiplier.ToString())}";
            if(d.ArmUses>0)gameplayText.Text+=$"\n累计兵装使用：{d.ArmUses}";
            if(d.EngineLimitReached)gameplayText.Text+="\n达到引擎上限";
            if(d.AlphaPowers.Count>0)gameplayText.Text+=$"\n刻印 {d.RinGrowthLayers}/{(d.AlphaPowers.GetValueOrDefault("RIN-R06")==2?6:5)} · 锻造 {d.ForgeLayers}/{(d.AlphaPowers.GetValueOrDefault("ARC-R06")==2?6:5)}";
            alphaText.Text=$"下一次投影：{(d.PendingReinforcement.Active?"强化":"普通")} · Mana Discount: {d.PendingReinforcement.ManaDiscount}\n术式强化额度：{d.U10Charges} · ARM_RESOLVED {d.ProjectedArmsResolvedThisCombat.Count}/3\nAlpha Power：{string.Join(" / ",d.AlphaPowers.Keys)}\nGuard Master：{d.GuardCharges} 次 · QA-only / NOT SHIPPING CONTENT\n"+string.Join("\n",d.FieldStatuses.Select(f=>$"{f.FieldId} · 时长 {(f.Duration<0?"本场战斗":f.Duration.ToString())} · {(f.Duration==0?"已到期":f.Suppressed?"已压制，下一玩家回合恢复":"生效")}"));
            guard.Disabled=suppress.Disabled=d.Enemy==null||d.Finished||d.Player.PlayerCombatState?.Phase!=PlayerTurnPhase.Play||AlphaChoice.IsOpen||RewardChoice.IsOpen||JewelChoice.PendingDecision!=null;
            suppress.Disabled|=d.FieldStatuses.All(f=>f.Duration==0);
            reserveDebuff.Disabled=guard.Disabled;
            if(d.Finished){text.Text=d.Defeated?"我方契约崩溃 · 战败\nCONTRACT_DEFEAT":"敌方契约崩溃 · 胜利\nENEMY_CONTRACT_DEFEAT";swap.Disabled=gameplaySwap.Disabled=true;return;}
            string Line(CharacterRuntime f)=>$"{CharacterName(f.CharacterId)} · {(f.ActiveState=="ACTIVE"?"前场":"后备")}\n生命 {f.Creature.CurrentHp}/{f.Creature.MaxHp} · 格挡 {f.Creature.Block}\n手牌 {f.Hand.Cards.Count} · 抽牌堆 {f.DrawPile.Cards.Count}\n弃牌堆 {f.Discard.Cards.Count} · 消耗堆 {f.Exhaust.Cards.Count}";
            text.Text=$"共享回合 {d.Turn} · 开发期验收\n前排：{CharacterName(d.Active.CharacterId)}\n后备：{CharacterName(d.Reserve.CharacterId)}\n共享能量 {d.Energy}/3\n契约魔力 {d.Mana}/10 · 宝石 {d.Jewel}/3\n本回合免费切换：{(d.FreeSwitchAvailable?"可用":"已使用")}\n独立行动：{(d.IndependentActionAvailable?"可用":"已使用")}\n\n{Line(d.Rin)}\n\n{Line(d.Archer)}\n\n敌方前排：{CharacterName(d.Enemy?.ActiveId)}\n意图步骤 {d.Enemy?.NextStep} · 敌方魔力 {d.Enemy?.Mana}/6\n{d.Enemy?.Intent}\n种子：{d.Seed}\n冻结后备手牌：只读";
            }
            swap.Text=FsnLoc.Text(d.Reserve==d.Rin?"SWITCH_RIN":"SWITCH_ARCHER");
            swap.Disabled=!d.FreeSwitchAvailable||d.Player.PlayerCombatState?.Phase!=PlayerTurnPhase.Play||d.Switching||JewelChoice.PendingDecision!=null||AlphaChoice.IsOpen||RewardChoice.IsOpen;
            gameplaySwap.Text=swap.Text;gameplaySwap.Disabled=swap.Disabled;
        };
    }
    public static async Task StartQa(bool field=false)
    {
        await StartQaRun("RINARCHERQA");
        await RunManager.Instance.EnterRoomDebug(RoomType.Monster,model:field?ModelDb.Encounter<QaFieldPressure>().ToMutable():ModelDb.Encounter<QaPairBasic>().ToMutable(),showTransition:false);
    }
    public static async Task StartQaRun(string seed)
    {
        ClearLauncher();
        var game=NGame.Instance!;
        NModalContainer.Instance?.Clear();TestMode.IsOn=false;
        SaveManager.Instance.MarkFtueAsComplete("combat_rules_ftue");
        PublicUiMode.CreatingDebugRun=true;
        try{await game.StartNewSingleplayerRun(ModelDb.Character<RinContractCharacter>(),false,[ModelDb.Act<Overgrowth>(),ModelDb.Act<Hive>(),ModelDb.Act<Glory>()],[],seed,GameMode.Standard);}
        finally{PublicUiMode.CreatingDebugRun=false;}
    }
    public static void AttachLauncher()
    {
        var game=NGame.Instance!;var layer=new CanvasLayer{Layer=65};launcher=layer;game.AddChild(layer);
        var button=new Button{Text="凛 / 弓兵 · Milestone B 基础契约 QA",Position=new(18,585),CustomMinimumSize=new(370,48)};layer.AddChild(button);
        button.Pressed+=()=>{layer.QueueFree();TaskHelper.RunSafely(StartQa());};
        var field=new Button{Text="Milestone B · QA_FIELD_PRESSURE",Position=new(18,640),CustomMinimumSize=new(370,48)};layer.AddChild(field);
        field.Pressed+=()=>{layer.QueueFree();TaskHelper.RunSafely(StartQa(true));};
        AlphaQaSession.AttachLauncher(layer);
        D1Run.AttachLauncher(layer);
        D2Run.AttachLauncher(layer);
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
        if(CommandLineHelper.HasArg("rin-archer-qa"))_ = TaskHelper.RunSafely(CoreHud.StartQa(CommandLineHelper.HasArg("rin-archer-field-qa")));
    }
}
