using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
public readonly record struct DualRewardDecision(string? CardId,bool Cancelled=false);
public static class DualRewardUi
{
    public static Action<string?>? Pending;
    public static string? CurrentOwner;
    public static IReadOnlyList<RewardOfferCard> CurrentOffer=[];
    public static bool Committing{get;private set;}
    static Action? closeCommitted;
    public static void CloseCommitted(){closeCommitted?.Invoke();closeCommitted=null;}
    public static readonly Queue<string?> TestChoices=[];
    public static Task<DualRewardDecision> Ask(Player p,DualRewardState reward,string owner)
    {
        if(TestMode.IsOn)return Task.FromResult(new DualRewardDecision(TestChoices.Count>0?TestChoices.Dequeue():null));
        if(Pending!=null)throw new InvalidOperationException("Dual reward selection already open");
        var result=new TaskCompletionSource<DualRewardDecision>();var game=NGame.Instance!;var size=game.GetViewport().GetVisibleRect().Size;
        var layer=new CanvasLayer{Layer=135};game.AddChild(layer);
        layer.AddChild(new ColorRect{Size=size,Color=new(0,0,0,0.95f),MouseFilter=Control.MouseFilterEnum.Stop});
        bool rin=owner=="CHAR_RIN";var color=new Color(rin?"92374d":"527087");
        var panel=new PanelContainer{Position=new(70,35),CustomMinimumSize=new(1140,640)};layer.AddChild(panel);
        var margin=new MarginContainer();foreach(var k in new[]{"margin_left","margin_right","margin_top","margin_bottom"})margin.AddThemeConstantOverride(k,18);panel.AddChild(margin);
        var box=new VBoxContainer();box.AddThemeConstantOverride("separation",10);margin.AddChild(box);
        var s=ContractSave.Get(p);
        var heading=new Label{Text=$"卡牌奖励 {(rin?1:2)} / 2  ·  {(rin?"MASTER — 远坂凛":"SERVANT — Archer")}\n凛 HP {p.Creature.CurrentHp}/{p.Creature.MaxHp}  ·  Archer HP {s.ArcherHp}/{s.ArcherMaxHp}  ·  每位角色选择 0–1 张",Modulate=color.Lightened(0.45f)};
        heading.AddThemeFontSizeOverride("font_size",24);box.AddChild(heading);
        var row=new HBoxContainer();row.AddThemeConstantOverride("separation",14);box.AddChild(row);
        void Resolve(string? id)
        {
            if(result.Task.IsCompleted)return;Pending=null;Committing=true;
            foreach(var child in Buttons(box))child.Disabled=true;
            heading.Text+="\n正在保存选择…";result.TrySetResult(new(id));
        }
        closeCommitted=()=>{Committing=false;CurrentOwner=null;CurrentOffer=[];layer.QueueFree();};
        foreach(var offered in reward.Offer(owner))
        {
            var definition=AlphaRewardRegistry.Get(offered.CardId);var item=new PanelContainer{CustomMinimumSize=new(354,430)};
            item.AddThemeStyleboxOverride("panel",new StyleBoxFlat{BgColor=color.Darkened(0.6f),BorderColor=color.Lightened(0.2f),BorderWidthLeft=rin?6:2,BorderWidthRight=rin?2:6,BorderWidthTop=3,BorderWidthBottom=3,ContentMarginLeft=14,ContentMarginRight=14,ContentMarginTop=12,ContentMarginBottom=12});row.AddChild(item);
            var column=new VBoxContainer();column.AddThemeConstantOverride("separation",12);item.AddChild(column);
            var title=new Label{Text=$"{(rin?"◆ MASTER FRAME":"▣ SERVANT FRAME")}\n{definition.Name}\n{definition.Id} · {definition.Rarity} · {definition.Type}\n{definition.Energy} Energy / {definition.Mana} Mana",AutowrapMode=TextServer.AutowrapMode.WordSmart,CustomMinimumSize=new(320,0)};title.AddThemeFontSizeOverride("font_size",21);column.AddChild(title);
            var rules=new Label{Text=definition.Rules+"\n升级："+definition.Upgrade,AutowrapMode=TextServer.AutowrapMode.WordSmart,CustomMinimumSize=new(320,235)};rules.AddThemeFontSizeOverride("font_size",18);column.AddChild(rules);
            var pick=new Button{Text="选择 "+definition.Id,CustomMinimumSize=new(0,48)};column.AddChild(pick);pick.Pressed+=()=>Resolve(definition.Id);
        }
        var skip=new Button{Text=$"Skip · {(rin?"凛":"Archer")} 本次不拿牌",CustomMinimumSize=new(0,48)};box.AddChild(skip);skip.Pressed+=()=>Resolve(null);
        var exit=new Button{Text="保存并返回主菜单 · 重进后继续当前奖励",CustomMinimumSize=new(0,42)};box.AddChild(exit);
        exit.Pressed+=async()=>{exit.Disabled=true;await ContractSave.Checkpoint(p,reward.Phase.ToString());Pending=null;CurrentOwner=null;CurrentOffer=[];result.TrySetResult(new(null,true));layer.QueueFree();await game.ReturnToMainMenu();};
        Action<string?> handler=Resolve;Pending=handler;CurrentOwner=owner;CurrentOffer=reward.Offer(owner);skip.GrabFocus();
        layer.TreeExiting+=()=>{result.TrySetResult(new(null,true));if(Pending==handler){Pending=null;CurrentOwner=null;CurrentOffer=[];Committing=false;}};
        return result.Task;
    }
    static IEnumerable<Button> Buttons(Node root){foreach(var n in root.GetChildren()){if(n is Button b)yield return b;foreach(var child in Buttons(n))yield return child;}}
}
