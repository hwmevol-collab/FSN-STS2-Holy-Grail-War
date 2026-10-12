namespace RinArcherCore;
public sealed class RinAlphaRewardPool:CustomCardPoolModel
{public override string Title=>AlphaRewardRegistry.RinPoolId;public override string EnergyColorName=>"ironclad";public override Color DeckEntryCardColor=>new("92374d");public override bool IsColorless=>false;}
public sealed class ArcherAlphaRewardPool:CustomCardPoolModel
{public override string Title=>AlphaRewardRegistry.ArcherPoolId;public override string EnergyColorName=>"ironclad";public override Color DeckEntryCardColor=>new("527087");public override bool IsColorless=>false;}
