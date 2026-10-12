using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
public static class RewardChoice
{
    public static readonly Queue<string?> TestChoices=[];
    public static Action<string?>? Pending;
    public static IReadOnlyList<(string Id,string Label)> CurrentOptions=[];
    public static bool IsOpen=>Pending!=null;
    public static async Task<string?> Ask(string title,IReadOnlyList<(string Id,string Label)> options,string cancel="取消：保留卡牌与全部资源")
    {
        if(options.Count==0)return null;
        if(TestMode.IsOn){var chosen=TestChoices.Count>0?TestChoices.Dequeue():null;if(chosen!=null&&!options.Any(o=>o.Id==chosen))throw new ArgumentException("Illegal test choice");return chosen;}
        var result=new TaskCompletionSource<string?>();var layer=new CanvasLayer{Layer=125};NGame.Instance!.AddChild(layer);
        var viewport=NGame.Instance.GetViewport().GetVisibleRect().Size;
        layer.AddChild(new ColorRect{Color=new(0.03f,0.02f,0.05f,0.72f),Size=viewport,MouseFilter=Control.MouseFilterEnum.Stop});
        var panel=new PanelContainer{Position=new(Math.Max(12,(viewport.X-760)/2),Math.Max(12,(viewport.Y-520)/2)),CustomMinimumSize=new(Math.Min(760,viewport.X-24),0)};layer.AddChild(panel);panel.AddThemeStyleboxOverride("panel",PresentationTheme.Box(PresentationTheme.Gold));
        var margin=new MarginContainer();foreach(var key in new[]{"margin_left","margin_right","margin_top","margin_bottom"})margin.AddThemeConstantOverride(key,20);panel.AddChild(margin);
        var box=new VBoxContainer();box.AddThemeConstantOverride("separation",12);margin.AddChild(box);
        box.AddChild(PresentationTheme.Label("CONTRACT  /  术式选择",16,PresentationTheme.Gold));
        var heading=new Label{Text=title,AutowrapMode=TextServer.AutowrapMode.WordSmart,CustomMinimumSize=new(Math.Min(690,viewport.X-64),0)};heading.AddThemeFontSizeOverride("font_size",25);heading.AddThemeColorOverride("font_color",PresentationTheme.Paper);box.AddChild(heading);
        bool memberChoice=options.All(o=>o.Id is "CHAR_RIN" or "CHAR_ARCHER");
        var scroll=new ScrollContainer{CustomMinimumSize=new(0,Math.Min(options.Count*(memberChoice?108:54),Math.Max(108,viewport.Y-220))),HorizontalScrollMode=ScrollContainer.ScrollMode.Disabled};box.AddChild(scroll);
        var optionBox=new VBoxContainer{SizeFlagsHorizontal=Control.SizeFlags.ExpandFill};scroll.AddChild(optionBox);
        void Resolve(string? id){if(result.Task.IsCompleted)return;Pending=null;CurrentOptions=[];layer.QueueFree();result.TrySetResult(id);}
        Action<string?> handler=Resolve;Pending=handler;CurrentOptions=options;layer.TreeExiting+=()=>{result.TrySetResult(null);if(Pending==handler){Pending=null;CurrentOptions=[];}};
        foreach(var option in options)
        {
            var selected=option.Id;var b=new Button{Text=option.Label,CustomMinimumSize=new(0,memberChoice?104:50)};PresentationTheme.Button(b,true);b.Alignment=HorizontalAlignment.Left;optionBox.AddChild(b);
            if(memberChoice)
            {
                foreach(var state in new[]{"normal","hover","pressed","disabled"})
                {var style=(StyleBoxFlat)b.GetThemeStylebox(state).Duplicate();style.ContentMarginLeft=110;b.AddThemeStyleboxOverride(state,style);}
                var atlas=PresentationTheme.Asset(selected=="CHAR_RIN"?"rin.png":"archer.png");
                var portrait=new TextureRect{Name="ContractMemberPortrait",ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered,MouseFilter=Control.MouseFilterEnum.Ignore,Texture=new AtlasTexture{Atlas=atlas,Region=new Rect2(0,0,atlas.GetWidth(),Math.Min(atlas.GetHeight(),atlas.GetWidth()*.72f))},Position=new(16,8),Size=new(80,88)};b.AddChild(portrait);portrait.Size=new(80,88);
            }
            b.Pressed+=()=>Resolve(selected);
        }
        var back=new Button{Text=cancel,CustomMinimumSize=new(0,54)};PresentationTheme.Button(back);box.AddChild(PresentationTheme.Label("确认后按原卡牌规则结算；取消保留卡牌与资源。",16,PresentationTheme.Muted));box.AddChild(back);back.Pressed+=()=>Resolve(null);back.GrabFocus();
        back.GuiInput+=e=>{if(e is InputEventKey {Pressed:true,Keycode:Key.Escape}){Resolve(null);back.AcceptEvent();}};
        return await result.Task;
    }
    public static async Task<bool> Prepare(AlphaRewardCard c)
    {
        c.ClearChoice();var d=ContractRuntime.For(c.Owner)!;string? selected;
        switch(c.SourceCardId)
        {
            case "RIN-C12":case "RIN-U14":
                var modes=new List<(string,string)>{("DEFENSE",$"防御：凛 {(c.SourceCardId=="RIN-C12"?(c.IsUpgraded?11:8):(c.IsUpgraded?15:12))} 格挡"),("SUPPLY",$"供魔：{(c.SourceCardId=="RIN-C12"?(c.IsUpgraded?3:2):(c.IsUpgraded?4:3))} 契约魔力")};
                if(c.SourceCardId=="RIN-U14")modes.Insert(0,("ATTACK",$"攻击：FRONT {(c.IsUpgraded?15:12)} 伤害"));
                c.PreparedSelection=await Ask(c.Title,modes);return c.PreparedSelection!=null;
            case "RIN-U06":var fields=RewardRules.Fields(d);if(fields.Length==0)return true;selected=await Ask(c.Title,fields.Select((f,i)=>(i.ToString(),$"FIELD {f.FieldId} · {(f.Suppressed?"已压制":"生效")} · 压制到下次共享回合开始")).ToArray());if(selected==null)return false;c.PreparedField=fields[int.Parse(selected)];return true;
            case "ARC-C06":case "ARC-U14":
                var ids=c.SourceCardId=="ARC-C06"?Arsenal.Ids.Take(2):Arsenal.Ids.Where(id=>!d.ProjectedArmsResolvedThisCombat.Contains(id));
                c.PreparedSelection=await Ask(c.Title,ids.Select(id=>(id,$"{Arsenal.Get(id).Title} · {id}")).ToArray());return c.PreparedSelection!=null;
            case "ARC-C07":case "ARC-C11":case "ARC-U02":case "ARC-R03":
                var arms=RewardRules.Arms(d,c.SourceCardId is "ARC-U02" or "ARC-R03");
                selected=await Ask(c.Title,arms.Select(a=>(a.InstanceId,$"{a.Title} · 魔力 {a.ModifiedManaCost} · {a.InstanceId}")).ToArray());if(selected==null)return false;c.PreparedArm=arms.Single(a=>a.InstanceId==selected);
                if(c.SourceCardId=="ARC-R03"&&c.PreparedArm.ArmId=="ARM_HRUNTING"){c.PreparedTarget=await Target(c,d.Enemy==null?d.Combat.Enemies.Where(e=>e.IsAlive).ToArray():new[]{d.Enemy.Master,d.Enemy.Servant}.Where(e=>e.IsAlive).ToArray());if(c.PreparedTarget==null){c.ClearChoice();return false;}}
                return true;
            case "ARC-U05":c.PreparedTarget=await Target(c,RewardRules.PrecisionTargets(d));return c.PreparedTarget!=null;
            default:return true;
        }
    }
    static async Task<Creature?> Target(AlphaRewardCard c,Creature[] legal)
    {
        var d=ContractRuntime.For(c.Owner)!;
        var options=legal.Select((t,i)=>(i.ToString(),$"{(t==d.Enemy?.Master?"敌方 Master":"敌方 Servant")} · {(t==d.Enemy?.Active?"FRONT":"Reserve")} · HP {t.CurrentHp} · Debuff {t.Powers.Count(p=>p.Type==MegaCrit.Sts2.Core.Entities.Powers.PowerType.Debuff)}")).ToArray();
        var selection=await Ask(c.Title+"：选择合法敌方目标",options);return selection==null?null:legal[int.Parse(selection)];
    }
}
