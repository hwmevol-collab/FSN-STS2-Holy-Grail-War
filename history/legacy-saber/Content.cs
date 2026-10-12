using MegaCrit.Sts2.Core.Entities.Characters;
using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.Models.PotionPools;
using MegaCrit.Sts2.Core.Models.RelicPools;
namespace FateStayNight;

public sealed class EmiyaShirou : PlaceholderCharacterModel
{
    public override int StartingHp => 30;
    public override CharacterGender Gender => CharacterGender.Masculine;
    public override Color NameColor => new("BC343A");
    public override CardPoolModel CardPool => ModelDb.CardPool<EmiyaPool>();
    public override PotionPoolModel PotionPool => ModelDb.PotionPool<IroncladPotionPool>();
    public override RelicPoolModel RelicPool => ModelDb.RelicPool<FateRelicPool>();
    public override IEnumerable<CardModel> StartingDeck => new CardModel[] {
        ModelDb.Card<PosterStrike>(),ModelDb.Card<PosterStrike>(),ModelDb.Card<PosterStrike>(),
        ModelDb.Card<QuickDodge>(),ModelDb.Card<QuickDodge>(),ModelDb.Card<QuickDodge>(),ModelDb.Card<QuickDodge>(),ModelDb.Card<QuickDodge>(),
        ModelDb.Card<Reinforcement>(),ModelDb.Card<Coordination>() };
    public override IReadOnlyList<RelicModel> StartingRelics => [ModelDb.Relic<CommandSeals>()];
    public override List<(string,string)> Localization => [ ("title","卫宫士郎"),("titleObject","卫宫士郎"),("description","Master与Servent共同作战，分别使用不同的卡组，使用同一个能量槽。"),
        ("pronounObject","他"),("pronounSubject","他"),("possessiveAdjective","他的"),("pronounPossessive","他的"),("characterSelectTitle","卫宫士郎与Saber") ];
}
public sealed class EmiyaPool : CustomCardPoolModel
{
    public override string Title => "Fate/stay night";
    public override string EnergyColorName => "ironclad";
    public override Color DeckEntryCardColor => new("BC343A");
    public override Color ShaderColor => new("BC343A");
    public override bool IsColorless => false;
    // Borrowing happens in GetUnlockedCards, never in AllCards: native pool identities remain intact.
    protected override CardModel[] GenerateAllCards() => [];
}
public sealed class SaberPool : CustomCardPoolModel
{
    public override string Title => "Saber";
    public override string EnergyColorName => "ironclad";
    public override Color DeckEntryCardColor => new("315AA0");
    public override Color ShaderColor => new("315AA0");
    public override bool IsColorless => false;
}
public sealed class FateRelicPool : CustomRelicPoolModel
{
    public override string EnergyColorName => "ironclad";
}
public sealed class FateEventPool : CustomCardPoolModel
{
    public override string Title => "Fate衍生";
    public override string EnergyColorName => "ironclad";
    public override Color DeckEntryCardColor => new("BC343A");
    public override bool IsColorless => true;
}
