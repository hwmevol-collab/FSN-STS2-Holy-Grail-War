using MegaCrit.Sts2.Core.Nodes.CommonUi;
namespace RinArcherCore;
public static class PresentationCopy
{
    public static string CardRules(string rules,StarterCard card,ContractRuntime? runtime)
    {
        string text=Rules(rules);
        if(!FsnLoc.Chinese){if(card.SourceCardId=="RIN-U19")text=text.Replace("Spend "+card.PrintedManaCost+" Mana. ","");if(card.SourceCardId is "RIN-U10" or "RIN-U14")text=text.Replace("Spend 1 Jewel. ","");return text.Replace("Jewel Boost:","\n[color=#efd3a2]Jewel Boost[/color]:");}
        // Only the redundant appended fixed-price line is removed. Choice/conditional payments stay explained.
        text=System.Text.RegularExpressions.Regex.Replace(text,@"\n魔力费用：\d+。","");
        if(card.SourceCardId=="RIN-U19")text=text.Replace("消耗"+card.PrintedManaCost+"点契约魔力。","");
        if(card.SourceCardId is "RIN-U10" or "RIN-U14")text=text.Replace("花费1枚宝石，","");
        text=text.Replace("宝石强化：","[color=#efd3a2]宝石强化[/color]：");
        return text;
    }
    // Presentation wording only; locked effects, numbers and payment stay in GameplayCatalog.
    public static string Rules(string text)=>text.Replace("契约魔力费用：","魔力费用：").Replace("选择一项：\n· ","选择：\n").Replace("\n· ","\n").Replace("。宝石强化：","。\n宝石强化：");
}
public static class DeckTabStyle
{
    public static void Apply(NPopupYesNoButton button,bool selected)
    {
        // Keep native hitbox, focus navigation and controller shortcuts; replace only the green face.
        bool rin=button.Name=="ContractRinDeckTab";
        var face=PresentationTheme.Svg("deck-tab-v2-"+rin+selected,"<path d='M8 2H198L208 12V38L198 46H8L2 40V8Z' fill='"+(selected?(rin?"#55283e":"#32495f"):"#252932")+"' stroke='"+(selected?(rin?"#eaa0b9":"#adcbe2"):"#8194a7")+"' stroke-width='1.5'/>",210,48);
        var visuals=button.GetNode<Control>("Visuals");visuals.CustomMinimumSize=Vector2.Zero;visuals.Position=Vector2.Zero;
        foreach(var t in Descendants(visuals).OfType<TextureRect>()){t.Material=null;t.SelfModulate=Colors.White;t.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;t.Texture=face;t.StretchMode=TextureRect.StretchModeEnum.Scale;t.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);}
        foreach(var l in Descendants(button).OfType<Label>()){l.CustomMinimumSize=Vector2.Zero;if(l is MegaCrit.Sts2.addons.mega_text.MegaLabel mega){mega.AutoSizeEnabled=false;mega.MinFontSize=23;mega.MaxFontSize=23;}l.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);l.HorizontalAlignment=HorizontalAlignment.Center;l.VerticalAlignment=VerticalAlignment.Center;l.AddThemeFontSizeOverride("font_size",23);l.AddThemeColorOverride("font_color",PresentationTheme.Paper);l.AddThemeConstantOverride("outline_size",2);}
        visuals.Size=new(210,48);
    }
    static IEnumerable<Node> Descendants(Node n){yield return n;foreach(var child in n.GetChildren())foreach(var c in Descendants(child))yield return c;}
}
