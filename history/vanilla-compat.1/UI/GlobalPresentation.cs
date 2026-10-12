using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.addons.mega_text;
namespace RinArcherCore;

// One native lobby choice, one jointly authored Master/Servant main visual.
public sealed partial class ContractSelectArtwork:Node2D
{
    public bool Archer=>false; // legacy QA API only; there is no separate hero selector.
    public void Select(bool _){ }
    float age;readonly Texture2D rin=PresentationTheme.Asset("select-rin.png"),archer=PresentationTheme.Asset("select-archer.png"),landscape=PresentationTheme.Asset("contract-landscape.png");
    public ContractSelectArtwork(){Name="ContractSelectArtwork";Draw+=Paint;TreeEntered+=()=>GetTree().ProcessFrame+=Tick;TreeExiting+=()=>GetTree().ProcessFrame-=Tick;}
    void Tick(){if(!IsVisibleInTree())return;age+=(float)GetProcessDeltaTime();QueueRedraw();}
    void Paint()
    {
        DrawTextureRect(landscape,new Rect2(0,0,1920,1080),false,new Color(.55f,.49f,.48f));
        // Continuous vignette, no rectangle enclosing the information column.
        DrawTextureRect(PresentationTheme.Svg("contract-vignette","<defs><linearGradient id='l'><stop stop-color='#100e19' stop-opacity='.94'/><stop offset='.31' stop-color='#19121b' stop-opacity='.76'/><stop offset='.65' stop-color='#17121c' stop-opacity='.08'/><stop offset='1' stop-color='#16101c' stop-opacity='.12'/></linearGradient><linearGradient id='b' x1='0' x2='0' y1='0' y2='1'><stop offset='.67' stop-color='#100e15' stop-opacity='0'/><stop offset='1' stop-color='#100e15' stop-opacity='.9'/></linearGradient></defs><rect width='1920' height='1080' fill='url(#l)'/><rect width='1920' height='1080' fill='url(#b)'/>",1920,1080),new Rect2(0,0,1920,1080),false);
        float drift=MathF.Sin(age*.36f)*3;
        // Official REMASTERED transparent character layers, each displayed below source resolution.
        // Archer stands behind his Master; shared warm foreground light connects both figures.
        DrawTextureRect(archer,new Rect2(1250+drift*.65f,25,666,821),false,new Color(.91f,.87f,.87f));
        DrawTextureRect(rin,new Rect2(876+drift,164,755,904),false,new Color(.98f,.92f,.91f));
        // The original authored lower edge dissolves into the native portrait rail instead of ending as a sticker.
        DrawTextureRect(PresentationTheme.Svg("contract-foreground-fade","<defs><linearGradient id='f' x1='0' x2='0' y1='0' y2='1'><stop offset='.70' stop-color='#111019' stop-opacity='0'/><stop offset='.82' stop-color='#111019' stop-opacity='.32'/><stop offset='.87' stop-color='#111019' stop-opacity='.94'/><stop offset='1' stop-color='#111019' stop-opacity='1'/></linearGradient></defs><rect width='1920' height='1080' fill='url(#f)'/>",1920,1080),new Rect2(0,0,1920,1080),false);
        // One silhouette and one shared scene: existing authored hand/weapon relationship is intact.
        for(int i=0;i<20;i++){float x=760+(i*137)%1110,y=920-((age*(12+i%4*4)+i*53)%910);DrawCircle(new(x,y),i%4==0?1.7f:1,new Color(.97f,.65f,.41f,.20f));}
        DrawLine(new(283,694),new(709,694),new Color(.72f,.57f,.42f,.35f),1);
    }
}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class ContractSelectPage
{
    static void Postfix(NCharacterSelectScreen __instance,CharacterModel characterModel)
    {
        var s=__instance;bool contract=characterModel is RinContractCharacter;
        var bg=(Control)AccessTools.Field(typeof(NCharacterSelectScreen),"_bgContainer").GetValue(s)!;
        foreach(var n in s.GetChildren().Where(n=>n.Name.ToString().StartsWith("ContractSpotlight")).ToArray())n.QueueFree();
        bg.Visible=!contract;
        var info=s.GetNode<Control>("InfoPanel");info.SelfModulate=contract?new Color(1,1,1,0):Colors.White;
        foreach(var n in Descendants(info).OfType<CanvasItem>().Where(n=>(n is TextureRect or NinePatchRect or ColorRect or Panel or Sprite2D)&&!n.GetPath().ToString().Contains("HpGold")&&!n.GetPath().ToString().Contains("Relic")))n.Visible=!contract;
        if(info is TextureRect it){if(!info.HasMeta("ContractNativePanelTexture"))info.SetMeta("ContractNativePanelTexture",it.Texture);it.Texture=contract?null:info.GetMeta("ContractNativePanelTexture").As<Texture2D>();}
        if(info is Panel or PanelContainer){if(contract)info.AddThemeStyleboxOverride("panel",new StyleBoxEmpty());else info.RemoveThemeStyleboxOverride("panel");}
        if(!contract)return;
        var art=new ContractSelectArtwork{Name="ContractSpotlightArtwork"};s.AddChild(art);s.MoveChild(art,0);
        s.GetNode<MegaLabel>("InfoPanel/VBoxContainer/Name").SetTextAutoSize(FsnLoc.Text("UI_42A68890419C"));
        s.GetNode<MegaRichTextLabel>("InfoPanel/VBoxContainer/DescriptionLabel").Text=FsnLoc.Text("UI_1E0F438901AF");
        var logo=new TextureRect{Name="ContractSpotlightLogo",ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,Texture=PresentationTheme.Asset("fsn-logo.png"),Position=new(277,101),Size=new(270,270),StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered,MouseFilter=Control.MouseFilterEnum.Ignore};s.AddChild(logo);
        var roles=PresentationTheme.Label("MASTER  /  SERVANT",17,PresentationTheme.Muted);roles.Name="ContractSpotlightRoles";roles.Position=new(283,668);s.AddChild(roles);
    }
    static IEnumerable<Node> Descendants(Node n){foreach(var c in n.GetChildren()){yield return c;foreach(var d in Descendants(c))yield return d;}}
}
public sealed partial class ContractCampArtwork:Node2D
{
    readonly Texture2D people=PresentationTheme.Asset("camp-duo.png");float age;
    public ContractCampArtwork(){Name="ContractCampArtwork";Draw+=Paint;TreeEntered+=()=>GetTree().ProcessFrame+=Tick;TreeExiting+=()=>GetTree().ProcessFrame-=Tick;}
    void Tick(){if(!IsVisibleInTree())return;age+=(float)GetProcessDeltaTime();QueueRedraw();}
    void Paint()
    {
        foreach(float x in new[]{655f,1270f})for(int i=0;i<8;i++){DrawSetTransform(new(x,815),0,new Vector2(1,.23f));DrawCircle(Vector2.Zero,84-i*5,new Color(0,0,0,.035f));}DrawSetTransform(Vector2.Zero);
        var size=people.GetSize();float breath=MathF.Sin(age*1.2f)*.8f,light=.84f+MathF.Sin(age*3.7f)*.018f;
        var shade=new Color(light,light*.94f,light*.84f);
        DrawTextureRectRegion(people,new Rect2(505,416+breath,310,414),new Rect2(0,0,size.X/2,size.Y),shade);
        DrawTextureRectRegion(people,new Rect2(1115,416-breath,310,414),new Rect2(size.X/2,0,size.X/2,size.Y),shade);
    }
}
[HarmonyPatch(typeof(NRestSiteRoom),"_Ready")]
public static class ContractCampPage
{
    static void Postfix(NRestSiteRoom __instance)
    {
        var p=MegaCrit.Sts2.Core.Runs.RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault();if(p?.Character is not RinContractCharacter)return;
        foreach(var c in __instance.Characters)c.Visible=false;
        __instance.GetNode<Control>("BgContainer").AddChild(new ContractCampArtwork());
    }
}
// The public Beta never adds historical milestone-launch buttons, including before a Run.
[HarmonyPatch(typeof(CoreHud),nameof(CoreHud.AttachLauncher))]
public static class BetaHideLegacyLauncher
{static bool Prefix(){if(!OS.GetUserDataDir().Replace('\\','/').Contains("RinArcherWorkshopBeta-20261011/"))return true;CoreHud.ClearLauncher();return false;}}

