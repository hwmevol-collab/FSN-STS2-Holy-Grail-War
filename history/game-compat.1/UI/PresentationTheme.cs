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
        string path=Path.Combine(ContentPaths.Root,"Presentation","Assets",name);
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
        string? selected=c.SourceCardId switch
        {
            "RIN_S_GANDR"=>"review-gandr.png",
            "RIN_S_JEWEL_PREPARATION"=>"review-jewel.png",
            "RIN_S_MANA_SUPPLY"=>"review-mana.png",
            "RIN-R04"=>"review-power.png",
            "RIN_S_REINFORCEMENT"=>"review-reinforcement.png",
            "ARC_S_CLOSE_COMBAT"=>"review-melee.png",
            "ARC_S_TRACE"=>"review-trace.png",
            "ARC_S_DEFLECT"=>"review-deflect.png",
            "ARM_KANSHOU_BAKUYA"=>"review-trace.png",
            "RIN_S_REINFORCE_PROJECTION"=>"review-mana.png",
            _=>null
        };
        if(selected!=null)return Asset(selected);
        bool rin=c.OwnerCharacterId=="CHAR_RIN";
        string family=c.SourceCardId switch{
            "RIN-C05" or "RIN-C13" or "RIN-U14"=>"review-jewel.png",
            "RIN-C12" or "RIN-U12" or "RIN-U19" or "RIN-R06"=>"review-mana.png",
            "ARC-C10" or "ARC-C14" or "ARC-U16" or "ARM_RHO_AIAS"=>"review-deflect.png",
            "ARM_HRUNTING"=>"review-melee.png",
            _=>rin?(c.Type==CardType.Power?"review-power.png":c.Type==CardType.Attack?"review-gandr.png":"review-reinforcement.png"):(c.Type==CardType.Attack?"review-melee.png":"review-trace.png")};
        return Asset(family);
    }
    public static string RarityMetal(CardRarity rarity)=>rarity switch{CardRarity.Rare=>"#e7c76a",CardRarity.Uncommon=>"#86c8ee",_=>"#adadba"};
    public static string RarityName(CardRarity rarity)=>rarity switch{CardRarity.Rare=>FsnLoc.Text("UI_050C11F35AA1"),CardRarity.Uncommon=>FsnLoc.Text("UI_FFE66E93D06A"),CardRarity.Common=>FsnLoc.Text("UI_DE907D10DF98"),CardRarity.Basic=>FsnLoc.Text("UI_89E5E14C8DB9"),CardRarity.Token=>FsnLoc.Text("UI_445278D8A39D"),_=>rarity.ToString()};
    public static Texture2D Frame(StarterCard c)
    {
        bool rin=c.OwnerCharacterId=="CHAR_RIN";string accent=rin?"#e25188":"#8caec7",metal=RarityMetal(c.Rarity);
        string edge=rin?"M18 91V226M282 91V226M24 248V387L37 401M276 248V387L263 401":"M15 87V235L23 242M285 87V235L277 242M22 271V379L40 400M278 271V379L260 400";
        string insignia=rin?Diamond(150,405,5,"#df4f82",metal):"<path d='M135 405H165M146 399L154 411M154 399L146 411' stroke='#adcbdc' stroke-width='1.5'/>";
        string rare=c.Rarity==CardRarity.Rare?"<path d='M27 29L40 17H260L273 29M27 397L39 412H261L273 397' fill='none' stroke='#e7c76a' stroke-width='2'/>":c.Rarity==CardRarity.Uncommon?"<path d='M28 36H272M28 389H272' stroke='#86c8ee' opacity='.65'/>":"";
        return Svg("frame-v2-"+rin+"-"+c.Rarity,$"<defs><linearGradient id='base' x2='1' y2='1'><stop stop-color='{(rin?"#33232f":"#303d4b")}'/><stop offset='1' stop-color='#11121b'/></linearGradient></defs><path d='M22 4H278L296 22V400L278 418H22L4 400V22Z M24 88H276V239H24Z' fill='url(#base)' fill-rule='evenodd' stroke='{metal}' stroke-width='3'/><path d='M25 12H275L286 26V395L272 409H28L14 395V26Z' fill='none' stroke='{accent}' stroke-width='1.6'/><path d='M25 244H275V389L265 400H35L25 389Z' fill='{(rin?"#19121e":"#151d27")}'/><path d='{edge}' fill='none' stroke='{accent}' stroke-width='3'/><path d='M26 241H274' stroke='{metal}' stroke-width='1.5'/>{rare}{insignia}",300,422);
    }
    public static Texture2D Banner(StarterCard c)
    {
        bool rin=c.OwnerCharacterId=="CHAR_RIN";string metal=RarityMetal(c.Rarity);
        return Svg("banner-v2-"+rin+"-"+c.Rarity,$"<defs><linearGradient id='b' x2='1'><stop stop-color='{(rin?"#74263e":"#374b61")}'/><stop offset='1' stop-color='{(rin?"#381b31":"#1d2a3b")}'/></linearGradient></defs><path d='M8 1H256L264 9V38H0V9Z' fill='url(#b)'/><path d='M1 37H263' stroke='{metal}' stroke-width='2'/>",264,40);
    }
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
    static readonly string[] LayoutNodes=["Frame","TitleBanner","PortraitBorder","Portrait","TitleLabel","TypePlaque","TypeLabel","DescriptionLabel","EnergyIcon","EnergyLabel"];
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<NCard,object> captured=new();
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<NCard,SkinState> applied=new();
    sealed record SkinState(StarterCard Card,string Language,CardRarity Rarity);
    public static void CaptureLayout(NCard n)
    {
        if(captured.TryGetValue(n,out _))return;
        if(!n.IsNodeReady())return;
        captured.Add(n,new object());
        foreach(var id in LayoutNodes)if(n.GetNodeOrNull<Control>("%"+id) is {} c&&!c.HasMeta("ContractNativePosition"))
        {c.SetMeta("ContractNativePosition",c.Position);c.SetMeta("ContractNativeSize",c.Size);ContractCardTypography.Capture(c);if(c is TextureRect t)c.SetMeta("ContractNativeExpand",(int)t.ExpandMode);}
    }
    static void Prefix(NCard __instance)
    {
        applied.Remove(__instance);ContractCardTypography.Invalidate(__instance);
        foreach(var id in LayoutNodes)if(__instance.GetNodeOrNull<Control>("%"+id) is {} c&&c.HasMeta("ContractNativePosition"))
        {ContractCardTypography.Restore(c);if(c is TextureRect t)t.ExpandMode=(TextureRect.ExpandModeEnum)c.GetMeta("ContractNativeExpand").AsInt32();c.Position=c.GetMeta("ContractNativePosition").AsVector2();c.Size=c.GetMeta("ContractNativeSize").AsVector2();c.RemoveThemeFontSizeOverride("font_size");}
        foreach(var name in new[]{"ContractRarityLabel","ContractSecondaryCosts","ContractArtBackdrop"})
            if(__instance.GetNodeOrNull<TextureRect>("%EnergyIcon")?.GetParent().GetNodeOrNull<Control>(name) is {} custom)custom.Visible=false;
    }
    static void Postfix(NCard __instance)=>Apply(__instance);
    public static void Apply(NCard n)
    {
        if(!n.IsNodeReady()||n.Model is not StarterCard c)return;
        string language=MegaCrit.Sts2.Core.Localization.LocManager.Instance.Language;
        if(applied.TryGetValue(n,out var previous)&&ReferenceEquals(previous.Card,c)&&previous.Language==language&&previous.Rarity==c.Rarity)
        {
            ContractCardTypography.Apply(n);
            if(n.CardHighlight.Modulate!=NCardHighlight.red)n.CardHighlight.Modulate=c.OwnerCharacterId=="CHAR_RIN"?new Color("ed597a"):new Color("c9dfed");
            return;
        }
        applied.Remove(n);applied.Add(n,new SkinState(c,language,c.Rarity));
        CaptureLayout(n);
        bool rin=c.OwnerCharacterId=="CHAR_RIN";
        if(n.GetNodeOrNull<TextureRect>("%Frame") is {} frame){frame.Material=null;frame.SelfModulate=Colors.White;frame.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;frame.Position=new(-150,-211);frame.Size=new(300,422);}
        if(n.GetNodeOrNull<TextureRect>("%TitleBanner") is {} banner){banner.Material=null;banner.Texture=PresentationTheme.Banner(c);banner.SelfModulate=Colors.White;banner.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;banner.Position=new(-132,-166);banner.Size=new(264,40);}
        if(n.GetNodeOrNull<TextureRect>("%PortraitBorder") is {} border){border.Material=null;border.SelfModulate=Colors.White;border.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;border.Position=new(-127,-125);border.Size=new(254,149);border.Texture=PresentationTheme.Svg("portrait-v2-"+rin,$"<rect x='1' y='1' width='252' height='147' fill='none' stroke='{(rin?"#b97586":"#91adc5")}' stroke-width='1.5'/>",254,149);}
        if(n.GetNodeOrNull<TextureRect>("%Portrait") is {} art)
        {
            art.Position=new(-125,-123);art.Size=new(250,145);art.StretchMode=TextureRect.StretchModeEnum.Scale;
            if(art.GetParent().GetNodeOrNull<TextureRect>("ContractArtBackdrop")==null)
            {
                var bg=new TextureRect{Name="ContractArtBackdrop",Position=art.Position,Size=art.Size,ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,MouseFilter=Control.MouseFilterEnum.Ignore,Texture=PresentationTheme.Svg("art-bg-"+rin,"<rect width='250' height='190' fill='#18151f'/>"+PresentationTheme.Circuit(rin,125,95,80),250,190)};
                art.GetParent().AddChild(bg);art.GetParent().MoveChild(bg,0);
            }
            art.GetParent().GetNode<TextureRect>("ContractArtBackdrop").Texture=PresentationTheme.Svg("art-bg-"+rin,"<rect width='250' height='190' fill='#18151f'/>"+PresentationTheme.Circuit(rin,125,95,80),250,190);
        }
        // Typography below respects native auto-sizing instead of forcing a fixed title size.
        var rarity=n.GetNode<TextureRect>("%EnergyIcon").GetParent().GetNodeOrNull<Label>("ContractRarityLabel");
        if(rarity==null){rarity=PresentationTheme.Label("",14);rarity.Name="ContractRarityLabel";n.GetNode<TextureRect>("%EnergyIcon").GetParent().AddChild(rarity);}
        rarity.Visible=true;rarity.ClipText=true;rarity.Position=new(58,-208);rarity.Size=new(66,25);rarity.HorizontalAlignment=HorizontalAlignment.Right;rarity.Text=PresentationTheme.RarityName(c.Rarity);rarity.AddThemeFontSizeOverride("font_size",12);rarity.AddThemeColorOverride("font_color",new Color(PresentationTheme.RarityMetal(c.Rarity)));
        ContractCostArtwork.Apply(n);
        if(n.GetNodeOrNull<NinePatchRect>("%TypePlaque") is {} plaque){plaque.Material=null;plaque.Texture=PresentationTheme.Svg("type-plaque-"+rin,$"<rect x='1' y='1' width='98' height='38' fill='#211c28' stroke='{(rin?"#d6b57d":"#b7c9d5")}'/>",100,40);}
        if(n.GetNodeOrNull<Control>("%TypeLabel") is {} typeLabel)typeLabel.AddThemeColorOverride("font_color",PresentationTheme.Paper);
        if(n.CardHighlight.Modulate!=NCardHighlight.red)n.CardHighlight.Modulate=rin?new Color("ed597a"):new Color("c9dfed");
        if(n.GetNodeOrNull<Control>("%Description") is {} description)description.AddThemeColorOverride("default_color",PresentationTheme.Paper);
        if(n.GetNodeOrNull<Control>("%DescriptionLabel") is {} label)label.AddThemeColorOverride("default_color",PresentationTheme.Paper);
        ContractCardTypography.Apply(n);
    }
}
[HarmonyPatch(typeof(NCard),nameof(NCard.UpdateVisuals))]
public static class PresentationCardUpdate
{static void Postfix(NCard __instance,CardPreviewMode previewMode){__instance.SetMeta("ContractPreviewMode",(int)previewMode);PresentationCardSkin.Apply(__instance);}}

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
