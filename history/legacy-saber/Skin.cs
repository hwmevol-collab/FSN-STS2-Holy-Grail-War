using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.TestSupport;
namespace FateStayNight;

// All modifications are scoped to FSN models. NCard nodes are pooled by the game.
public static class Skin
{
    static readonly Dictionary<string,Texture2D> SvgCache=[];
    sealed record PortraitState(Material? Material,TextureRect.StretchModeEnum Stretch,TextureRect.ExpandModeEnum Expand, Color Highlight, Vector2 Position, Vector2 Size);
    static readonly ConditionalWeakTable<NCard,PortraitState> Original=new();
    static readonly Dictionary<Texture2D,Texture2D> Standalone=[];
    static T Field<T>(object node,string field)=> (T)AccessTools.Field(node.GetType(),field).GetValue(node)!;
    static Texture2D Svg(string key,int width,int height,string body){
        if(SvgCache.TryGetValue(key,out var texture))return texture;
        var im=new Image();im.LoadSvgFromString($"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{body}</svg>");
        return SvgCache[key]=ImageTexture.CreateFromImage(im);
    }
    static readonly Shader FitShader=new(){Code="""
        shader_type canvas_item;
        varying vec4 vertex_tint;
        void vertex(){vertex_tint=COLOR;}
        uniform float source_aspect = 1.0;
        uniform float window_aspect = 1.70068;
        void fragment() {
            vec2 span = source_aspect > window_aspect ? vec2(window_aspect/source_aspect,1.0) : vec2(1.0,source_aspect/window_aspect);
            // Favor faces and weapons in the upper half of the illustration.
            vec2 center=vec2(0.5,max(span.y*0.5,0.40));
            vec2 p=(UV-0.5)*span+center;
            COLOR=texture(TEXTURE,p)*vertex_tint;
        }
        """};
    public static void Card(NCard node){
        if(TestMode.IsOn||!node.IsNodeReady())return;
        var portrait=Field<TextureRect>(node,"_portrait");
        if(node.Model is not FateCard){if(Original.TryGetValue(node,out var old)){portrait.Material=old.Material;portrait.StretchMode=old.Stretch;portrait.ExpandMode=old.Expand;node.CardHighlight.Modulate=old.Highlight;portrait.Position=old.Position;portrait.Size=old.Size;Original.Remove(node);}return;}
        if(!Original.TryGetValue(node,out _))Original.Add(node,new(portrait.Material,portrait.StretchMode,portrait.ExpandMode,node.CardHighlight.Modulate,portrait.Position,portrait.Size));
        // Compose the artwork inside the visible area below the native title banner.
        portrait.Position=new(-125,-124);portrait.Size=new(250,147);
        portrait.ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize;portrait.StretchMode=TextureRect.StretchModeEnum.Scale;
        if(node.Visibility==MegaCrit.Sts2.Core.Entities.UI.ModelVisibility.Visible&&portrait.Texture is {} t){
            // Atlas UVs are a subrectangle of the source sheet. Give this shader a standalone native region texture.
            if(t is AtlasTexture atlas){if(!Standalone.TryGetValue(t,out var region)){region=ImageTexture.CreateFromImage(atlas.Atlas.GetImage().GetRegion(new Rect2I((Vector2I)atlas.Region.Position,(Vector2I)atlas.Region.Size)));Standalone[t]=region;}portrait.Texture=t=region;}
            var mat=new ShaderMaterial{Shader=FitShader};mat.SetShaderParameter("source_aspect",(float)t.GetWidth()/t.GetHeight());portrait.Material=mat;
        }
        if(node.Model is not FateCard)return;
        Highlight(node);
        bool saber=node.Model is SwiftStrike or SwordGuard or LuckyProtection;
        bool rare=node.Model.Rarity==CardRarity.Rare;
        string edge=rare?"#f1ce86":saber?"#a5cce9":"#83bcad",accent=saber?"#77c9ff":"#65ebbd";
        string palette=saber?"saber":"master", cache=palette+(rare?"Rare":"Normal");
        string defs=$"<defs><linearGradient id='metal' x2='1' y2='1'><stop stop-color='#f2e4c0'/><stop offset='.28' stop-color='{edge}'/><stop offset='.55' stop-color='#354755'/><stop offset='.8' stop-color='{edge}'/><stop offset='1' stop-color='#d8eaf1'/></linearGradient><linearGradient id='body' x2='0' y2='1'><stop stop-color='{(saber?"#162f50":"#193a33")}'/><stop offset='1' stop-color='#080f1c'/></linearGradient></defs>";
        string detail=saber?"<path d='M24 278L41 290 34 310 M276 278L259 290 266 310 M37 376L61 397H104 M263 376L239 397H196 M135 398L150 388 165 398 150 408Z'/>":"<path d='M24 280H38V300L49 311 M276 280H262V300L251 311 M28 365V389H57L65 397H108 M272 365V389H243L235 397H192 M140 397L150 387 160 397 150 407Z'/>";
        var frame=Field<TextureRect>(node,"_frame");frame.Material=null;
        frame.Texture=Svg(cache+"Frame",300,422,defs+$"<path d='M20 3H280L296 19V399L278 419H22L4 399V19Z M25 43V233H275V43Z' fill='url(#body)' fill-rule='evenodd' stroke='url(#metal)' stroke-width='4'/><path d='M18 248H282 M24 410H276' stroke='{edge}' stroke-width='1' opacity='.65'/><g fill='none' stroke='{accent}' stroke-width='1' opacity='.55'>{detail}</g><path d='M10 35V18L22 8H74 M226 8H278L290 18V35 M10 385V398L22 411 M290 385V398L278 411' fill='none' stroke='{accent}' stroke-width='2'/>");
        var border=Field<TextureRect>(node,"_portraitBorder");border.Material=null;
        border.Texture=Svg(cache+"Border",275,210,defs+$"<path d='M13 3H262V193H13Z' fill='none' stroke='url(#metal)' stroke-width='4'/><path d='M16 7H74 M202 7H259 M16 189H50 M225 189H259' stroke='{accent}' stroke-width='1'/>");
        var banner=Field<TextureRect>(node,"_banner");banner.Material=null;
        banner.Texture=Svg(cache+"Banner",327,83,defs+$"<path d='M5 19L22 10H305L322 19 312 66 302 73H25L15 66Z' fill='url(#body)' stroke='url(#metal)' stroke-width='2'/><path d='M25 16H302 M29 66H298' stroke='{accent}' stroke-width='1' opacity='.65'/>");
        Field<TextureRect>(node,"_energyIcon").Texture=Cost(saber);
        var plaque=Field<NinePatchRect>(node,"_typePlaque");plaque.Material=null;
        plaque.Texture=Svg(cache+"Plaque",100,34,$"<path d='M10 2H90L98 17 90 32H10L2 17Z' fill='#acc5d0' stroke='{edge}' stroke-width='2'/>");
    }
    public static void Highlight(NCard node){if(node.Model is not FateCard)return;node.CardHighlight.Modulate=node.Model is SwiftStrike or SwordGuard or LuckyProtection?new Color(.52f,.72f,1f,.48f):new Color(.38f,.95f,.75f,.48f);}
    static Texture2D Cost(bool saber)=>Svg(saber?"saberCost":"masterCost",64,64,$"<defs><radialGradient id='gem'><stop stop-color='{(saber?"#347fc0":"#278a70")}'/><stop offset='.7' stop-color='#102c3b'/><stop offset='1' stop-color='#080e19'/></radialGradient></defs><path d='M32 2L54 11 62 32 54 53 32 62 10 53 2 32 10 11Z' fill='url(#gem)' stroke='#dfcd9c' stroke-width='2'/><circle cx='32' cy='32' r='23' fill='none' stroke='{(saber?"#84d6ff":"#85ffcd")}' stroke-width='1'/><path d='M32 3V9 M32 55V61 M3 32H9 M55 32H61' stroke='#fff1c8' stroke-width='2'/>");

    public static void RefreshEnergy(Duo d){
        if(TestMode.IsOn||Art.Find<NEnergyCounter>() is not {} counter)return;
        var root=counter.GetNodeOrNull<TextureRect>("FSNEnergy");
        if(root==null){
            foreach(string field in new[]{"_layers","_rotationLayers","_backVfx","_frontVfx"})if(AccessTools.Field(typeof(NEnergyCounter),field).GetValue(counter) is CanvasItem canvas)canvas.Visible=false;
            root=new TextureRect{Name="FSNEnergy",Position=new(-74,-74),Size=new(148,148),ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered,MouseFilter=Control.MouseFilterEnum.Ignore};counter.AddChild(root);counter.MoveChild(root,0);
        }
        root.Texture=Energy(d.IsSaber);root.Modulate=d.Player.PlayerCombatState?.Energy==0?new Color("727a81"):Colors.White;
        if(AccessTools.Field(typeof(NEnergyCounter),"_label").GetValue(counter) is Control label){root.Position=label.Position+label.Size/2-root.Size/2;counter.MoveChild(label,counter.GetChildCount()-1);}
    }
    static Texture2D Energy(bool saber)=>Svg(saber?"saberEnergy":"masterEnergy",160,160,$"<defs><radialGradient id='e'><stop stop-color='{(saber?"#295887":"#235b50")}'/><stop offset='.65' stop-color='#102331'/><stop offset='1' stop-color='#060f1e'/></radialGradient></defs><circle cx='80' cy='80' r='69' fill='url(#e)' stroke='#d0bd8c' stroke-width='2'/><circle cx='80' cy='80' r='62' fill='none' stroke='{(saber?"#7ccaff":"#6cdeb2")}' stroke-width='2'/><circle cx='80' cy='80' r='75' fill='none' stroke='#8cacc5' stroke-width='1' stroke-dasharray='18 7 2 7'/><path d='M80 1L88 14 80 31 72 14Z M80 159L72 146 80 129 88 146Z M1 80L14 72 31 80 14 88Z M159 80L146 88 129 80 146 72Z' fill='#b9ced9' stroke='#eed59b' stroke-width='1'/><path d='M33 38L48 38 48 48 M127 38H112V48 M33 122H48V112 M127 122H112V112' fill='none' stroke='{(saber?"#7ccaff":"#6cdeb2")}' stroke-width='2'/>");
    public static void SelectionBackdrop(Control board){
        board.AddChild(new TextureRect{Name="FSNKeyVisual",Texture=Art.Texture("SelectionV3"),Position=new(480,0),Size=new(1700,1200),ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,StretchMode=TextureRect.StretchModeEnum.KeepAspectCovered,MouseFilter=Control.MouseFilterEnum.Ignore});
        var atmosphere=new ContractAtmosphere{Name="FSNSelectionAtmosphere",Selection=true};board.AddChild(atmosphere);atmosphere.Start();
        board.Modulate=new Color(1,1,1,0);
        board.CreateTween().TweenProperty(board,"modulate:a",1.0,.65).SetTrans(Tween.TransitionType.Sine);
    }

}
[HarmonyPatch(typeof(NCard),"Reload")]
public static class FsnCardSkinPatch{static void Postfix(NCard __instance)=>Skin.Card(__instance);}
[HarmonyPatch(typeof(NEnergyCounter),"RefreshLabel")]
public static class FsnEnergySkinPatch{static void Postfix(NEnergyCounter __instance){var p=(Player)AccessTools.Field(typeof(NEnergyCounter),"_player").GetValue(__instance)!;if(p.Character is EmiyaShirou&&Duo.For(p) is {} d)Skin.RefreshEnergy(d);}}
[HarmonyPatch]
public static class FsnCardHighlightPatch{
    static IEnumerable<System.Reflection.MethodBase> TargetMethods()=>new[]{nameof(NCardHighlight.AnimShow),nameof(NCardHighlight.AnimFlash)}.Select(n=>AccessTools.Method(typeof(NCardHighlight),n));
    static void Prefix(NCardHighlight __instance){Node? parent=__instance.GetParent();while(parent!=null&&parent is not NCard)parent=parent.GetParent();if(parent is NCard card&&card.Model is FateCard)Skin.Highlight(card);}
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Nodes.Cards.Holders.NHandCardHolder),"UpdateCard")]
public static class FsnHandHighlightPatch{static void Postfix(MegaCrit.Sts2.Core.Nodes.Cards.Holders.NHandCardHolder __instance){if(__instance.CardNode is {} node)Skin.Highlight(node);}}

