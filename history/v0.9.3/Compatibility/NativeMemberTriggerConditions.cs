// Generated from approved native command data-flow; original hooks still execute every effect/counter.
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Entities.Players;
namespace RinArcherCore;
public static class NativeMemberTriggerConditions
{
    public static bool Eligible(AbstractModel model,string trigger,Player ownerPlayer,Creature memberTarget,object[] hookArgs)
        =>memberTarget.IsAlive&&((model.GetType().FullName,trigger) switch
        {
        ("MegaCrit.Sts2.Core.Models.Relics.BigMushroom","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.BlackBlood","AfterCombatVictory") => ((!memberTarget.IsDead)),
        ("MegaCrit.Sts2.Core.Models.Relics.BloodVial","AfterPlayerTurnStartLate") => ((((Player)hookArgs[1]!) == ownerPlayer && ownerPlayer.PlayerCombatState!.TurnNumber <= 1)),
        ("MegaCrit.Sts2.Core.Models.Relics.BookOfFiveRings","AfterCardChangedPiles") => (!(memberTarget.IsDead || ((CardModel)hookArgs[0]!).Owner != ownerPlayer) && ((((CardModel)hookArgs[0]!).Pile) != null && (((CardModel)hookArgs[0]!).Pile)!.Type == PileType.Deck) && (((((MegaCrit.Sts2.Core.Models.Relics.BookOfFiveRings)model).CardsAdded + 1) % ((RelicModel)model).DynamicVars.Cards.IntValue) == 0)),
        ("MegaCrit.Sts2.Core.Models.Relics.BookRepairKnife","AfterDiedToDoom") => (!((((IReadOnlyList<Creature>)hookArgs[1]!).Count((Creature c) => c != memberTarget && c.Powers.All((PowerModel p) => p.ShouldOwnerDeathTriggerFatal()))) == 0)),
        ("MegaCrit.Sts2.Core.Models.Relics.BurningBlood","AfterCombatVictory") => ((!memberTarget.IsDead)),
        ("MegaCrit.Sts2.Core.Models.Relics.ChosenCheese","AfterCombatEnd") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.DarkstonePeriapt","AfterCardChangedPiles") => (((((CardModel)hookArgs[0]!).Pile) != null && (((CardModel)hookArgs[0]!).Pile)!.Type == PileType.Deck && ((CardModel)hookArgs[0]!).Owner == ownerPlayer && ((CardModel)hookArgs[0]!)!.Type == CardType.Curse)),
        ("MegaCrit.Sts2.Core.Models.Relics.DragonFruit","AfterGoldGained") => ((((Player)hookArgs[0]!) == ownerPlayer)),
        ("MegaCrit.Sts2.Core.Models.Relics.FakeBloodVial","AfterPlayerTurnStartLate") => ((((Player)hookArgs[1]!) == ownerPlayer && ownerPlayer.PlayerCombatState!.TurnNumber <= 1)),
        ("MegaCrit.Sts2.Core.Models.Relics.FakeLeesWaffle","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.FakeMango","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.LeesWaffle","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.LoomingFruit","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.Mango","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.MealTicket","AfterRoomEntered") => ((!memberTarget.IsDead && ((AbstractRoom)hookArgs[0]!) is MerchantRoom)),
        ("MegaCrit.Sts2.Core.Models.Relics.MeatOnTheBone","AfterCombatVictoryEarly") => ((!memberTarget.IsDead) && (NativeMemberConditionContext.PrivateBool(model,ownerPlayer,memberTarget,"AfterCombatVictoryEarly","WillHealOnCombatFinished"))),
        ("MegaCrit.Sts2.Core.Models.Relics.NutritiousOyster","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.Pantograph","BeforeCombatStart") => ((!memberTarget.IsDead && ownerPlayer.RunState.CurrentRoom!.RoomType == RoomType.Boss)),
        ("MegaCrit.Sts2.Core.Models.Relics.Pear","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Relics.Planisphere","AfterRoomEntered") => ((!memberTarget.IsDead) && ((ownerPlayer.RunState.CurrentMapPoint) != null && (ownerPlayer.RunState.CurrentMapPoint).PointType == MapPointType.Unknown)),
        ("MegaCrit.Sts2.Core.Models.Relics.Strawberry","AfterObtained") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.BlockPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.DexterityPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.BloodPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.FlexPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.Fortifier","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.FruitJuice","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.GhostInAJar","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.LiquidBronze","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.LuckyTonic","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.MazalethsGift","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.RegenPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.SpeedPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.StrengthPotion","OnUse") => (true),
        ("MegaCrit.Sts2.Core.Models.Potions.SwiftPotion","OnUse") => (true),
        _ => false
    });
}
