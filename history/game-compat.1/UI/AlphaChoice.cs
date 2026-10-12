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
            var result=new TaskCompletionSource<string?>();var(layer,box)=Panel(FsnLoc.Text("UI_7C3ABF278881"));
            void Resolve(string? value){if(result.Task.IsCompleted)return;PendingArm=null;layer.QueueFree();result.TrySetResult(value);}
            PendingArm=Resolve;layer.TreeExiting+=()=>{result.TrySetResult(null);PendingArm=null;};
            Button(box,FsnLoc.Text("UI_D8B754DECB22"),()=>Resolve(Arsenal.Ids[0]));
            Button(box,FsnLoc.Text("UI_A8D55784189F"),()=>Resolve(Arsenal.Ids[1]));
            Button(box,FsnLoc.Text("UI_22B6DD5A1C71"),()=>Resolve(Arsenal.Ids[2]));
            Button(box,FsnLoc.Text("UI_74966E20DF2E"),()=>Resolve(null)).GrabFocus();id=await result.Task;
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
            var result=new TaskCompletionSource<Creature?>();var(layer,box)=Panel(FsnLoc.Text("UI_6A0F073DF15C"));
            void Resolve(Creature? value){if(result.Task.IsCompleted)return;PendingTarget=null;layer.QueueFree();result.TrySetResult(value);}
            PendingTarget=Resolve;layer.TreeExiting+=()=>{result.TrySetResult(null);PendingTarget=null;};
            foreach(var c in legal){var member=c;Button(box,FsnLoc.Format("UI_FD422DB9661F", (c==d.Enemy?.Master?FsnLoc.Text("UI_547C769CABB5"):FsnLoc.Text("UI_A8C9C3DB7C88")), c.CurrentHp, c.Block, (c==d.Enemy?.Active?FsnLoc.Text("UI_8065FA1C7928"):FsnLoc.Text("UI_CF2E968D2598"))),()=>Resolve(member));}
            Button(box,FsnLoc.Text("UI_74966E20DF2E"),()=>Resolve(null)).GrabFocus();target=await result.Task;
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
    public static string Text(ContractTarget type)=>type switch{ContractTarget.FRONT=>FsnLoc.Text("UI_BBC664ADB0C7"),ContractTarget.MASTER=>FsnLoc.Text("UI_371EE8E73726"),ContractTarget.BOTH=>FsnLoc.Text("UI_252A1F1C6F9F"),ContractTarget.SERVANT=>FsnLoc.Text("UI_02090DFB2D1C"),ContractTarget.ANY_CONTRACT_MEMBER=>FsnLoc.Text("UI_4732813BC451"),ContractTarget.LOCKED=>FsnLoc.Text("UI_98422FDB172F"),_=>throw new ArgumentOutOfRangeException(nameof(type))};
    public static void Attach(ContractRuntime d)
    {
        if(d.Enemy==null||NCombatRoom.Instance is not {} room)return;
        var node=room.GetCreatureNode(d.Enemy.Servant);if(node==null)return;
        var panel=new PanelContainer{Position=new(-125,-285),MouseFilter=Control.MouseFilterEnum.Ignore};node.AddChild(panel);
        string DisplayTarget()=>PublicUiMode.IsPublic(d.Player)?Text(d.Enemy.IntentTarget).Split('[')[0].TrimEnd():Text(d.Enemy.IntentTarget);
        var label=new Label{Text=DisplayTarget(),MouseFilter=Control.MouseFilterEnum.Ignore};label.AddThemeFontSizeOverride("font_size",19);panel.AddChild(label);
        var timer=new Godot.Timer{WaitTime=0.1,Autostart=true};panel.AddChild(timer);
        timer.Timeout+=()=>{label.Text=d.Enemy.NextStep==4&&d.Enemy.IsField?FsnLoc.Text("UI_03D14735327E"):DisplayTarget();};
    }
}
