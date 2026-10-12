using System.Globalization;
using MegaCrit.Sts2.Core.Nodes.Cards;
namespace RinArcherCore;

// Presentation assets belong only to this local research candidate.
public static class PresentationTheme
{
    public static readonly Color Ink=new("111018"),Paper=new("f4e9d7"),Muted=new("c6b9aa"),Rin=new("d63155"),Archer=new("b93943"),Silver=new("c1d0db"),Gold=new("d6b57d");
    static readonly Dictionary<string,Texture2D> textures=[];
    public static Texture2D Asset(string name)
    {
        if(textures.TryGetValue(name,out var tex))return tex;
        string path=Path.Combine(Path.GetDirectoryName(typeof(PresentationTheme).Assembly.Location)!,"Presentation","Assets",name);
        var img=Image.LoadFromFile(path);if(img==null||img.IsEmpty())throw new InvalidOperationException("Missing prototype asset: "+name);
        return textures[name]=ImageTexture.CreateFromImage(img);
    }
    public static Texture2D Svg(string key,string body,int width=300,int height=430)
    {
        if(textures.TryGetValue(key,out var tex))return tex;
        var img=new Image();var error=img.LoadSvgFromString($"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>{body}</svg>");
        if(error!=Error.Ok)throw new InvalidOperationException("Prototype vector texture: "+error);
        return textures[key]=ImageTexture.CreateFromImage(img);
    }
    public static string Diamond(float x,float y,float r,string fill,string stroke="none")
        =>$"<path d='M{x} {y-r} L{x+r} {y} L{x} {y+r} L{x-r} {y} Z' fill='{fill}' stroke='{stroke}' stroke-width='2'/>";
    public static string Circuit(bool rin,float cx=150,float cy=130,float r=92)
    {
        string accent=rin?"#d63155":"#a7c8df";
        var b=new System.Text.StringBuilder($"<g fill='none' stroke='{accent}' stroke-width='1.4' opacity='.7'><circle cx='{cx}' cy='{cy}' r='{r}'/><circle cx='{cx}' cy='{cy}' r='{r-10}'/>");
        for(int i=0;i<12;i++){double a=i*Math.PI/6;float x=cx+(float)Math.Cos(a)*r,y=cy+(float)Math.Sin(a)*r,x2=cx+(float)Math.Cos(a)*(r-18),y2=cy+(float)Math.Sin(a)*(r-18);b.Append(FormattableString.Invariant($"<path d='M{x} {y} L{x2} {y2}'/>"));}
        b.Append($"<path d='M{cx-r*.8f} {cy+r*.45f} L{cx} {cy-r*.9f} L{cx+r*.8f} {cy+r*.45f} Z'/></g>");return b.ToString();
    }
    public static Texture2D Portrait(StarterCard c)
    {
        bool rin=c.OwnerCharacterId=="CHAR_RIN";
        string scene=c.SourceCardId switch
        {
            "RIN_S_GANDR" or "RIN_S_JEWEL_RELEASE"=>"rin_gandr",
            "ARC_S_TRACE" or "ARC_S_RELOAD"=>"archer_projection",
            "ARM_KANSHOU_BAKUYA" or "ARC_S_CLOSE_COMBAT"=>"archer_cut",
            _=>rin?(c.Type==CardType.Power?"rin_power":c.Type==CardType.Attack?"rin_gandr":"rin_jewel"):(c.Type==CardType.Power?"archer_power":c.Type==CardType.Attack?"archer_cut":"archer_projection")
        };
        return Asset(scene+".png");
    }
    public static Texture2D Frame(StarterCard c)
    {
        bool rin=c.OwnerCharacterId=="CHAR_RIN";string accent=rin?"#d63155":"#ba424d",metal=rin?"#d6b57d":"#b7c9d5";
        string key="frame-"+rin+"-"+c.Type;
        string motif=c.Type switch{CardType.Attack=>"<path d='M24 34L38 20M28 20L38 30' stroke='#f4e9d7' stroke-width='3'/>",CardType.Power=>"<circle cx='30' cy='27' r='8' fill='none' stroke='#f4e9d7' stroke-width='2'/><path d='M30 14V40M17 27H43' stroke='#f4e9d7'/>",_=>Diamond(30,27,9,"none","#f4e9d7")};
        return Svg(key,$"<defs><linearGradient id='base' x2='1' y2='1'><stop stop-color='#29222b'/><stop offset='1' stop-color='#100e15'/></linearGradient><linearGradient id='red'><stop stop-color='#310e1b'/><stop offset='.6' stop-color='{accent}'/><stop offset='1' stop-color='#39141c'/></linearGradient></defs><path d='M20 4H280L296 22V408L280 426H20L4 408V22Z M24 54H276V223H24Z' fill='url(#base)' fill-rule='evenodd' stroke='{metal}' stroke-width='3'/><path d='M23 12H277L287 24V401L275 416H25L13 401V24Z' fill='none' stroke='{accent}' stroke-width='1.5'/><path d='M20 224H280V398L272 407H28L20 398Z' fill='#14121a'/><path d='M14 14H286V54H14Z' fill='url(#red)'/><path d='M21 223H279M28 230H272' stroke='{metal}' opacity='.7'/><path d='M16 70V210M284 70V210' stroke='{accent}' stroke-width='3'/>{motif}{Diamond(150,414,8,accent,metal)}<path d='M34 395H115M185 395H266' stroke='{metal}' stroke-width='1'/>");
    }
    public static Texture2D Banner(bool rin)=>Svg("banner-"+rin,$"<path d='M0 0H300V46H0Z' fill='{(rin?"#501827":"#351b24")}'/><path d='M0 44H300' stroke='{(rin?"#d6b57d":"#b7c9d5")}' stroke-width='2'/>",300,46);
    public static StyleBoxFlat Box(Color border,Color? background=null,int pad=16)
    {
        var box=new StyleBoxFlat{BgColor=background??Ink,BorderColor=border,BorderWidthLeft=1,BorderWidthRight=1,BorderWidthTop=1,BorderWidthBottom=1,CornerRadiusTopLeft=5,CornerRadiusTopRight=5,CornerRadiusBottomLeft=5,CornerRadiusBottomRight=5,ContentMarginLeft=pad,ContentMarginRight=pad,ContentMarginTop=pad,ContentMarginBottom=pad,ShadowColor=new(0,0,0,.4f),ShadowSize=8};return box;
    }
    public static void Button(Button b,bool primary=false)
    {
        b.AddThemeStyleboxOverride("normal",Box(primary?Rin:Gold,primary?new Color("391522"):new Color("1d1a24"),12));
        b.AddThemeStyleboxOverride("hover",Box(Paper,new Color("492030"),12));b.AddThemeStyleboxOverride("pressed",Box(Gold,new Color("662639"),12));
        var focus=Box(Paper,new Color(0,0,0,0),12);focus.BorderWidthLeft=focus.BorderWidthRight=focus.BorderWidthTop=focus.BorderWidthBottom=2;b.AddThemeStyleboxOverride("focus",focus);
        b.AddThemeStyleboxOverride("disabled",Box(new Color("62565c"),new Color("19161d"),12));
        b.AddThemeColorOverride("font_color",Paper);b.AddThemeColorOverride("font_hover_color",Colors.White);b.AddThemeColorOverride("font_focus_color",Paper);b.AddThemeColorOverride("font_pressed_color",Paper);b.AddThemeColorOverride("font_disabled_color",new Color("a29498"));b.AddThemeFontSizeOverride("font_size",20);
    }
    public static Label Label(string text,int size=18,Color? color=null)
    {var l=new Label{Text=text,MouseFilter=Control.MouseFilterEnum.Ignore};l.AddThemeFontSizeOverride("font_size",size);l.AddThemeColorOverride("font_color",color??Paper);return l;}
}

[HarmonyPatch(typeof(NCard),"Reload")]
public static class PresentationCardSkin
{
    static void Postfix(NCard __instance)=>Apply(__instance);
    public static void Apply(NCard n)
    {
        if(!n.IsNodeReady()||n.Model is not StarterCard c)return;
        bool rin=c.OwnerCharacterId=="CHAR_RIN";
        if(n.GetNodeOrNull<TextureRect>("%Frame") is {} frame){frame.Material=null;frame.SelfModulate=Colors.White;}
        if(n.GetNodeOrNull<TextureRect>("%TitleBanner") is {} banner){banner.Material=null;banner.Texture=PresentationTheme.Banner(rin);}
        if(n.GetNodeOrNull<TextureRect>("%PortraitBorder") is {} border){border.Material=null;border.SelfModulate=Colors.White;border.Texture=PresentationTheme.Svg("portrait-rim-"+rin,$"<path d='M10 4H265V204H10Z' fill='none' stroke='{(rin?"#d6b57d":"#b7c9d5")}' stroke-width='2'/>",275,210);}
        if(n.GetNodeOrNull<TextureRect>("%Portrait") is {} art)
        {
            art.Position=new(-125,-123);art.Size=new(250,145);art.StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered;
            if(art.GetParent().GetNodeOrNull<TextureRect>("ContractArtBackdrop")==null)
            {
                var bg=new TextureRect{Name="ContractArtBackdrop",Position=art.Position,Size=art.Size,ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,MouseFilter=Control.MouseFilterEnum.Ignore,Texture=PresentationTheme.Svg("art-bg-"+rin,"<rect width='250' height='190' fill='#18151f'/>"+PresentationTheme.Circuit(rin,125,95,80),250,190)};
                art.GetParent().AddChild(bg);art.GetParent().MoveChild(bg,0);
            }
            art.GetParent().GetNode<TextureRect>("ContractArtBackdrop").Texture=PresentationTheme.Svg("art-bg-"+rin,"<rect width='250' height='190' fill='#18151f'/>"+PresentationTheme.Circuit(rin,125,95,80),250,190);
        }
        if(n.GetNodeOrNull<TextureRect>("%EnergyIcon") is {} energy)energy.Texture=PresentationTheme.Svg("energy-gem-"+rin,$"<path d='M32 1L59 17V47L32 63L5 47V17Z' fill='#21131f' stroke='{(rin?"#d63155":"#b7c9d5")}' stroke-width='3'/><path d='M32 7L53 20V44L32 57L11 44V20Z' fill='none' stroke='#d6b57d' stroke-width='1'/>",64,64);
        if(n.GetNodeOrNull<NinePatchRect>("%TypePlaque") is {} plaque){plaque.Material=null;plaque.Texture=PresentationTheme.Svg("type-plaque-"+rin,$"<rect x='1' y='1' width='98' height='38' fill='#211c28' stroke='{(rin?"#d6b57d":"#b7c9d5")}'/>",100,40);}
        if(n.GetNodeOrNull<Control>("%TypeLabel") is {} typeLabel)typeLabel.AddThemeColorOverride("font_color",PresentationTheme.Paper);
        n.CardHighlight.Modulate=rin?new Color("ed597a"):new Color("c9dfed");
        if(n.GetNodeOrNull<Control>("%Description") is {} description)description.AddThemeColorOverride("default_color",PresentationTheme.Paper);
        if(n.GetNodeOrNull<Control>("%DescriptionLabel") is {} label)label.AddThemeColorOverride("default_color",PresentationTheme.Paper);
    }
}
[HarmonyPatch(typeof(NCard),nameof(NCard.UpdateVisuals))]
public static class PresentationCardUpdate
{static void Postfix(NCard __instance)=>PresentationCardSkin.Apply(__instance);}

[HarmonyPatch]
public static class PresentationNativeHighlight
{
    static IEnumerable<System.Reflection.MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(NCardHighlight),nameof(NCardHighlight.AnimShow)),AccessTools.Method(typeof(NCardHighlight),nameof(NCardHighlight.AnimFlash))};
    static void Prefix(NCardHighlight __instance)
    {
        Node? p=__instance.GetParent();while(p!=null&&p is not NCard)p=p.GetParent();
        if(p is NCard {Model:StarterCard c}&&__instance.Modulate!=NCardHighlight.red)__instance.Modulate=c.OwnerCharacterId=="CHAR_RIN"?new Color("ed597a"):new Color("c9dfed");
    }
}
