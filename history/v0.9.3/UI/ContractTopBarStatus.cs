using MegaCrit.sts2.Core.Nodes.TopBar;
using MegaCrit.Sts2.Core.Combat;
namespace RinArcherCore;

// Presentation only: retain the native top-bar slots and their input behavior.
[HarmonyPatch(typeof(NTopBarPortrait),nameof(NTopBarPortrait.Initialize))]
public static class ContractTopBarPortraitSize
{
    static void Postfix(NTopBarPortrait __instance,Player player)
    {
        if(player.Character is not RinContractCharacter)return;
        Callable.From(()=>Apply(__instance)).CallDeferred();
    }
    public static void Apply(NTopBarPortrait portrait)
    {
        if(portrait.GetNodeOrNull<Control>("ContractIcon") is not {} icon)return;
        icon.SetAnchorsPreset(Control.LayoutPreset.TopLeft);
        icon.CustomMinimumSize=Vector2.Zero;icon.Position=new(4,-4);icon.Size=new(56,56);
    }
}
[HarmonyPatch(typeof(NTopBarHp),nameof(NTopBarHp.Initialize))]
public static class ContractTopBarHpMount
{
    static void Postfix(NTopBarHp __instance,Player player)
    {
        if(player.Character is RinContractCharacter&&__instance.GetNodeOrNull<ContractDualHpView>("ContractDualHp")==null)
            __instance.AddChild(new ContractDualHpView(player,__instance));
    }
}
public sealed partial class ContractDualHpView:Control
{
    readonly Player player;readonly NTopBarHp hp;readonly Label rin,archer;
    public ContractDualHpView(Player p,NTopBarHp native)
    {
        player=p;hp=native;Name="ContractDualHp";MouseFilter=MouseFilterEnum.Ignore;
        rin=Row("RinHp");archer=Row("ArcherHp");AddChild(rin);AddChild(archer);
        TreeEntered+=()=>{GetTree().ProcessFrame+=Refresh;Refresh();};
        TreeExiting+=()=>GetTree().ProcessFrame-=Refresh;
    }
    static Label Row(string name)
    {
        var row=PresentationTheme.Label("",21,new Color("ff716e"));row.Name=name;
        row.ClipText=true;row.VerticalAlignment=VerticalAlignment.Center;
        row.AddThemeConstantOverride("outline_size",3);row.AddThemeColorOverride("font_outline_color",new Color("161c23"));
        return row;
    }
    void Refresh()
    {
        if(MegaCrit.Sts2.Core.Nodes.NRun.Instance?.GlobalUi.TopBar.Portrait is {} portrait)ContractTopBarPortraitSize.Apply(portrait);
        var native=hp.GetNodeOrNull<Control>("%HpLabel");if(native==null)return;
        var d=ContractRuntime.For(player);
        bool combat=d is {Finished:false}&&CombatManager.Instance.IsInProgress;
        Visible=combat;native.Visible=true;native.SelfModulate=combat?new Color(1,1,1,0):Colors.White;if(!combat)return;
        // Use exactly the native HP label's horizontal footprint; no extra topbar panel.
        Position=new(native.Position.X,4);Size=new(native.Size.X,60);
        rin.Position=Vector2.Zero;rin.Size=new(Size.X,30);archer.Position=new(0,30);archer.Size=rin.Size;
        rin.Text=$"{FsnLoc.Text("RIN_SHORT")} {d!.Rin.Creature.CurrentHp}/{d.Rin.Creature.MaxHp}";
        archer.Text=$"Archer {d.Archer.Creature.CurrentHp}/{d.Archer.Creature.MaxHp}";
        foreach(var row in new[]{rin,archer})
        {
            int font=21;var face=row.GetThemeFont("font");
            while(font>15&&face.GetStringSize(row.Text,fontSize:font).X>Size.X-2)font--;
            row.AddThemeFontSizeOverride("font_size",font);
        }
    }
}
