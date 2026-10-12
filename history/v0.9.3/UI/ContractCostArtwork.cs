using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Models;
using MegaCrit.Sts2.Core.Entities.UI;
namespace RinArcherCore;

// Read-only artwork. Native EnergyCost and its native label still own every cost calculation.
public static class ContractCostArtwork
{
    public static bool LegacyReview {get;set;} // screenshot comparison only; defaults to the new artwork.
    public static Texture2D Energy=>EnergyFor(true);
    public static Texture2D EnergyFor(bool rin)=>PresentationTheme.Svg("cost-owner-v2-"+rin,
        (rin?"<path d='M40 2L64 10L78 40L64 70L40 78L16 70L2 40L16 10Z' fill='#481d38' stroke='#dc75a0' stroke-width='2'/>":"<path d='M24 3H56L77 24V56L56 77H24L3 56V24Z' fill='#233548' stroke='#c0d3e1' stroke-width='2'/>")+"<g transform='translate(7 7) scale(.825)'>"+EnergySvg+"</g>",80,80);
    public static Texture2D Mana=>PresentationTheme.Svg("cost-mana-circuit",ManaSvg,48,48);
    public static Texture2D Jewel=>PresentationTheme.Svg("cost-jewel-facet",JewelSvg,48,48);
    public const string EnergySvg="<defs><radialGradient id='metal' cx='.3' cy='.18' r='.9'><stop stop-color='#f7e4b8'/><stop offset='.32' stop-color='#c5a36d'/><stop offset='.64' stop-color='#766149'/><stop offset='1' stop-color='#2d2429'/></radialGradient><radialGradient id='glass' cx='.38' cy='.25' r='.8'><stop stop-color='#74513d'/><stop offset='.6' stop-color='#35262c'/><stop offset='1' stop-color='#16141c'/></radialGradient></defs><path d='M39 4C60 3 74 19 75 40C76 61 59 75 39 76C18 76 4 60 4 39C4 20 18 5 39 4Z' fill='#0f1119' stroke='#1b1320' stroke-width='4'/><path d='M38 5C58 4 73 18 74 38C76 58 60 73 40 75C19 76 6 60 5 41C4 21 17 7 38 5Z' fill='url(#metal)' stroke='#e0c397' stroke-width='1.4'/><circle cx='40' cy='40' r='28' fill='url(#glass)' stroke='#17151d' stroke-width='3'/><path d='M17 29A27 27 0 0 1 56 17' fill='none' stroke='#f6dfb0' stroke-width='1.3' opacity='.65'/><path d='M25 68L33 66L36 69L43 64L40 72L48 69' fill='none' stroke='#f3d58e' stroke-width='1.8' stroke-linecap='round'/><path d='M8 40L13 40M67 40L72 40M40 8L40 13' stroke='#ead5ad' stroke-width='2'/><circle cx='16' cy='19' r='1.7' fill='#ffeccc'/><circle cx='65' cy='59' r='1.5' fill='#8d714f'/>";
    public const string ManaSvg="<defs><radialGradient id='m'><stop stop-color='#305b82'/><stop offset='1' stop-color='#152030'/></radialGradient></defs><path d='M12 5H36L43 12V36L36 43H12L5 36V12Z' fill='url(#m)' stroke='#9eafc9' stroke-width='1.5'/><path d='M15 8H33L40 15V33L33 40H15L8 33V15Z' fill='none' stroke='#67c3e2' stroke-width='1'/><path d='M5 18H10M38 30H43M18 5V10M30 38V43' stroke='#d5e7ed' stroke-width='2'/><path d='M13 30A13 13 0 0 1 30 12M18 36A13 13 0 0 0 36 19' fill='none' stroke='#51add0' stroke-width='1' opacity='.65'/>";
    public const string JewelSvg="<defs><linearGradient id='j' x2='1' y2='1'><stop stop-color='#ff879f'/><stop offset='.35' stop-color='#cd3156'/><stop offset='1' stop-color='#6c1235'/></linearGradient></defs><path d='M24 3L38 13L36 31L24 44L12 32L9 13Z' fill='url(#j)' stroke='#dfbc92' stroke-width='1.5'/><path d='M24 3L20 15L24 44L29 16ZM9 13L20 15L12 32M20 15L29 16L38 13M29 16L36 31' fill='none' stroke='#ffc2cb' stroke-width='1'/><path d='M15 12L22 6' stroke='#ffe2dd' stroke-width='2' stroke-linecap='round'/>";
    public sealed record CostFacts(int Mana,bool ShowMana,string OptionalMana,int Jewels,string JewelText,bool OptionalJewel,bool FreeBoost,bool JewelAvailable);
    public static CostFacts Facts(StarterCard c,ContractRuntime? d)
    {
        bool live=d is {Finished:false};int mana=live?d!.EffectiveManaCost(c.OwnerCharacterId,c.PrintedManaCost,c.ModifiedManaCost):c.ModifiedManaCost;
        // Exact registered choice branches. Gaining a resource never becomes a price.
        string optional=c.SourceCardId switch{"RIN_S_MANA_SUPPLY"=>(c.IsUpgraded?2:3).ToString(),"ARC-C10" or "RIN-C20"=>"2","RIN-R07"=>"0–4","ARC-R12"=>live?d!.Mana.ToString():"X",_=>""};
        if(c.SourceCardId=="ARC-U14"&&live&&Arsenal.Ids.All(d!.ProjectedArmsResolvedThisCombat.Contains))mana+=1;
        bool all=c.SourceCardId=="RIN-R13";if(all)mana=live?d!.Mana:0;
        bool boost=c.HasJewelChoice;int gems=c.SourceCardId switch{"RIN-U10" or "RIN-U14" or "RIN-R07"=>1,"RIN-R13"=>live?d!.Jewel:0,_=>boost?1:0};
        string gemText=c.SourceCardId=="RIN-R07"?"1–3":all?(live?gems.ToString():"X"):gems.ToString();
        bool free=boost&&live&&d!.AlphaPowers.ContainsKey("RIN-R04")&&!d.FreeJewelBoostUsed;
        return new(mana,c.PrintedManaCost>0||mana>0||all,optional,gems,gemText,boost,free,!live||d!.Jewel>=gems);
    }
    public static void Apply(NCard n)
    {
        if(n.Model is not StarterCard c){if(n.GetNodeOrNull<TextureRect>("%EnergyIcon")?.GetParent().GetNodeOrNull<Control>("ContractSecondaryCosts") is {} old)old.Visible=false;return;}
        PresentationCardSkin.CaptureLayout(n);
        if(n.GetNodeOrNull<TextureRect>("%EnergyIcon") is {} energy)
        {
            energy.Material=null;energy.SelfModulate=Colors.White;
            energy.Texture=EnergyFor(c.OwnerCharacterId=="CHAR_RIN");energy.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;energy.Position=new(-163,-227);energy.Size=new(64,64);
            var nativeLabel=n.GetNode<Control>("%EnergyLabel");nativeLabel.Position=Vector2.Zero;nativeLabel.Size=energy.Size;nativeLabel.AddThemeFontSizeOverride("font_size",38);
        }
        var host=n.GetNode<TextureRect>("%EnergyIcon").GetParent();
        var badges=host.GetNodeOrNull<Control>("ContractSecondaryCosts");
        if(badges==null){badges=new Control{Name="ContractSecondaryCosts",MouseFilter=Control.MouseFilterEnum.Ignore};host.AddChild(badges);}
        badges.Visible=n.Visibility==ModelVisibility.Visible;
        var d=ContractRuntime.For(c.Owner);var f=Facts(c,d);float x=-86;
        UpdateBadge(badges,"Mana",Mana,new(x,-215),f.ShowMana,c.SourceCardId=="RIN-R13"&&d is not {Finished:false}?"X":f.Mana.ToString(),FsnLoc.Text("UI_522148A1FDCC"),FsnLoc.Format("UI_7E8D50DCB36F", f.Mana),f.Mana<c.PrintedManaCost,d is {Finished:false}&&d.Mana<f.Mana);if(f.ShowMana)x+=49;
        UpdateBadge(badges,"OptionalMana",Mana,new(x,-215),f.OptionalMana.Length>0,f.OptionalMana,FsnLoc.Text("UI_537352400C49"),FsnLoc.Text("UI_049B64F070C1")+f.OptionalMana+FsnLoc.Text("UI_37195081B261"),false,d is {Finished:false}&&int.TryParse(f.OptionalMana,out int optional)&&d.Mana<optional);if(f.OptionalMana.Length>0)x+=49;
        UpdateBadge(badges,"Jewel",Jewel,new(x,-215),f.Jewels>0||c.SourceCardId=="RIN-R13",f.FreeBoost?"0*":f.OptionalJewel?"+"+f.JewelText:f.JewelText,f.OptionalJewel?FsnLoc.Text("UI_DCA25EDABC3F"):FsnLoc.Text("UI_80716311485A"),f.OptionalJewel?FsnLoc.Text("UI_664337C9FEB8")+(f.FreeBoost?FsnLoc.Text("UI_9FB4FF2F795D"):FsnLoc.Text("UI_0DC0FE513B60"))+(c.SourceCardId=="RIN_S_REINFORCE_PROJECTION"?FsnLoc.Text("UI_379ABDD7B91E"):""):FsnLoc.Text("UI_ADA90C0E9ABE")+f.JewelText+FsnLoc.Text("UI_D226A0F80857"),f.FreeBoost,!f.JewelAvailable);
        if(n.GetNodeOrNull<ContractCostWatch>("ContractCostWatch")==null)n.AddChild(new ContractCostWatch(n));
    }
    static void UpdateBadge(Control host,string name,Texture2D tex,Vector2 at,bool visible,string text,string caption,string tip,bool reduced,bool shortage)
    {
        var icon=host.GetNodeOrNull<TextureRect>(name);
        if(icon==null)
        {
            icon=new TextureRect{Name=name,ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,MouseFilter=Control.MouseFilterEnum.Ignore};host.AddChild(icon);
            var count=PresentationTheme.Label("",24);count.Name="Amount";count.HorizontalAlignment=HorizontalAlignment.Center;count.VerticalAlignment=VerticalAlignment.Center;count.AddThemeConstantOverride("outline_size",3);count.AddThemeColorOverride("font_outline_color",new Color("10121b"));icon.AddChild(count);
            var kind=PresentationTheme.Label("",13);kind.Name="Kind";kind.HorizontalAlignment=HorizontalAlignment.Center;kind.AddThemeConstantOverride("outline_size",3);kind.AddThemeColorOverride("font_outline_color",new Color("10121b"));icon.AddChild(kind);
        }
        icon.Texture=tex;icon.Position=at;icon.Size=new(42,42);icon.Visible=visible;icon.TooltipText=tip;
        var label=icon.GetNode<Label>("Amount");label.Text=text;label.Position=Vector2.Zero;label.Size=icon.Size;label.AddThemeFontSizeOverride("font_size",text.Length>2?17:25);label.AddThemeColorOverride("font_color",shortage?new Color("ff988f"):reduced?new Color("abefba"):PresentationTheme.Paper);
        var kindLabel=icon.GetNode<Label>("Kind");kindLabel.Text=caption+(shortage?"!":"");kindLabel.ClipText=true;kindLabel.Position=new(-4,34);kindLabel.Size=new(50,16);kindLabel.AddThemeFontSizeOverride("font_size",10);kindLabel.AddThemeColorOverride("font_color",shortage?new Color("ff988f"):PresentationTheme.Paper);
    }
    public static IEnumerable<MegaCrit.Sts2.Core.HoverTips.IHoverTip> HoverTips(StarterCard c)
    {
        var f=Facts(c,ContractRuntime.For(c.Owner));var lines=new List<string>();
        if(f.ShowMana)lines.Add(FsnLoc.Text("UI_68A107639485")+f.Mana+FsnLoc.Text("UI_2E2E0FD3BFC1"));
        if(f.OptionalMana.Length>0)lines.Add(FsnLoc.Text("UI_9EB007EDD154")+f.OptionalMana+FsnLoc.Text("UI_249B887A6361"));
        if(f.Jewels>0||c.SourceCardId=="RIN-R13")lines.Add(f.OptionalJewel?FsnLoc.Text("UI_F7567054E9F7")+(f.FreeBoost?FsnLoc.Text("UI_5287C6EFEC03"):FsnLoc.Text("UI_22099FD2AD16"))+(c.SourceCardId=="RIN_S_REINFORCE_PROJECTION"?FsnLoc.Text("UI_DCF971D1CE34"):""):FsnLoc.Text("UI_ADA90C0E9ABE")+f.JewelText+FsnLoc.Text("UI_3DF354A9AC55"));
        if(lines.Count>0)yield return new MegaCrit.Sts2.Core.HoverTips.HoverTip(EconomyNativeUi.Text(FsnLoc.Text("UI_35DF03354039")),string.Join("\n",lines)){Id="FSN_PRESENTATION_PAYMENT"};
    }
}
// Refresh visible native views only when read-only facts change; retains native upgrade-preview mode.
public sealed partial class ContractCostWatch:Node
{
    readonly NCard card;string state="";
    public ContractCostWatch(NCard n){card=n;Name="ContractCostWatch";TreeEntered+=()=>GetTree().ProcessFrame+=Tick;TreeExiting+=()=>GetTree().ProcessFrame-=Tick;}
    void Tick()
    {
        if(card.Model is not StarterCard c||!card.IsVisibleInTree())return;
        var d=ContractRuntime.For(c.Owner);var f=ContractCostArtwork.Facts(c,d);string next=$"{c.SourceCardId}:{c.IsUpgraded}:{f}:{d?.Mana}:{d?.Jewel}:{d?.Active.CharacterId}:{d?.PendingReinforcement.Active}";
        if(state==next)return;state=next;var mode=card.HasMeta("ContractPreviewMode")?(CardPreviewMode)card.GetMeta("ContractPreviewMode").AsInt32():CardPreviewMode.Normal;card.UpdateVisuals(card.DisplayingPile,mode);
    }
}
[HarmonyPatch(typeof(NCard),"UpdateEnergyCostVisuals")]
public static class ContractNativeCostRefresh
{static void Postfix(NCard __instance)=>ContractCostArtwork.Apply(__instance);}
