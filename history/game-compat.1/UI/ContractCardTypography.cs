using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.addons.mega_text;
namespace RinArcherCore;

// Only text geometry changes. All textures, frames and portraits stay unchanged.
public static class ContractCardTypography
{
    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<NCard,TypographyState> fitted=new();
    sealed record TypographyState(string Title,string Type,string Body,Vector2 TitlePosition,Vector2 TitleSize,Vector2 TypePosition,Vector2 TypeSize,Vector2 BodyPosition,Vector2 BodySize,Vector2 PlaquePosition,Vector2 PlaqueSize);
    public static void Invalidate(NCard card)=>fitted.Remove(card);
    static TypographyState State(MegaLabel title,MegaLabel type,MegaRichTextLabel body,NinePatchRect plaque)=>new(title.Text,type.Text,body.Text,title.Position,title.Size,type.Position,type.Size,body.Position,body.Size,plaque.Position,plaque.Size);
    static readonly System.Reflection.MethodInfo FitLabel=AccessTools.Method(typeof(MegaLabel),"AdjustFontSize");
    static readonly System.Reflection.MethodInfo FitBody=AccessTools.Method(typeof(MegaRichTextLabel),"AdjustFontSize");
    public static void Capture(Control c)
    {
        if(c.HasMeta("ContractNativeAnchor"))return;
        c.SetMeta("ContractNativeAnchor",new Vector4(c.AnchorLeft,c.AnchorTop,c.AnchorRight,c.AnchorBottom));
        if(c is MegaLabel l){c.SetMeta("ContractNativeFontLimits",new Vector2I(l.MinFontSize,l.MaxFontSize));c.SetMeta("ContractNativeAutoSize",l.AutoSizeEnabled);}
        if(c is MegaRichTextLabel r){c.SetMeta("ContractNativeFontLimits",new Vector2I(r.MinFontSize,r.MaxFontSize));c.SetMeta("ContractNativeAutoSize",r.AutoSizeEnabled);}
    }
    public static void Restore(Control c)
    {
        if(!c.HasMeta("ContractNativeAnchor"))return;
        var a=c.GetMeta("ContractNativeAnchor").AsVector4();c.AnchorLeft=a.X;c.AnchorTop=a.Y;c.AnchorRight=a.Z;c.AnchorBottom=a.W;
        if(!c.HasMeta("ContractNativeFontLimits"))return;
        var f=c.GetMeta("ContractNativeFontLimits").AsVector2I();bool auto=c.GetMeta("ContractNativeAutoSize").AsBool();
        if(c is MegaLabel l){l.MinFontSize=f.X;l.MaxFontSize=f.Y;l.AutoSizeEnabled=auto;l.ClipText=false;}
        if(c is MegaRichTextLabel r){r.MinFontSize=f.X;r.MaxFontSize=f.Y;r.AutoSizeEnabled=auto;}
    }
    static void Place(Control node,Control origin,Vector2 position,Vector2 size)
    {
        node.SetAnchorsPreset(Control.LayoutPreset.TopLeft);
        var parent=(CanvasItem)node.GetParent();
        node.Position=parent.GetGlobalTransformWithCanvas().AffineInverse()*(origin.GetGlobalTransformWithCanvas()*position);
        node.CustomMinimumSize=Vector2.Zero;node.Size=size;
    }
    public static void Apply(NCard card)
    {
        if(card.Model is not StarterCard||card.GetNodeOrNull<TextureRect>("%Frame")?.GetParent() is not Control origin)return;
        var currentTitle=card.GetNodeOrNull<MegaLabel>("%TitleLabel");var currentType=card.GetNodeOrNull<MegaLabel>("%TypeLabel");var currentBody=card.GetNodeOrNull<MegaRichTextLabel>("%DescriptionLabel");var currentPlaque=card.GetNodeOrNull<NinePatchRect>("%TypePlaque");
        if(currentTitle!=null&&currentType!=null&&currentBody!=null&&currentPlaque!=null&&fitted.TryGetValue(card,out var last)&&last==State(currentTitle,currentType,currentBody,currentPlaque))return;
        if(currentTitle is {} title)
        {
            title.AutoSizeEnabled=true;title.MinFontSize=12;title.MaxFontSize=25;
            title.ClipText=true;title.HorizontalAlignment=HorizontalAlignment.Center;title.VerticalAlignment=VerticalAlignment.Center;
            Place(title,origin,new(-120,-159),new(240,30));FitLabel.Invoke(title,null);
        }
        if(card.GetNodeOrNull<NinePatchRect>("%TypePlaque") is {} plaque&&card.GetNodeOrNull<MegaLabel>("%TypeLabel") is {} type)
        {
            type.AutoSizeEnabled=true;type.MinFontSize=14;type.MaxFontSize=20;type.ClipText=true;
            type.HorizontalAlignment=HorizontalAlignment.Center;type.VerticalAlignment=VerticalAlignment.Center;
            float width=Mathf.Clamp(type.GetThemeFont("font").GetStringSize(type.Text,fontSize:20).X+24,64,108);
            Place(plaque,origin,new(-width*.5f,16),new(width,34));
            Place(type,origin,new(-width*.5f+6,18),new(width-12,28));FitLabel.Invoke(type,null);
        }
        if(card.GetNodeOrNull<MegaRichTextLabel>("%DescriptionLabel") is {} body)
        {
            body.FitContent=false;body.AutoSizeEnabled=true;body.MinFontSize=14;body.MaxFontSize=22;
            body.IsVerticallyBound=true;body.IsHorizontallyBound=true;body.ScrollActive=false;
            Place(body,origin,new(-120,53),new(240,146));
            body.AddThemeConstantOverride("line_separation",0);body.AddThemeConstantOverride("paragraph_separation",1);
            FitBody.Invoke(body,null);
        }
        if(currentTitle!=null&&currentType!=null&&currentBody!=null&&currentPlaque!=null){fitted.Remove(card);fitted.Add(card,State(currentTitle,currentType,currentBody,currentPlaque));}
    }
}
[HarmonyPatch(typeof(NCard),"UpdateTypePlaqueSizeAndPosition")]
public static class ContractDeferredTypeAlignment
{static void Postfix(NCard __instance)=>ContractCardTypography.Apply(__instance);}
