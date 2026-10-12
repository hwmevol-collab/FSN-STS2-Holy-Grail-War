using STS2RitsuLib.CardPiles;
namespace RinArcherCore;
public static class CardBanks
{
    public static readonly Dictionary<PileType,ModCardPileDefinition> Reserve=[];
    public static ModCardPileDefinition ArcherDeck=null!;
    public static void Register()
    {
        var reg=ModCardPileRegistry.For("RinArcherCore");
        ArcherDeck=reg.RegisterOwned("archer_deck",new(){Scope=ModCardPileScope.RunPersistent});
        foreach(var type in new[]{PileType.Hand,PileType.Draw,PileType.Discard,PileType.Exhaust,PileType.Play})
            Reserve[type]=reg.RegisterOwned("reserve_"+type.ToString().ToLowerInvariant(),new(){
                Style=type==PileType.Hand?ModCardPileUiStyle.ExtraHand:ModCardPileUiStyle.Headless,
                CardShouldBeVisible=type==PileType.Hand,
                Anchor=new(ModCardPileAnchorKind.ExtraHandAbove,new Vector2(90,-710)),
                ExtraHand=new(){AllowCardPlay=false,Behaviors=ModExtraHandBehavior.None,Direction=ModExtraHandLayoutDirection.Horizontal,
                    Spacing=110,CardScale=Vector2.One*0.42f,HoverScale=Vector2.One*0.7f},
                VisibleWhen=ctx=>ContractRuntime.For(ctx.Player)!=null
            });
    }
    public static CardPile Bank(PileType type,Player p)=>CardPile.Get(Reserve[type].PileType,p)??throw new InvalidOperationException("Ritsu bank unavailable");
}
public sealed class CharacterRuntime(ContractRuntime contract,string id,string role,Creature creature)
{
    public string CharacterId{get;}=id;
    public string Role{get;}=role;
    public Creature Creature{get;}=creature;
    public readonly Dictionary<string,int> CharacterResources=[];
    public readonly Dictionary<string,bool> TemporaryFlags=[];
    public bool IsActive=>contract.Active==this;
    public string ActiveState=>IsActive?"ACTIVE":"RESERVE";
    public CardPile Deck=>CharacterId=="CHAR_RIN"?contract.Player.Deck:CardPile.Get(CardBanks.ArcherDeck.PileType,contract.Player)!;
    public CardPile Pile(PileType type)=>IsActive?CardPile.Get(type,contract.Player)!:CardBanks.Bank(type,contract.Player);
    public CardPile Hand=>Pile(PileType.Hand);
    public CardPile DrawPile=>Pile(PileType.Draw);
    public CardPile Discard=>Pile(PileType.Discard);
    public CardPile Exhaust=>Pile(PileType.Exhaust);
    public IReadOnlyList<PowerModel> Statuses=>Creature.Powers;
}
