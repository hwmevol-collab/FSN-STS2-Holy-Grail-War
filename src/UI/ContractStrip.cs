using MegaCrit.Sts2.Core.Nodes.Rooms;
namespace RinArcherCore;
// Read-only resource views. Neither icon is a relic or a card pile.
public sealed partial class ContractPresentationHud:HBoxContainer
{
    readonly ContractRuntime d;readonly Label mana,jewel,ia;readonly Button swap;
    public ContractPresentationHud(ContractRuntime runtime,Button switchButton)
    {
        d=runtime;swap=switchButton;Name="PresentationContractHud";MouseFilter=MouseFilterEnum.Ignore;AddThemeConstantOverride("separation",16);
        mana=Resource("ManaView",FsnLoc.Text("UI_A9D8AE7EFBC2"),"#a488df",false);
        jewel=Resource("JewelView",FsnLoc.Text("UI_9B94E941BEF0"),"#ed486f",true);
        ia=PresentationTheme.Label("",17);ia.Name="IndependentActionView";swap.AddChild(ia);ia.Position=new(-32,-31);ia.MouseFilter=MouseFilterEnum.Stop;
        swap.CustomMinimumSize=new(170,40);swap.Size=new(170,40);
        PresentationTheme.Button(swap);swap.AddThemeFontSizeOverride("font_size",17);
        Update();
    }
    Label Resource(string name,string title,string color,bool gem)
    {
        var box=new HBoxContainer{Name=name,MouseFilter=MouseFilterEnum.Stop};box.AddThemeConstantOverride("separation",5);AddChild(box);
        string shape=gem?$"<path d='M16 3L27 12L22 27L16 32L7 25L5 12Z' fill='{color}' stroke='#f0d8af' stroke-width='1.5'/><path d='M16 3L13 14L16 32M5 12L13 14L27 12M13 14L22 27' fill='none' stroke='#ffccd9'/>":$"<circle cx='17' cy='17' r='14' fill='#252336' stroke='#cebd8e' stroke-width='2'/><path d='M17 5L24 18L17 28L10 18Z' fill='{color}'/><path d='M7 19L17 10L27 19' fill='none' stroke='#e4d3ff' stroke-width='1.5'/>";
        box.AddChild(new TextureRect{Texture=gem?ContractCostArtwork.Jewel:ContractCostArtwork.Mana,CustomMinimumSize=new(34,34),ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,MouseFilter=MouseFilterEnum.Ignore});
        var count=PresentationTheme.Label("",23);count.AddThemeColorOverride("font_outline_color",Colors.Black);count.AddThemeConstantOverride("outline_size",5);box.AddChild(count);
        box.TooltipText=title;return count;
    }
    public void Update()
    {
        mana.Text=$"{d.Mana}/10";jewel.Text=$"{d.Jewel}/3";
        mana.GetParent<Control>().TooltipText=FsnLoc.Text("UI_D9C70781B108")+d.Mana+FsnLoc.Text("UI_C86359B0F818");
        var facts=new List<string>();if(d.PendingReinforcement.Active)facts.Add(FsnLoc.Text("UI_266FAB64CC69"));if(d.U10Charges>0)facts.Add(FsnLoc.Text("UI_9733E7A6031E")+d.U10Charges);if(d.U15Pending)facts.Add(FsnLoc.Text("UI_58C65C056488"));if(d.SelfReinforcement>0)facts.Add(FsnLoc.Text("UI_91A5A68624CB")+d.SelfReinforcement);if(d.EngineLimitReached)facts.Add(FsnLoc.Text("UI_CF003555B410"));
        jewel.GetParent<Control>().TooltipText=FsnLoc.Text("UI_10B2DB5D0A13")+d.Jewel+FsnLoc.Text("UI_44C62CD9CF02")+string.Join(" · ",facts);
        ia.Text=FsnLoc.Text("UI_C85D957799AE")+(d.FreeSwitchAvailable?FsnLoc.Text("UI_4D99C976BEB8"):FsnLoc.Text("UI_937683DA32C1"))+FsnLoc.Text("UI_D2F0656064EE")+(d.IndependentActionAvailable?FsnLoc.Text("UI_4D99C976BEB8"):FsnLoc.Text("UI_937683DA32C1"));ia.Modulate=d.IndependentActionAvailable?PresentationTheme.Paper:PresentationTheme.Muted;
        ia.TooltipText=FsnLoc.Text("UI_A4DCDE298C01");
        swap.TooltipText=FsnLoc.Text("UI_AE5A0A4A30DF");
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
