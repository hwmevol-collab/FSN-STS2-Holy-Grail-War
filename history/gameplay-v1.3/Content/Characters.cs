using MegaCrit.Sts2.Core.Entities.Characters;
using MegaCrit.Sts2.Core.Models.PotionPools;
using MegaCrit.Sts2.Core.Models.RelicPools;
using MegaCrit.Sts2.Core.Nodes.Combat;
namespace RinArcherCore;
public sealed class RinContractCharacter : PlaceholderCharacterModel
{
    public override int StartingHp=>58;
    public override Color NameColor=>new("92374d");
    public override CharacterGender Gender=>CharacterGender.Feminine;
    public override CardPoolModel CardPool=>ModelDb.CardPool<RinArcherPool>();
    public override PotionPoolModel PotionPool=>ModelDb.PotionPool<RinContractPotionPool>();
    public override RelicPoolModel RelicPool=>ModelDb.RelicPool<RinContractRelicPool>();
    public override IEnumerable<CardModel> StartingDeck=>StarterDefinitions.Rin;
    public override IReadOnlyList<RelicModel> StartingRelics=>[];
    public override List<(string,string)> Localization=>[("title","凛（御主占位）"),("titleObject","凛"),("description","凛 / 弓兵 · Public Vertical Slice。共用资源，独立生命与手牌；在战斗中切换前场角色。当前开放短路线：战斗、宝箱、休息与商店。"),("pronounObject","她"),("pronounSubject","她"),("possessiveAdjective","她的"),("pronounPossessive","她的"),("characterSelectTitle","凛 / 弓兵")];
    public override NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("凛（御主占位）",new Color("92374d"));
}
// Vanilla shared pools are added by the native factories. RinContract has no
// approved vanilla character-exclusive pool; placeholder artwork is not eligibility.
public sealed class RinContractPotionPool:CustomPotionPoolModel;
public sealed class RinContractRelicPool:CustomRelicPoolModel;
public sealed class RinArcherPool:CustomCardPoolModel
{
    public override string Title=>"凛 / 弓兵初始牌组";
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
