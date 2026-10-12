using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
public static class AlphaChoice
{
    public static string? TestArm;
    public static Creature? TestTarget;
    public static Action<string?>? PendingArm;
    public static Action<Creature?>? PendingTarget;
    public static bool IsOpen=>PendingArm!=null||PendingTarget!=null;
    static (CanvasLayer,VBoxContainer) Panel(string title)
    {
        var layer=new CanvasLayer{Layer=120};NGame.Instance!.AddChild(layer);
        var backdrop=new ColorRect{Color=new(0,0,0,0.85f),Size=NGame.Instance.GetViewport().GetVisibleRect().Size,MouseFilter=Control.MouseFilterEnum.Stop};layer.AddChild(backdrop);
        var panel=new PanelContainer{Position=new(350,150),CustomMinimumSize=new(590,350)};layer.AddChild(panel);
        var box=new VBoxContainer();box.AddThemeConstantOverride("separation",12);panel.AddChild(box);
        box.AddChild(new Label{Text=title});return(layer,box);
    }
    static Button Button(VBoxContainer box,string text,Action press)
    {
        var b=new Button{Text=text,CustomMinimumSize=new(0,64)};box.AddChild(b);b.Pressed+=press;return b;
    }
    public static async Task<string?> AskArm(Trace card)
    {
        var d=ContractRuntime.For(card.Owner)!;d.Log("TRACE_OPENED",new{availableArms=Arsenal.Ids,selectedArm=(string?)null,cancelled=false});
        string? id;
        if(TestMode.IsOn)id=TestArm;
        else
        {
            var result=new TaskCompletionSource<string?>();var(layer,box)=Panel("投影：明确选择 1 件武器\n取消将保留投影卡牌与能量。");
            void Resolve(string? value){if(!result.TrySetResult(value))return;PendingArm=null;layer.QueueFree();}
            PendingArm=Resolve;layer.TreeExiting+=()=>{result.TrySetResult(null);PendingArm=null;};
            Button(box,"干将·莫邪 · 0 能量 / 1 魔力 · 前排 6 伤害",()=>Resolve(Arsenal.Ids[0]));
            Button(box,"Rho Aias（开发名） · 0 能量 / 1 魔力 · 弓兵 8 格挡",()=>Resolve(Arsenal.Ids[1]));
            Button(box,"Hrunting（开发名） · 1 能量 / 1 魔力 · 可选 Master / Servant",()=>Resolve(Arsenal.Ids[2]));
            Button(box,"取消选择",()=>Resolve(null)).GrabFocus();id=await result.Task;
        }
        if(id!=null&&!Arsenal.Ids.Contains(id))throw new ArgumentException("Illegal Arsenal choice");
        d.Log("TRACE_CHOICE",new{availableArms=Arsenal.Ids,selectedArm=id,cancelled=id==null});return id;
    }
    public static async Task<Creature?> AskTarget(Hrunting card)
    {
        var d=ContractRuntime.For(card.Owner)!;
        Creature[] legal=d.Enemy==null?d.Combat.Enemies.Where(c=>c.IsAlive).ToArray():new[]{d.Enemy.Master,d.Enemy.Servant}.Where(c=>c.IsAlive).ToArray();
        Creature? target;
        if(TestMode.IsOn)target=TestTarget;
        else if(legal.Length==1)target=legal[0];
        else
        {
            var result=new TaskCompletionSource<Creature?>();var(layer,box)=Panel("选择 Hrunting 的目标\n敌方 Master / Servant 均可选择，包括后备成员。\n取消将保留卡牌、能量、魔力与独立行动。");
            void Resolve(Creature? value){if(!result.TrySetResult(value))return;PendingTarget=null;layer.QueueFree();}
            PendingTarget=Resolve;layer.TreeExiting+=()=>{result.TrySetResult(null);PendingTarget=null;};
            foreach(var c in legal){var member=c;Button(box,$"{(c==d.Enemy?.Master?"QA Master · 敌方御主":"QA Servant · 敌方从者")} · 生命 {c.CurrentHp} · 格挡 {c.Block} · {(c==d.Enemy?.Active?"前场":"后备")}",()=>Resolve(member));}
            Button(box,"取消选择",()=>Resolve(null)).GrabFocus();target=await result.Task;
        }
        if(target!=null&&!legal.Contains(target))throw new ArgumentException("Illegal Contract member choice");
        d.Log("ANY_TARGET_CHOICE",new{target=target?.CombatId,member=target==d.Enemy?.Master?"MASTER":target==null?null:"SERVANT",cancelled=target==null});return target;
    }
}
public static class QaTargetTag
{
    public static void RefreshNumbers(ContractRuntime d)
    {
        if(TestMode.IsOn||d.Enemy?.IsField!=true||NCombatRoom.Instance?.GetCreatureNode(d.Enemy.Servant) is not {} node)return;
        _ = MegaCrit.Sts2.Core.Helpers.TaskHelper.RunSafely(node.UpdateIntent(d.Combat.Players.Select(p=>p.Creature)));
    }
    public static string Text(ContractTarget type)=>type switch{ContractTarget.FRONT=>"目标：前排 [FRONT]",ContractTarget.MASTER=>"目标：Master [MASTER]",ContractTarget.BOTH=>"目标：双方 [BOTH]",ContractTarget.SERVANT=>"目标：Servant [SERVANT]",ContractTarget.ANY_CONTRACT_MEMBER=>"目标：任选契约成员 [ANY_CONTRACT_MEMBER]",ContractTarget.LOCKED=>"目标：锁定成员 [LOCKED]",_=>throw new ArgumentOutOfRangeException(nameof(type))};
    public static void Attach(ContractRuntime d)
    {
        if(d.Enemy==null||NCombatRoom.Instance is not {} room)return;
        var node=room.GetCreatureNode(d.Enemy.Servant);if(node==null)return;
        var panel=new PanelContainer{Position=new(-125,-285),MouseFilter=Control.MouseFilterEnum.Ignore};node.AddChild(panel);
        var label=new Label{Text=Text(d.Enemy.IntentTarget),MouseFilter=Control.MouseFilterEnum.Ignore};label.AddThemeFontSizeOverride("font_size",19);panel.AddChild(label);
        var timer=new Godot.Timer{WaitTime=0.1,Autostart=true};panel.AddChild(timer);
        timer.Timeout+=()=>{label.Text=d.Enemy.NextStep==4&&d.Enemy.IsField?"目标：自身 · 格挡 +10 / 切换从者":Text(d.Enemy.IntentTarget);};
    }
}
