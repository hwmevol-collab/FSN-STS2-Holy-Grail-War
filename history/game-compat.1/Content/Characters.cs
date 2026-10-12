using MegaCrit.Sts2.Core.Entities.Characters;
using MegaCrit.Sts2.Core.Models.PotionPools;
using MegaCrit.Sts2.Core.Models.RelicPools;
using MegaCrit.Sts2.Core.Nodes.Combat;
namespace RinArcherCore;
public sealed class RinContractCharacter : PlaceholderCharacterModel
{
    public override Control? CustomIcon => new TextureRect { Name="ContractIcon", Texture=new AtlasTexture { Atlas=PresentationTheme.Asset("rin-face.png"), Region=new Rect2(20,0,425,425) }, ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize, StretchMode=TextureRect.StretchModeEnum.KeepAspectCovered, Size=new(80,80), MouseFilter=Control.MouseFilterEnum.Ignore };
    public override int StartingHp=>58;
    public override Color NameColor=>new("92374d");
    public override CharacterGender Gender=>CharacterGender.Feminine;
    public override CardPoolModel CardPool=>ModelDb.CardPool<RinArcherPool>();
    public override PotionPoolModel PotionPool=>ModelDb.PotionPool<RinContractPotionPool>();
    public override RelicPoolModel RelicPool=>ModelDb.RelicPool<RinContractRelicPool>();
    public override IEnumerable<CardModel> StartingDeck=>StarterDefinitions.Rin;
    public override IReadOnlyList<RelicModel> StartingRelics=>[];
    public override List<(string,string)> Localization=>[("title",FsnLoc.Text("UI_043F19C4E63F")),("titleObject",FsnLoc.Text("UI_D5116EA0D04E")),("description",FsnLoc.Text("UI_A27AC6B77286")),("pronounObject",FsnLoc.Text("UI_2AB425E0C6B9")),("pronounSubject",FsnLoc.Chinese?"她":"she"),("possessiveAdjective",FsnLoc.Text("UI_96864FC749AC")),("pronounPossessive",FsnLoc.Text("UI_96864FC749AC")),("characterSelectTitle",FsnLoc.Text("UI_F4F21659D6B4"))];
    public override NCreatureVisuals? CreateCustomVisuals()=>ContractPresentationBody.Create(true);
}
// Vanilla shared pools are added by the native factories. RinContract has no
// approved vanilla character-exclusive pool; placeholder artwork is not eligibility.
public sealed class RinContractPotionPool:CustomPotionPoolModel;
public sealed class RinContractRelicPool:CustomRelicPoolModel;
public sealed class RinArcherPool:CustomCardPoolModel
{
    public override string Title=>FsnLoc.Text("UI_857431D54625");
    public override string EnergyColorName=>"ironclad";
    public override Color DeckEntryCardColor=>new("92374d");
    public override bool IsColorless=>false;
}
public static class PlaceholderVisuals
{
    static Texture2D? rinCard,archerCard;
    public static Texture2D CardTexture(bool rin)
    {
        if((rin?rinCard:archerCard) is {} existing)return existing;
        var img=Image.CreateEmpty(256,192,false,Image.Format.Rgba8);img.Fill(new Color(rin?"92374d":"527087"));
        var tex=ImageTexture.CreateFromImage(img);if(rin)rinCard=tex;else archerCard=tex;return tex;
    }
    public static NCreatureVisuals Creature(string label,Color color)
    {
        var root=new NCreatureVisuals{Name="PlaceholderVisuals"};
        void Add(Node node){root.AddChild(node);node.Owner=root;node.UniqueNameInOwner=true;}
        var visuals=new Node2D{Name="Visuals"};Add(visuals);
        visuals.AddChild(new Polygon2D{Color=color,Polygon=[new(-65,-145),new(65,-145),new(65,0),new(-65,0)]});
        visuals.AddChild(new Label{Text=label,Position=new(-85,-180),MouseFilter=Control.MouseFilterEnum.Ignore});
        Add(new Control{Name="Bounds",Position=new(-65,-145),Size=new(130,145),MouseFilter=Control.MouseFilterEnum.Ignore});
        Add(new Marker2D{Name="IntentPos",Position=new(0,-220)});Add(new Marker2D{Name="CenterPos",Position=new(0,-75)});
        return root;
    }
}