[HarmonyPatch(typeof(NCharacterSelectButton),nameof(NCharacterSelectButton.Init))]
public static class ContractSelectIcon
{
    static void Postfix(NCharacterSelectButton __instance,CharacterModel character)
    {
        if(character is not RinContractCharacter)return;
        var portrait=new AtlasTexture{Atlas=PresentationTheme.Asset("rin-face.png"),Region=new Rect2(20,0,425,425)};
        __instance.GetNode<TextureRect>("%Icon").Texture=portrait;__instance.GetNode<TextureRect>("%IconAdd").Texture=portrait;
    }
}

[HarmonyPatch(typeof(CharacterModel),"get_Icon")]
public static class ContractNativePortrait
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(CharacterModel __instance,ref Control __result)
    {
        if(__instance is not RinContractCharacter)return;
        if(__result.GetNodeOrNull<TextureRect>("IroncladIcon") is {} icon){icon.Texture=new AtlasTexture{Atlas=PresentationTheme.Asset("rin-face.png"),Region=new Rect2(20,0,425,425)};icon.StretchMode=TextureRect.StretchModeEnum.KeepAspectCovered;}
    }
}
[HarmonyPatch(typeof(CharacterModel),"get_IconTexture")]
public static class ContractNativePortraitTexture
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(CharacterModel __instance,ref Texture2D __result)
    {if(__instance is RinContractCharacter)__result=new AtlasTexture{Atlas=PresentationTheme.Asset("rin-face.png"),Region=new Rect2(20,0,425,425)};}
}
