using System.Text.Json;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Entities.Multiplayer;
namespace RinArcherCore;
public sealed record DraftEvent(string Event,string Owner,int Round,string[] CardIds,string[] Rarities,string? CardId);
public sealed class AlphaDraftSession
{
    public const string LabId="QA_ALPHA_DRAFT_LAB";
    public const string Policy="NOT_FINAL_REWARD_SYSTEM / DUPLICATE_REWARD_POLICY_DEFERRED / POWER_DUPLICATE_STACK_POLICY_DEFERRED";
    public int Seed{get;}
    public int Round{get;private set;}=1;
    public readonly List<DraftEvent> Events=[];
    public readonly Dictionary<string,List<string>> Picks=new(){["CHAR_RIN"]=[],["CHAR_ARCHER"]=[]};
    readonly Dictionary<string,List<string>> remaining=new(){["CHAR_RIN"]=[],["CHAR_ARCHER"]=[]};
    readonly Dictionary<string,string[]> offers=[];
    readonly HashSet<string> decided=[];
    readonly Random random;
    public AlphaDraftSession(int seed){Seed=seed;random=new(seed);foreach(var owner in remaining.Keys)remaining[owner].AddRange(AlphaRewardRegistry.Pool(owner).Select(d=>d.Id));}
    public bool Complete=>remaining.Values.All(p=>p.Count==0)&&offers.Count==0;
    public IReadOnlyList<string> Offer(string owner)
    {
        if(offers.TryGetValue(owner,out var current))return current;
        if(decided.Contains(owner))throw new InvalidOperationException("Already decided this owner round");
        var pool=remaining[owner];var offer=new List<string>();
        // Avoid repeats within an offer; picked IDs are retired for this QA session.
        // Unpicked cards return to later rounds so coverage does not require taking every card.
        var candidates=pool.ToList();for(int i=0;i<Math.Min(3,pool.Count);i++){int index=random.Next(candidates.Count);offer.Add(candidates[index]);candidates.RemoveAt(index);}
        if(offer.Count==0)return [];
        offers[owner]=offer.ToArray();Events.Add(new("REWARD_OFFER",owner,Round,offer.ToArray(),offer.Select(id=>AlphaRewardRegistry.Get(id).Rarity.ToString()).ToArray(),null));return offers[owner];
    }
    public void Decide(string owner,string? cardId)
    {
        if(!offers.TryGetValue(owner,out var offer)||decided.Contains(owner))throw new InvalidOperationException("No undecided offer");
        if(cardId!=null&&!offer.Contains(cardId))throw new ArgumentException("Pick is not offered to owner");
        if(cardId!=null){Picks[owner].Add(cardId);remaining[owner].Remove(cardId);}
        Events.Add(new(cardId==null?"REWARD_SKIP":"REWARD_PICK",owner,Round,[],[],cardId));offers.Remove(owner);decided.Add(owner);
        if(remaining.Keys.All(o=>decided.Contains(o)||remaining[o].Count==0)){Round++;decided.Clear();}
    }
}
public static class AlphaQaSession
{
    public const string ArchetypeId="QA_ALPHA_ARCHETYPE";
    public static readonly IReadOnlyDictionary<string,string[]> Presets=new Dictionary<string,string[]>{
        ["RIN_JEWEL"]=["RIN-C05","RIN-C13","RIN-U01","RIN-U14","RIN-R04"],
        ["RIN_COMBAT_CONTROL"]=["RIN-C04","RIN-C10","RIN-U04","RIN-U06"],
        ["RIN_CONTRACT"]=["RIN-C08","RIN-C12","RIN-C13","RIN-U10","RIN-U12","RIN-R05"],
        ["ARC_TOOLBOX"]=["ARC-C03","ARC-C06","ARC-C07","ARC-U12","ARC-U14"],
        ["ARC_BROKEN"]=["ARC-C11","ARC-U02","ARC-U12","ARC-R03"],
        ["ARC_INDEPENDENT"]=["ARC-C10","ARC-U13","ARC-R05"],
        ["ARC_PRECISION"]=["ARC-U05"]};
    static Player? pendingPlayer;
    static Dictionary<string,List<string>>? pendingBuild;
    static List<DraftEvent>? pendingEvents;
    static string? pendingSource;
    public static bool DraftOpen{get;private set;}
    public static AlphaDraftSession? CurrentDraft{get;private set;}
    public static async Task Start(string? preset=null,int seed=310,int rounds=6,bool field=false)
    {
        await CoreHud.StartQaRun("RINARCHERALPHA"+seed);var p=RunManager.Instance.DebugOnlyGetState()!.Players[0];
        Dictionary<string,List<string>> build=new(){["CHAR_RIN"]=[],["CHAR_ARCHER"]=[]};List<DraftEvent> events=[];
        if(preset!=null){foreach(var id in Presets[preset])build[AlphaRewardRegistry.Get(id).Owner].Add(id);}
        else
        {
            CurrentDraft=new(seed);DraftOpen=true;
            try{for(int round=0;round<rounds;round++)foreach(var owner in new[]{"CHAR_RIN","CHAR_ARCHER"})
            {
                var offer=CurrentDraft.Offer(owner);if(offer.Count==0)continue;
                var picked=await AlphaDraftUi.Ask(CurrentDraft,owner,offer);CurrentDraft.Decide(owner,picked);
            }}finally{DraftOpen=false;}
            build=CurrentDraft.Picks;events=CurrentDraft.Events;
        }
        pendingPlayer=p;pendingBuild=build;pendingEvents=events;pendingSource=preset??AlphaDraftSession.LabId;
        await RunManager.Instance.EnterRoomDebug(RoomType.Monster,model:field?ModelDb.Encounter<QaFieldPressure>().ToMutable():ModelDb.Encounter<QaPairBasic>().ToMutable(),showTransition:false);
    }
    public static void Inject(ContractRuntime d)
    {
        if(pendingPlayer!=d.Player||pendingBuild==null||d.Enemy==null)return;
        foreach(var owner in new[]{"CHAR_RIN","CHAR_ARCHER"})foreach(var id in pendingBuild[owner])
        {
            var definition=AlphaRewardRegistry.Get(id);if(definition.Owner!=owner)throw new InvalidOperationException("Reward owner mismatch");
            var card=(AlphaRewardCard)d.Player.RunState.CreateCard(AlphaRewardRegistry.Card(id),d.Player);card.InstanceId=$"qa:{owner}:{id}";d.Member(owner).Deck.AddInternal(card,silent:true);
        }
        foreach(var ev in pendingEvents??[])d.Log(ev.Event,new{owner=ev.Owner,round=ev.Round,cardIds=ev.CardIds,rarities=ev.Rarities,cardId=ev.CardId});
        if(pendingSource=="ARC_PRECISION")d.CombatFlags["QA_RESERVE_DEBUFF_TARGET"]=true;
        d.Log("ALPHA_QA_BUILD",new{source=pendingSource,policy=AlphaDraftSession.Policy,rin=pendingBuild["CHAR_RIN"],archer=pendingBuild["CHAR_ARCHER"]});
        pendingBuild=null;pendingPlayer=null;pendingEvents=null;
    }
    public static void AttachLauncher(CanvasLayer layer)
    {
        var draft=new Button{Text="Milestone C · QA_ALPHA_DRAFT_LAB",Position=new(410,530),CustomMinimumSize=new(430,48)};layer.AddChild(draft);
        draft.Pressed+=()=>TaskHelper.RunSafely(ChooseDraft());
        var forced=new Button{Text="Milestone C · QA_ALPHA_ARCHETYPE",Position=new(410,585),CustomMinimumSize=new(430,48)};layer.AddChild(forced);
        forced.Pressed+=()=>TaskHelper.RunSafely(ChoosePreset());
    }
    static async Task ChooseDraft()
    {
        var selected=await RewardChoice.Ask("QA Draft · 固定种子可复现 · 每人每轮选 0–1\n"+AlphaDraftSession.Policy,[("310","Seed 310 · 6 轮"),("311","Seed 311 · 6 轮"),("312","Seed 312 · 6 轮")]);
        if(selected==null)return;
        var enemy=await RewardChoice.Ask("选择 Draft 后的 QA 战斗",[("BASIC","QA_PAIR_BASIC"),("FIELD","QA_FIELD_PRESSURE")]);if(enemy!=null)await Start(seed:int.Parse(selected),field:enemy=="FIELD");
    }
    static async Task ChoosePreset()
    {
        // Seven presets in two short panels to stay inside the 720p QA viewport.
        var family=await RewardChoice.Ask("QA_ALPHA_ARCHETYPE",[("RIN","凛：宝石 / 控制 / 契约"),("ARC","弓兵：工具箱 / 崩坏 / 独立 / 精准")]);if(family==null)return;
        var preset=await RewardChoice.Ask("选择强制构筑 · 只注入 QA Deck",Presets.Where(p=>p.Key.StartsWith(family)).Select(p=>(p.Key,p.Key+" · "+p.Value.Length+" 张核心 Reward" )).ToArray());if(preset==null)return;
        var enemy=await RewardChoice.Ask("选择 QA 战斗",[("BASIC","QA_PAIR_BASIC"),("FIELD","QA_FIELD_PRESSURE")]);if(enemy!=null)await Start(preset,field:enemy=="FIELD");
    }
}
public sealed class QaReserveDebuffAction(ContractRuntime d):MegaCrit.Sts2.Core.GameActions.GameAction
{
    public override ulong OwnerId=>d.Player.NetId;
    public override GameActionType ActionType=>GameActionType.CombatPlayPhaseOnly;
    protected override async Task ExecuteAction()
    {
        if(!d.CombatFlags.GetValueOrDefault("QA_RESERVE_DEBUFF_TARGET")||d.Enemy==null)throw new InvalidOperationException("Reserve Debuff helper requires ARC_PRECISION QA preset");
        var reserve=d.Enemy.Active==d.Enemy.Master?d.Enemy.Servant:d.Enemy.Master;
        await PowerCmd.Apply<MegaCrit.Sts2.Core.Models.Powers.WeakPower>(new ThrowingPlayerChoiceContext(),reserve,1,d.Archer.Creature,null);d.Log("QA_RESERVE_DEBUFF_TARGET",new{target=reserve.CombatId,weak=1});
    }
    public override INetAction ToNetAction()=>new MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction{cmd="RinArcherCore/QA_RESERVE_DEBUFF_TARGET",inCombat=true};
}
public static class AlphaDraftUi
{
    public static Action<string?>? Pending;
    public static string? CurrentOwner;
    public static IReadOnlyList<string> CurrentOffer=[];
    public static async Task<string?> Ask(AlphaDraftSession session,string owner,IReadOnlyList<string> offer)
    {
        var result=new TaskCompletionSource<string?>();var game=NGame.Instance!;var viewport=game.GetViewport().GetVisibleRect().Size;var layer=new CanvasLayer{Layer=130};game.AddChild(layer);
        layer.AddChild(new ColorRect{Size=viewport,Color=new(0,0,0,0.92f),MouseFilter=Control.MouseFilterEnum.Stop});
        var panel=new PanelContainer{Position=new(90,70),CustomMinimumSize=new(1100,570)};layer.AddChild(panel);
        var margin=new MarginContainer();foreach(var key in new[]{"margin_left","margin_right","margin_top","margin_bottom"})margin.AddThemeConstantOverride(key,20);panel.AddChild(margin);
        var box=new VBoxContainer();box.AddThemeConstantOverride("separation",14);margin.AddChild(box);
        var heading=new Label{Text=$"QA_ALPHA_DRAFT_LAB · Seed {session.Seed} · Round {session.Round}\n{owner} · 选择 0–1 张 Alpha Reward",CustomMinimumSize=new(1060,0)};heading.AddThemeFontSizeOverride("font_size",24);box.AddChild(heading);
        var row=new HBoxContainer();row.AddThemeConstantOverride("separation",20);box.AddChild(row);
        void Resolve(string? id){if(result.Task.IsCompleted)return;Pending=null;CurrentOwner=null;CurrentOffer=[];layer.QueueFree();result.TrySetResult(id);}
        foreach(var id in offer)
        {
            var d=AlphaRewardRegistry.Get(id);var item=new PanelContainer{CustomMinimumSize=new(340,350)};row.AddChild(item);var column=new VBoxContainer();column.AddThemeConstantOverride("separation",12);item.AddChild(column);
            var title=new Label{Text=$"{d.Name}\n{d.Id} · {d.Rarity}\n{d.Owner} · {d.Type}\n{d.Energy} Energy / {d.Mana} Mana",AutowrapMode=TextServer.AutowrapMode.WordSmart,CustomMinimumSize=new(315,0)};title.AddThemeFontSizeOverride("font_size",21);column.AddChild(title);
            var rules=new Label{Text=d.Rules+"\n升级："+d.Upgrade,AutowrapMode=TextServer.AutowrapMode.WordSmart,CustomMinimumSize=new(315,210)};rules.AddThemeFontSizeOverride("font_size",18);column.AddChild(rules);
            var pick=new Button{Text="选择 "+id,CustomMinimumSize=new(0,54)};column.AddChild(pick);pick.Pressed+=()=>Resolve(id);
        }
        box.AddChild(new Label{Text="NOT_FINAL_REWARD_SYSTEM · QA cardId 无重复发放；重复牌与 Power 叠加规则暂缓。"});
        var skip=new Button{Text="Skip · 此 Owner 本轮不拿牌",CustomMinimumSize=new(0,54)};box.AddChild(skip);skip.Pressed+=()=>Resolve(null);skip.GrabFocus();
        Action<string?> handler=Resolve;Pending=handler;CurrentOwner=owner;CurrentOffer=offer;layer.TreeExiting+=()=>{result.TrySetResult(null);if(Pending==handler){Pending=null;CurrentOwner=null;CurrentOffer=[];}};return await result.Task;
    }
}
