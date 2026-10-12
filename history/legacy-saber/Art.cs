using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.TestSupport;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Nodes.Relics;
namespace FateStayNight;
public static class Art
{
    static readonly Dictionary<string,Texture2D> Textures=[];
    public static string Directory=>System.IO.Path.Combine(System.IO.Path.GetDirectoryName(typeof(Art).Assembly.Location)!,"assets");
    public static Texture2D? Texture(string key){
        if(TestMode.IsOn)return null;
        if(Textures.TryGetValue(key,out var texture))return texture;
        string[] masterCards=[nameof(PosterStrike),nameof(QuickDodge),nameof(Reinforcement),nameof(StructuralAnalysis),nameof(Coordination),nameof(DesperateFlight)];
        string[] fateCards=[nameof(CounterfeitLife),nameof(Precaution),nameof(PaperShield),nameof(FateNight),nameof(LuckyProtection),nameof(GemWind),nameof(SwiftStrike),nameof(SwordGuard)];
        int masterIndex=Array.IndexOf(masterCards,key), fateIndex=Array.IndexOf(fateCards,key);
        if(masterIndex>=0&&Texture("MasterAtlasV3") is {} masters)return Textures[key]=Cell(masters,masterIndex,3,2);
        if(fateIndex>=0&&Texture("FateAtlasV3") is {} fates)return Textures[key]=FateCell(fates,fateIndex);
        if(key is "ShirouBattle" or "SaberBattle"&&Texture("FightersV3") is {} fighters)return Textures[key]=Cell(fighters,key=="ShirouBattle"?0:1,2,1);
        if(key is "ShirouFace" or "SaberFace"&&Texture("FightersV3") is {} faces){
            var region=key=="ShirouFace"?new Rect2(.22f,.025f,.115f,.245f):new Rect2(.675f,.07f,.112f,.24f);
            return Textures[key]=new AtlasTexture{Atlas=faces,Region=new Rect2(region.Position*faces.GetSize(),region.Size*faces.GetSize())};
        }
        if(key is nameof(Reinforcement) or nameof(SwiftStrike)&&Texture(key+"V2") is {} sample)return Textures[key]=sample;
        if(key is "ShirouFace" or "SaberFace"&&Texture(key=="ShirouFace"?"ShirouIcon":"SaberIcon") is {} face)return Textures[key]=new AtlasTexture{Atlas=face,Region=new Rect2(0,0,face.GetWidth(),Math.Min(100,face.GetHeight()))};
        int quadrant=key switch{nameof(PosterStrike)=>0,nameof(Reinforcement)=>1,nameof(StructuralAnalysis)=>2,nameof(PaperShield)=>3,_=>-1};
        if(quadrant>=0&&Texture("SpellAtlas") is {} atlas){float w=atlas.GetWidth()/2f,h=atlas.GetHeight()/2f;return Textures[key]=new AtlasTexture{Atlas=atlas,Region=new Rect2((quadrant%2)*w,(quadrant/2)*h,w,h)};}
        if(key is nameof(QuickDodge) or nameof(DesperateFlight)&&Texture("DodgeAtlas") is {} dodge){float w=dodge.GetWidth()/2f;return Textures[key]=new AtlasTexture{Atlas=dodge,Region=new Rect2(key==nameof(QuickDodge)?0:w,0,w,dodge.GetHeight())};}
        string path=System.IO.Path.Combine(Directory,key+".png");
        if(!System.IO.File.Exists(path))path=System.IO.Path.Combine(Directory,key+".jpg");
        if(!System.IO.File.Exists(path))return null;
        var image=Image.LoadFromFile(path);if(image.IsEmpty())return null;
        return Textures[key]=ImageTexture.CreateFromImage(image);
    }
    static AtlasTexture FateCell(Texture2D atlas,int index){
        float[] rows=[0,.3145f,.6643f,1];int row=index/3;
        return new AtlasTexture{Atlas=atlas,Region=new Rect2(index%3*atlas.GetWidth()/3f,rows[row]*atlas.GetHeight(),atlas.GetWidth()/3f,(rows[row+1]-rows[row])*atlas.GetHeight())};
    }
    static AtlasTexture Cell(Texture2D atlas,int index,int columns,int rows){float w=atlas.GetWidth()/(float)columns,h=atlas.GetHeight()/(float)rows;return new AtlasTexture{Atlas=atlas,Region=new Rect2(index%columns*w,index/columns*h,w,h)};}
    public static T? Find<T>(Node? root=null) where T:Node{
        root??=NGame.Instance?.GetTree()?.Root;if(root==null)return null;
        if(root is T t)return t;
        foreach(var child in root.GetChildren())if(Find<T>(child) is {} found)return found;
        return null;
    }
    static Label? Status;
    static VBoxContainer? Choices;
    public static Texture2D? Icon(string key){
        if(TestMode.IsOn)return null;
        string cache="icon:"+key;if(Textures.TryGetValue(cache,out var texture))return texture;
        string[] relicKeys=[nameof(CommandSeals),nameof(WindBarrier),nameof(KingsArmor),nameof(OldHeater),nameof(EmiyaHouse),nameof(Avalon)];
        int relicIndex=Array.IndexOf(relicKeys,key);
        if(relicIndex>=0&&Texture("RelicsV3") is {} relicAtlas){
            var region=Cell(relicAtlas,relicIndex,3,2).Region;
            var medallion=relicAtlas.GetImage().GetRegion(new Rect2I((Vector2I)region.Position,(Vector2I)region.Size));
            medallion.Convert(Image.Format.Rgba8);medallion.Resize(192,192,Image.Interpolation.Lanczos);
            // Native inventory uses small cutout icons: enclose the art in an octagonal metal setting.
            for(int y=0;y<192;y++)for(int x=0;x<192;x++){
                float dx=Mathf.Abs(x-95.5f),dy=Mathf.Abs(y-95.5f);
                float distance=Mathf.Max(Mathf.Max(dx,dy)/93,(dx+dy)/151);
                if(distance>1)medallion.SetPixel(x,y,Colors.Transparent);
                else if(distance>.977f)medallion.SetPixel(x,y,new Color("cbbd96"));
            }
            return Textures[cache]=ImageTexture.CreateFromImage(medallion);
        }
        if(key is nameof(WindBarrier) or nameof(KingsArmor)&&Texture("SaberRelicsV2") is {} objects){float w=objects.GetWidth()/2f;return Textures[cache]=new AtlasTexture{Atlas=objects,Region=new Rect2(key==nameof(WindBarrier)?0:w,0,w,objects.GetHeight())};}
        string mark=key switch{
            nameof(CommandSeals)=>"<path d='M48 18L62 40 48 54 34 40Z M27 46L42 62 37 82 18 66Z M69 46L54 62 59 82 78 66Z' fill='#db4448'/>",
            nameof(WindBarrier)=>"<path d='M17 37Q50 15 76 30Q90 44 61 48 M20 51Q57 31 78 50 M23 68Q53 47 70 67' fill='none' stroke='#cdeffc' stroke-width='5'/>",
            nameof(KingsArmor)=>"<path d='M25 23L38 18 48 28 58 18 71 23 78 46 62 52 61 79H35L34 52 18 46Z' fill='#bcc9dd' stroke='#dabe74' stroke-width='3'/>",
            nameof(OldHeater)=>"<rect x='25' y='21' width='46' height='60' rx='5' fill='#8d6250'/><path d='M32 36H64 M32 47H64 M32 58H64 M32 69H64' stroke='#ffd199' stroke-width='5'/>",
            nameof(EmiyaHouse)=>"<path d='M15 44L48 18 81 44 M24 40V79H72V40' fill='#ad9a84' stroke='#ece1cb' stroke-width='3'/><rect x='42' y='55' width='13' height='24' fill='#503b35'/>",
            nameof(Avalon)=>"<path d='M42 15H55L65 66 49 84 32 66Z' fill='#426ca9' stroke='#eac576' stroke-width='4'/><path d='M48 24V65 M42 42H55 M40 58H59' stroke='#f5df9a' stroke-width='3'/>",
            nameof(ReinforcePower)=>"<path d='M18 71L35 54 41 26 62 17 77 32 66 52 41 59 25 78Z' fill='none' stroke='#81e7c2' stroke-width='5'/><path d='M38 58L65 31' stroke='#f5e4be' stroke-width='4'/>",
            nameof(AnalysisPower)=>"<circle cx='43' cy='42' r='23' fill='none' stroke='#93deb5' stroke-width='4'/><path d='M60 60L79 79 M29 43H57 M43 29V57' stroke='#93deb5' stroke-width='5'/>",
            nameof(TemporaryArtifact)=>"<path d='M48 17L74 32V57L48 80 22 57V32Z' fill='#73b4d5' stroke='#daeff4' stroke-width='3'/><path d='M38 41L47 58 61 32' fill='none' stroke='#fff1ae' stroke-width='4'/>",
            nameof(PrecautionBuffer)=>"<path d='M48 18L74 28V50Q74 69 48 81Q22 69 22 50V28Z' fill='#6c99c5' stroke='#e5cf8f' stroke-width='4'/>",
            _=>"<path d='M48 78Q10 54 23 33Q36 14 48 34Q60 14 73 33Q86 54 48 78Z' fill='#ed868c'/><path d='M26 49H39L46 36 53 64 61 49H74' fill='none' stroke='#fce3b4' stroke-width='3'/>"
        };
        string svg="<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96'><path d='M48 3L87 25V71L48 93 9 71V25Z' fill='#182738' stroke='#bd985a' stroke-width='3'/>"+mark+"</svg>";
        var im=new Image();im.LoadSvgFromString(svg);return Textures[cache]=ImageTexture.CreateFromImage(im);
    }
    public static void Portrait(Node root,string key,Vector2 position,float height){
        if(TestMode.IsOn||Texture(key) is not {} texture)return;
        var sprite=new Sprite2D{Name="FSNPortrait",Texture=texture,Position=position,Scale=Vector2.One*(height/texture.GetHeight())};root.AddChild(sprite);
    }
    public static void AttachUi(Player player){
        if(TestMode.IsOn||NCombatRoom.Instance==null)return;
        var root=new Control{Name="FSNContract",Position=new Vector2(24,175),Size=new Vector2(310,100),MouseFilter=Control.MouseFilterEnum.Ignore};
        var panel=new Panel{Name="FSNContractPanel",Size=new(300,92),MouseFilter=Control.MouseFilterEnum.Ignore};
        panel.AddThemeStyleboxOverride("panel",new StyleBoxFlat{BgColor=new Color("0a1722e8"),BorderColor=new("668c96"),BorderWidthLeft=3,BorderWidthTop=1,BorderWidthBottom=1,ContentMarginLeft=14,CornerRadiusTopRight=12,CornerRadiusBottomRight=12});root.AddChild(panel);
        Status=new Label{Name="FSNFighter",Position=new(15,9),Size=new Vector2(280,76)};
        Status.AddThemeFontSizeOverride("font_size",18);root.AddChild(Status);
        Choices=new VBoxContainer{Position=new Vector2(0,100),Visible=false};Choices.AddThemeConstantOverride("separation",6);root.AddChild(Choices);
        string[] names=["玛娜补给","来我身边","解除契约"];
        for(int i=0;i<3;i++){int option=i;var button=CreateButton(names[i],new(230,50));Choices.AddChild(button);
            button.Released+=_=>{Choices.Visible=false;if(Duo.For(player) is {} d&&player.PlayerCombatState?.Phase==PlayerTurnPhase.Play)RunManager.Instance.ActionQueueSynchronizer.RequestEnqueue(new SealAction(d,option));};}
        var monitor=new Godot.Timer{WaitTime=0.15,Autostart=true};root.AddChild(monitor);monitor.Timeout+=()=>{if(Duo.For(player) is {} d)RefreshSealUi(d);};
        NCombatRoom.Instance.Ui.AddChild(root);RefreshFighter(Duo.For(player)!);
    }
    static NButton CreateButton(string text,Vector2 size){var b=new NButton{Size=size,CustomMinimumSize=size,FocusMode=Control.FocusModeEnum.All};var visual=new Button{Text=text,MouseFilter=Control.MouseFilterEnum.Ignore,FocusMode=Control.FocusModeEnum.None};StyleButton(visual);b.AddChild(visual);visual.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);b.Focused+=_=>visual.Modulate=new Color("cce0ff");b.Unfocused+=_=>visual.Modulate=Colors.White;return b;}
    static void StyleButton(Button b){b.AddThemeFontSizeOverride("font_size",20);foreach(string state in new[]{"normal","hover","pressed","disabled"}){var box=new StyleBoxFlat{BgColor=new Color(state=="hover"?"35465a":state=="pressed"?"573942":"182938"),BorderColor=new("8397a9"),BorderWidthLeft=1,BorderWidthTop=1,BorderWidthRight=1,BorderWidthBottom=1,CornerRadiusTopLeft=2,CornerRadiusTopRight=2,CornerRadiusBottomLeft=2,CornerRadiusBottomRight=2};b.AddThemeStyleboxOverride(state,box);}}
    public static void RefreshFighter(Duo d){
        if(TestMode.IsOn)return;
        if(Find<MegaCrit.sts2.Core.Nodes.TopBar.NTopBarPortrait>()?.GetNodeOrNull<TextureRect>("FSNFighterIcon") is {} topIcon)topIcon.Texture=Texture(d.IsSaber?"SaberFace":"ShirouFace");
        RefreshSealUi(d);
        Skin.RefreshEnergy(d);
        if(Status!=null&&GodotObject.IsInstanceValid(Status)){
            Status.Text=$"{(d.IsSaber?"Saber · 剑之骑士":"卫宫士郎 · 魔术使")}\n{(d.ContractActive?(d.Other==d.Saber?"Saber":"士郎")+"  "+d.Other.Hp+" / "+d.Other.MaxHp:"契约已解除")}    令咒 {d.Seal.Charges}/3"+(d.Current.TemporaryHp>0?$"\n临时生命 {d.Current.TemporaryHp}":"");
            Status.Modulate=d.IsSaber?new Color("bcddff"):new Color("b7ead7");
        }
        // Keep the native creature, hitboxes and animation controller; replace its visible artwork.
        var node=d.Player.Creature.GetCreatureNode();if(node?.Visuals==null)return;
        var visuals=node.Visuals;
        var sprite=visuals.GetNodeOrNull<Sprite2D>("FSNPortrait");
        bool changed=sprite?.Texture!=Texture(d.IsSaber?"SaberBattle":"ShirouBattle");
        if(sprite==null){sprite=new Sprite2D{Name="FSNPortrait",Position=new Vector2(0,-173)};visuals.AddChild(sprite);var motion=new FighterMotion{Name="FSNMotion",Sprite=sprite};sprite.AddChild(motion);motion.Start();}
        sprite.Texture=Texture(d.IsSaber?"SaberBattle":"ShirouBattle")??Texture(d.IsSaber?"Saber":"Shirou");
        if(sprite.Texture!=null){sprite.Scale=Vector2.One*(385f/sprite.Texture.GetHeight());
            foreach(var child in visuals.GetChildren())if(child!=sprite&&child.Name!="FSNAura"&&child is CanvasItem canvas)canvas.Visible=false;}
        var aura=visuals.GetNodeOrNull<ContractAtmosphere>("FSNAura");if(aura==null){aura=new(){Name="FSNAura"};visuals.AddChild(aura);visuals.MoveChild(aura,0);aura.Start();}aura.Saber=d.IsSaber;
        if(changed){sprite.Modulate=new Color(1,1,1,.15f);sprite.CreateTween().TweenProperty(sprite,"modulate:a",1.0,.28);}
    }
    public static bool SealAvailable(Duo d)=>d.Combat!=null&&d.Player.PlayerCombatState?.Phase==PlayerTurnPhase.Play&&!d.Switching&&!d.Seal.UsedThisCombat&&d.Seal.Charges>0;
    public static void RefreshSealUi(Duo d){
        if(TestMode.IsOn)return;
        if(Choices!=null&&GodotObject.IsInstanceValid(Choices)&&!SealAvailable(d))Choices.Visible=false;
        var inventory=Find<NRelicInventory>();if(inventory==null)return;
        foreach(var holder in inventory.FindChildren("*","",true,false).OfType<NRelicInventoryHolder>().Where(h=>h.Relic.Model==d.Seal)){
            holder.Relic.Icon.Modulate=SealAvailable(d)?Colors.White:new Color("777b83");
            AccessTools.Method(holder.GetType(),"RefreshAmount").Invoke(holder,[]);
            holder.TooltipText="";
        }
    }
    public static void ToggleSealChoices(Duo d){
        if(!SealAvailable(d)||Choices==null||!GodotObject.IsInstanceValid(Choices))return;
        var holder=Find<NRelicInventory>()?.FindChildren("*","",true,false).OfType<NRelicInventoryHolder>().FirstOrDefault(h=>h.Relic.Model==d.Seal);
        if(holder!=null)Choices.GlobalPosition=holder.GlobalPosition+new Vector2(0,60);
        Choices.Visible=!Choices.Visible;
        if(Choices.Visible&&holder!=null)MegaCrit.Sts2.Core.Nodes.HoverTips.NHoverTipSet.Remove(holder);
    }
}
