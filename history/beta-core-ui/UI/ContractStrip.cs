using MegaCrit.Sts2.Core.Nodes.Rooms;
namespace RinArcherCore;
// Read-only resource views. Neither icon is a relic or a card pile.
public sealed partial class ContractPresentationHud:HBoxContainer
{
    readonly ContractRuntime d;readonly Label mana,jewel,ia;readonly Button swap;
    public ContractPresentationHud(ContractRuntime runtime,Button switchButton)
    {
        d=runtime;swap=switchButton;Name="PresentationContractHud";MouseFilter=MouseFilterEnum.Ignore;AddThemeConstantOverride("separation",16);
        mana=Resource("ManaView","契约魔力","#a488df",false);
        jewel=Resource("JewelView","宝石","#ed486f",true);
        ia=PresentationTheme.Label("",14);ia.Name="IndependentActionView";swap.AddChild(ia);ia.Position=new(-8,-29);ia.MouseFilter=MouseFilterEnum.Stop;
        swap.CustomMinimumSize=new(170,40);swap.Size=new(170,40);
        PresentationTheme.Button(swap);swap.AddThemeFontSizeOverride("font_size",17);
        Update();
    }
    Label Resource(string name,string title,string color,bool gem)
    {
        var box=new HBoxContainer{Name=name,MouseFilter=MouseFilterEnum.Stop};box.AddThemeConstantOverride("separation",5);AddChild(box);
        string shape=gem?$"<path d='M16 3L27 12L22 27L16 32L7 25L5 12Z' fill='{color}' stroke='#f0d8af' stroke-width='1.5'/><path d='M16 3L13 14L16 32M5 12L13 14L27 12M13 14L22 27' fill='none' stroke='#ffccd9'/>":$"<circle cx='17' cy='17' r='14' fill='#252336' stroke='#cebd8e' stroke-width='2'/><path d='M17 5L24 18L17 28L10 18Z' fill='{color}'/><path d='M7 19L17 10L27 19' fill='none' stroke='#e4d3ff' stroke-width='1.5'/>";
        box.AddChild(new TextureRect{Texture=PresentationTheme.Svg(name,shape,34,34),CustomMinimumSize=new(34,34),ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,MouseFilter=MouseFilterEnum.Ignore});
        var count=PresentationTheme.Label("",23);count.AddThemeColorOverride("font_outline_color",Colors.Black);count.AddThemeConstantOverride("outline_size",5);box.AddChild(count);
        box.TooltipText=title;return count;
    }
    public void Update()
    {
        mana.Text=$"{d.Mana}/10";jewel.Text=$"{d.Jewel}/3";
        mana.GetParent<Control>().TooltipText="契约魔力：共享资源，当前 "+d.Mana+" / 上限 10。沿用卡牌与前场供魔规则；此图标仅显示资源。";
        var facts=new List<string>();if(d.PendingReinforcement.Active)facts.Add("强化投影待生效");if(d.U10Charges>0)facts.Add("术式额度 "+d.U10Charges);if(d.U15Pending)facts.Add("术式接续待生效");if(d.SelfReinforcement>0)facts.Add("自用强化 +"+d.SelfReinforcement);if(d.EngineLimitReached)facts.Add("达到引擎上限");
        jewel.GetParent<Control>().TooltipText="宝石：共享资源，当前 "+d.Jewel+" / 上限 3。仅在合法宝石强化选择后消耗。\n"+string.Join(" · ",facts);
        ia.Text="切换 "+(d.FreeSwitchAvailable?"可用":"已用")+" · 独立行动 "+(d.IndependentActionAvailable?"可用":"已用");ia.Modulate=d.IndependentActionAvailable?PresentationTheme.Paper:PresentationTheme.Muted;
        ia.TooltipText="Archer 每个共享回合的第一次兵装使用可享独立行动；实际资格与支付沿用 V1.3。";
        swap.TooltipText="每个共享回合一次免费 Switch；切换保留双方手牌与共享能量。";
        if(NCombatRoom.Instance is {} room&&room.GetCreatureNode(d.Rin.Creature) is {} rin&&room.GetCreatureNode(d.Archer.Creature) is {} archer)
        {Position=rin.GetGlobalTransformWithCanvas().Origin+new Vector2(-95,-405);swap.Position=archer.GetGlobalTransformWithCanvas().Origin+new Vector2(-86,-406);}
        Visible=!d.Finished;swap.Visible=!d.Finished;
    }
    public static ContractPresentationHud Attach(ContractRuntime d,PanelContainer panel,Label oldText,Button swap)
    {
        oldText.Visible=false;panel.Visible=false;panel.CustomMinimumSize=Vector2.Zero;panel.AddThemeStyleboxOverride("panel",new StyleBoxEmpty());
        var layer=panel.GetParent();swap.Reparent(layer);var hud=new ContractPresentationHud(d,swap);layer.AddChild(hud);return hud;
    }
}
