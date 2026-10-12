namespace RinArcherCore;
public sealed record AlphaDefinition(string Id,string Owner,CardRarity Rarity,CardType Type,int Energy,int Mana,string Name,string Rules,string Upgrade);
public static class AlphaRewardRegistry
{
    public const string RinPoolId="RIN_ALPHA_REWARD_POOL",ArcherPoolId="ARCHER_ALPHA_REWARD_POOL";
    public static readonly IReadOnlyList<AlphaDefinition> Definitions=Array.AsReadOnly(new[]{
        new AlphaDefinition("RIN-C04","CHAR_RIN",CardRarity.Common,CardType.Attack,GameplayCatalog.Cards["RIN-C04"].Energy,GameplayCatalog.Cards["RIN-C04"].Mana,"强化格斗",GameplayCatalog.Cards["RIN-C04"].Normal,GameplayCatalog.Cards["RIN-C04"].Upgraded),
        new AlphaDefinition("RIN-C05","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C05"].Energy,GameplayCatalog.Cards["RIN-C05"].Mana,"储魔宝石",GameplayCatalog.Cards["RIN-C05"].Normal,GameplayCatalog.Cards["RIN-C05"].Upgraded),
        new AlphaDefinition("RIN-C08","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C08"].Energy,GameplayCatalog.Cards["RIN-C08"].Mana,"强化支援",GameplayCatalog.Cards["RIN-C08"].Normal,GameplayCatalog.Cards["RIN-C08"].Upgraded),
        new AlphaDefinition("RIN-C10","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C10"].Energy,GameplayCatalog.Cards["RIN-C10"].Mana,"甘德连射",GameplayCatalog.Cards["RIN-C10"].Normal,GameplayCatalog.Cards["RIN-C10"].Upgraded),
        new AlphaDefinition("RIN-C12","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C12"].Energy,GameplayCatalog.Cards["RIN-C12"].Mana,"魔力转换",GameplayCatalog.Cards["RIN-C12"].Normal,GameplayCatalog.Cards["RIN-C12"].Upgraded),
        new AlphaDefinition("RIN-C13","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C13"].Energy,GameplayCatalog.Cards["RIN-C13"].Mana,"宝石调律",GameplayCatalog.Cards["RIN-C13"].Normal,GameplayCatalog.Cards["RIN-C13"].Upgraded),
        new AlphaDefinition("RIN-C15","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C15"].Energy,GameplayCatalog.Cards["RIN-C15"].Mana,"魔术整序",GameplayCatalog.Cards["RIN-C15"].Normal,GameplayCatalog.Cards["RIN-C15"].Upgraded),
        new AlphaDefinition("RIN-C16","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C16"].Energy,GameplayCatalog.Cards["RIN-C16"].Mana,"礼装防护",GameplayCatalog.Cards["RIN-C16"].Normal,GameplayCatalog.Cards["RIN-C16"].Upgraded),
        new AlphaDefinition("RIN-U01","CHAR_RIN",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["RIN-U01"].Energy,GameplayCatalog.Cards["RIN-U01"].Mana,"宝石爆发",GameplayCatalog.Cards["RIN-U01"].Normal,GameplayCatalog.Cards["RIN-U01"].Upgraded),
        new AlphaDefinition("RIN-U04","CHAR_RIN",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["RIN-U04"].Energy,GameplayCatalog.Cards["RIN-U04"].Mana,"强化连击",GameplayCatalog.Cards["RIN-U04"].Normal,GameplayCatalog.Cards["RIN-U04"].Upgraded),
        new AlphaDefinition("RIN-U06","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U06"].Energy,GameplayCatalog.Cards["RIN-U06"].Mana,"术式解析",GameplayCatalog.Cards["RIN-U06"].Normal,GameplayCatalog.Cards["RIN-U06"].Upgraded),
        new AlphaDefinition("RIN-U10","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U10"].Energy,GameplayCatalog.Cards["RIN-U10"].Mana,"投影强化术式",GameplayCatalog.Cards["RIN-U10"].Normal,GameplayCatalog.Cards["RIN-U10"].Upgraded),
        new AlphaDefinition("RIN-U12","CHAR_RIN",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["RIN-U12"].Energy,GameplayCatalog.Cards["RIN-U12"].Mana,"强化供魔",GameplayCatalog.Cards["RIN-U12"].Normal,GameplayCatalog.Cards["RIN-U12"].Upgraded),
        new AlphaDefinition("RIN-U14","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U14"].Energy,GameplayCatalog.Cards["RIN-U14"].Mana,"宝石转换",GameplayCatalog.Cards["RIN-U14"].Normal,GameplayCatalog.Cards["RIN-U14"].Upgraded),
        new AlphaDefinition("RIN-U15","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U15"].Energy,GameplayCatalog.Cards["RIN-U15"].Mana,"术式接续",GameplayCatalog.Cards["RIN-U15"].Normal,GameplayCatalog.Cards["RIN-U15"].Upgraded),
        new AlphaDefinition("RIN-U16","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U16"].Energy,GameplayCatalog.Cards["RIN-U16"].Mana,"双重结界",GameplayCatalog.Cards["RIN-U16"].Normal,GameplayCatalog.Cards["RIN-U16"].Upgraded),
        new AlphaDefinition("RIN-R04","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R04"].Energy,GameplayCatalog.Cards["RIN-R04"].Mana,"宝石魔术精炼",GameplayCatalog.Cards["RIN-R04"].Normal,GameplayCatalog.Cards["RIN-R04"].Upgraded),
        new AlphaDefinition("RIN-R05","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R05"].Energy,GameplayCatalog.Cards["RIN-R05"].Mana,"契约共鸣",GameplayCatalog.Cards["RIN-R05"].Normal,GameplayCatalog.Cards["RIN-R05"].Upgraded),
        new AlphaDefinition("RIN-R06","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R06"].Energy,GameplayCatalog.Cards["RIN-R06"].Mana,"魔术刻印·积层",GameplayCatalog.Cards["RIN-R06"].Normal,GameplayCatalog.Cards["RIN-R06"].Upgraded),
        new AlphaDefinition("RIN-R07","CHAR_RIN",CardRarity.Rare,CardType.Attack,GameplayCatalog.Cards["RIN-R07"].Energy,GameplayCatalog.Cards["RIN-R07"].Mana,"宝石术式·星落",GameplayCatalog.Cards["RIN-R07"].Normal,GameplayCatalog.Cards["RIN-R07"].Upgraded),
        new AlphaDefinition("ARC-C03","CHAR_ARCHER",CardRarity.Common,CardType.Attack,GameplayCatalog.Cards["ARC-C03"].Energy,GameplayCatalog.Cards["ARC-C03"].Mana,"武装续击",GameplayCatalog.Cards["ARC-C03"].Normal,GameplayCatalog.Cards["ARC-C03"].Upgraded),
        new AlphaDefinition("ARC-C06","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C06"].Energy,GameplayCatalog.Cards["ARC-C06"].Mana,"即时投影",GameplayCatalog.Cards["ARC-C06"].Normal,GameplayCatalog.Cards["ARC-C06"].Upgraded),
        new AlphaDefinition("ARC-C07","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C07"].Energy,GameplayCatalog.Cards["ARC-C07"].Mana,"投影调整",GameplayCatalog.Cards["ARC-C07"].Normal,GameplayCatalog.Cards["ARC-C07"].Upgraded),
        new AlphaDefinition("ARC-C10","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C10"].Energy,GameplayCatalog.Cards["ARC-C10"].Mana,"独立防御",GameplayCatalog.Cards["ARC-C10"].Normal,GameplayCatalog.Cards["ARC-C10"].Upgraded),
        new AlphaDefinition("ARC-C11","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C11"].Energy,GameplayCatalog.Cards["ARC-C11"].Mana,"舍弃投影",GameplayCatalog.Cards["ARC-C11"].Normal,GameplayCatalog.Cards["ARC-C11"].Upgraded),
        new AlphaDefinition("ARC-C14","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C14"].Energy,GameplayCatalog.Cards["ARC-C14"].Mana,"护卫御主",GameplayCatalog.Cards["ARC-C14"].Normal,GameplayCatalog.Cards["ARC-C14"].Upgraded),
        new AlphaDefinition("ARC-C15","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C15"].Energy,GameplayCatalog.Cards["ARC-C15"].Mana,"空想整序",GameplayCatalog.Cards["ARC-C15"].Normal,GameplayCatalog.Cards["ARC-C15"].Upgraded),
        new AlphaDefinition("ARC-C16","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C16"].Energy,GameplayCatalog.Cards["ARC-C16"].Mana,"神速格挡",GameplayCatalog.Cards["ARC-C16"].Normal,GameplayCatalog.Cards["ARC-C16"].Upgraded),
        new AlphaDefinition("ARC-U01","CHAR_ARCHER",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["ARC-U01"].Energy,GameplayCatalog.Cards["ARC-U01"].Mana,"武装轮替",GameplayCatalog.Cards["ARC-U01"].Normal,GameplayCatalog.Cards["ARC-U01"].Upgraded),
        new AlphaDefinition("ARC-U02","CHAR_ARCHER",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["ARC-U02"].Energy,GameplayCatalog.Cards["ARC-U02"].Mana,"Broken Phantasm",GameplayCatalog.Cards["ARC-U02"].Normal,GameplayCatalog.Cards["ARC-U02"].Upgraded),
        new AlphaDefinition("ARC-U05","CHAR_ARCHER",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["ARC-U05"].Energy,GameplayCatalog.Cards["ARC-U05"].Mana,"精准狙击",GameplayCatalog.Cards["ARC-U05"].Normal,GameplayCatalog.Cards["ARC-U05"].Upgraded),
        new AlphaDefinition("ARC-U12","CHAR_ARCHER",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["ARC-U12"].Energy,GameplayCatalog.Cards["ARC-U12"].Mana,"一次性兵装",GameplayCatalog.Cards["ARC-U12"].Normal,GameplayCatalog.Cards["ARC-U12"].Upgraded),
        new AlphaDefinition("ARC-U13","CHAR_ARCHER",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["ARC-U13"].Energy,GameplayCatalog.Cards["ARC-U13"].Mana,"单独行动",GameplayCatalog.Cards["ARC-U13"].Normal,GameplayCatalog.Cards["ARC-U13"].Upgraded),
        new AlphaDefinition("ARC-U14","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U14"].Energy,GameplayCatalog.Cards["ARC-U14"].Mana,"武装再现",GameplayCatalog.Cards["ARC-U14"].Normal,GameplayCatalog.Cards["ARC-U14"].Upgraded),
        new AlphaDefinition("ARC-U15","CHAR_ARCHER",CardRarity.Uncommon,CardType.Attack,GameplayCatalog.Cards["ARC-U15"].Energy,GameplayCatalog.Cards["ARC-U15"].Mana,"双刀连舞",GameplayCatalog.Cards["ARC-U15"].Normal,GameplayCatalog.Cards["ARC-U15"].Upgraded),
        new AlphaDefinition("ARC-U16","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U16"].Energy,GameplayCatalog.Cards["ARC-U16"].Mana,"心眼防御",GameplayCatalog.Cards["ARC-U16"].Normal,GameplayCatalog.Cards["ARC-U16"].Upgraded),
        new AlphaDefinition("ARC-R03","CHAR_ARCHER",CardRarity.Rare,CardType.Skill,GameplayCatalog.Cards["ARC-R03"].Energy,GameplayCatalog.Cards["ARC-R03"].Mana,"高阶幻想崩坏",GameplayCatalog.Cards["ARC-R03"].Normal,GameplayCatalog.Cards["ARC-R03"].Upgraded),
        new AlphaDefinition("ARC-R05","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R05"].Energy,GameplayCatalog.Cards["ARC-R05"].Mana,"无供魔作战",GameplayCatalog.Cards["ARC-R05"].Normal,GameplayCatalog.Cards["ARC-R05"].Upgraded),
        new AlphaDefinition("ARC-R06","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R06"].Energy,GameplayCatalog.Cards["ARC-R06"].Mana,"千锤百炼",GameplayCatalog.Cards["ARC-R06"].Normal,GameplayCatalog.Cards["ARC-R06"].Upgraded),
        new AlphaDefinition("ARC-R07","CHAR_ARCHER",CardRarity.Rare,CardType.Attack,GameplayCatalog.Cards["ARC-R07"].Energy,GameplayCatalog.Cards["ARC-R07"].Mana,"鹤翼三连",GameplayCatalog.Cards["ARC-R07"].Normal,GameplayCatalog.Cards["ARC-R07"].Upgraded),
        new AlphaDefinition("RIN-C17","CHAR_RIN",CardRarity.Common,CardType.Attack,GameplayCatalog.Cards["RIN-C17"].Energy,GameplayCatalog.Cards["RIN-C17"].Mana,"魔力脉冲",GameplayCatalog.Cards["RIN-C17"].Normal,GameplayCatalog.Cards["RIN-C17"].Upgraded),
        new AlphaDefinition("RIN-C18","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C18"].Energy,GameplayCatalog.Cards["RIN-C18"].Mana,"宝石护体",GameplayCatalog.Cards["RIN-C18"].Normal,GameplayCatalog.Cards["RIN-C18"].Upgraded),
        new AlphaDefinition("RIN-C19","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C19"].Energy,GameplayCatalog.Cards["RIN-C19"].Mana,"预读术式",GameplayCatalog.Cards["RIN-C19"].Normal,GameplayCatalog.Cards["RIN-C19"].Upgraded),
        new AlphaDefinition("RIN-C20","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C20"].Energy,GameplayCatalog.Cards["RIN-C20"].Mana,"魔术护壁",GameplayCatalog.Cards["RIN-C20"].Normal,GameplayCatalog.Cards["RIN-C20"].Upgraded),
        new AlphaDefinition("RIN-C21","CHAR_RIN",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["RIN-C21"].Energy,GameplayCatalog.Cards["RIN-C21"].Mana,"咒缚转嫁",GameplayCatalog.Cards["RIN-C21"].Normal,GameplayCatalog.Cards["RIN-C21"].Upgraded),
        new AlphaDefinition("RIN-U17","CHAR_RIN",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["RIN-U17"].Energy,GameplayCatalog.Cards["RIN-U17"].Mana,"宝石再结晶",GameplayCatalog.Cards["RIN-U17"].Normal,GameplayCatalog.Cards["RIN-U17"].Upgraded),
        new AlphaDefinition("RIN-U18","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U18"].Energy,GameplayCatalog.Cards["RIN-U18"].Mana,"甘德·三重封锁",GameplayCatalog.Cards["RIN-U18"].Normal,GameplayCatalog.Cards["RIN-U18"].Upgraded),
        new AlphaDefinition("RIN-U19","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U19"].Energy,GameplayCatalog.Cards["RIN-U19"].Mana,"魔力超频",GameplayCatalog.Cards["RIN-U19"].Normal,GameplayCatalog.Cards["RIN-U19"].Upgraded),
        new AlphaDefinition("RIN-U20","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U20"].Energy,GameplayCatalog.Cards["RIN-U20"].Mana,"契约献祭",GameplayCatalog.Cards["RIN-U20"].Normal,GameplayCatalog.Cards["RIN-U20"].Upgraded),
        new AlphaDefinition("RIN-U21","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U21"].Energy,GameplayCatalog.Cards["RIN-U21"].Mana,"甘德·广域诅咒",GameplayCatalog.Cards["RIN-U21"].Normal,GameplayCatalog.Cards["RIN-U21"].Upgraded),
        new AlphaDefinition("RIN-U22","CHAR_RIN",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["RIN-U22"].Energy,GameplayCatalog.Cards["RIN-U22"].Mana,"咒印储能",GameplayCatalog.Cards["RIN-U22"].Normal,GameplayCatalog.Cards["RIN-U22"].Upgraded),
        new AlphaDefinition("RIN-U23","CHAR_RIN",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["RIN-U23"].Energy,GameplayCatalog.Cards["RIN-U23"].Mana,"预支未来",GameplayCatalog.Cards["RIN-U23"].Normal,GameplayCatalog.Cards["RIN-U23"].Upgraded),
        new AlphaDefinition("RIN-R08","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R08"].Energy,GameplayCatalog.Cards["RIN-R08"].Mana,"宝石无尽轮转",GameplayCatalog.Cards["RIN-R08"].Normal,GameplayCatalog.Cards["RIN-R08"].Upgraded),
        new AlphaDefinition("RIN-R09","CHAR_RIN",CardRarity.Rare,CardType.Attack,GameplayCatalog.Cards["RIN-R09"].Energy,GameplayCatalog.Cards["RIN-R09"].Mana,"五大元素·贯通",GameplayCatalog.Cards["RIN-R09"].Normal,GameplayCatalog.Cards["RIN-R09"].Upgraded),
        new AlphaDefinition("RIN-R10","CHAR_RIN",CardRarity.Rare,CardType.Skill,GameplayCatalog.Cards["RIN-R10"].Energy,GameplayCatalog.Cards["RIN-R10"].Mana,"宝石洪流",GameplayCatalog.Cards["RIN-R10"].Normal,GameplayCatalog.Cards["RIN-R10"].Upgraded),
        new AlphaDefinition("RIN-R11","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R11"].Energy,GameplayCatalog.Cards["RIN-R11"].Mana,"魔术刻印·指数演算",GameplayCatalog.Cards["RIN-R11"].Normal,GameplayCatalog.Cards["RIN-R11"].Upgraded),
        new AlphaDefinition("RIN-R12","CHAR_RIN",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["RIN-R12"].Energy,GameplayCatalog.Cards["RIN-R12"].Mana,"置换魔术·代偿",GameplayCatalog.Cards["RIN-R12"].Normal,GameplayCatalog.Cards["RIN-R12"].Upgraded),
        new AlphaDefinition("RIN-R13","CHAR_RIN",CardRarity.Rare,CardType.Attack,GameplayCatalog.Cards["RIN-R13"].Energy,GameplayCatalog.Cards["RIN-R13"].Mana,"五大元素·万象坍缩",GameplayCatalog.Cards["RIN-R13"].Normal,GameplayCatalog.Cards["RIN-R13"].Upgraded),
        new AlphaDefinition("ARC-C17","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C17"].Energy,GameplayCatalog.Cards["ARC-C17"].Mana,"自给回路",GameplayCatalog.Cards["ARC-C17"].Normal,GameplayCatalog.Cards["ARC-C17"].Upgraded),
        new AlphaDefinition("ARC-C18","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C18"].Energy,GameplayCatalog.Cards["ARC-C18"].Mana,"心眼·闪避",GameplayCatalog.Cards["ARC-C18"].Normal,GameplayCatalog.Cards["ARC-C18"].Upgraded),
        new AlphaDefinition("ARC-C19","CHAR_ARCHER",CardRarity.Common,CardType.Attack,GameplayCatalog.Cards["ARC-C19"].Energy,GameplayCatalog.Cards["ARC-C19"].Mana,"剑舞突进",GameplayCatalog.Cards["ARC-C19"].Normal,GameplayCatalog.Cards["ARC-C19"].Upgraded),
        new AlphaDefinition("ARC-C20","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C20"].Energy,GameplayCatalog.Cards["ARC-C20"].Mana,"投影回收",GameplayCatalog.Cards["ARC-C20"].Normal,GameplayCatalog.Cards["ARC-C20"].Upgraded),
        new AlphaDefinition("ARC-C21","CHAR_ARCHER",CardRarity.Common,CardType.Skill,GameplayCatalog.Cards["ARC-C21"].Energy,GameplayCatalog.Cards["ARC-C21"].Mana,"弓兵不屈",GameplayCatalog.Cards["ARC-C21"].Normal,GameplayCatalog.Cards["ARC-C21"].Upgraded),
        new AlphaDefinition("ARC-U17","CHAR_ARCHER",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["ARC-U17"].Energy,GameplayCatalog.Cards["ARC-U17"].Mana,"自律魔术回路",GameplayCatalog.Cards["ARC-U17"].Normal,GameplayCatalog.Cards["ARC-U17"].Upgraded),
        new AlphaDefinition("ARC-U18","CHAR_ARCHER",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["ARC-U18"].Energy,GameplayCatalog.Cards["ARC-U18"].Mana,"投影连锁",GameplayCatalog.Cards["ARC-U18"].Normal,GameplayCatalog.Cards["ARC-U18"].Upgraded),
        new AlphaDefinition("ARC-U19","CHAR_ARCHER",CardRarity.Uncommon,CardType.Power,GameplayCatalog.Cards["ARC-U19"].Energy,GameplayCatalog.Cards["ARC-U19"].Mana,"心眼·破格",GameplayCatalog.Cards["ARC-U19"].Normal,GameplayCatalog.Cards["ARC-U19"].Upgraded),
        new AlphaDefinition("ARC-U20","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U20"].Energy,GameplayCatalog.Cards["ARC-U20"].Mana,"破绽狙击",GameplayCatalog.Cards["ARC-U20"].Normal,GameplayCatalog.Cards["ARC-U20"].Upgraded),
        new AlphaDefinition("ARC-U21","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U21"].Energy,GameplayCatalog.Cards["ARC-U21"].Mana,"咒缚卸载",GameplayCatalog.Cards["ARC-U21"].Normal,GameplayCatalog.Cards["ARC-U21"].Upgraded),
        new AlphaDefinition("ARC-U22","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U22"].Energy,GameplayCatalog.Cards["ARC-U22"].Mana,"血契置换",GameplayCatalog.Cards["ARC-U22"].Normal,GameplayCatalog.Cards["ARC-U22"].Upgraded),
        new AlphaDefinition("ARC-U23","CHAR_ARCHER",CardRarity.Uncommon,CardType.Skill,GameplayCatalog.Cards["ARC-U23"].Energy,GameplayCatalog.Cards["ARC-U23"].Mana,"魔力洗练",GameplayCatalog.Cards["ARC-U23"].Normal,GameplayCatalog.Cards["ARC-U23"].Upgraded),
        new AlphaDefinition("ARC-R08","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R08"].Energy,GameplayCatalog.Cards["ARC-R08"].Mana,"投影·万象增殖",GameplayCatalog.Cards["ARC-R08"].Normal,GameplayCatalog.Cards["ARC-R08"].Upgraded),
        new AlphaDefinition("ARC-R09","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R09"].Energy,GameplayCatalog.Cards["ARC-R09"].Mana,"剑势洪流",GameplayCatalog.Cards["ARC-R09"].Normal,GameplayCatalog.Cards["ARC-R09"].Upgraded),
        new AlphaDefinition("ARC-R10","CHAR_ARCHER",CardRarity.Rare,CardType.Skill,GameplayCatalog.Cards["ARC-R10"].Energy,GameplayCatalog.Cards["ARC-R10"].Mana,"连环幻想崩坏",GameplayCatalog.Cards["ARC-R10"].Normal,GameplayCatalog.Cards["ARC-R10"].Upgraded),
        new AlphaDefinition("ARC-R11","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R11"].Energy,GameplayCatalog.Cards["ARC-R11"].Mana,"心眼·无尽",GameplayCatalog.Cards["ARC-R11"].Normal,GameplayCatalog.Cards["ARC-R11"].Upgraded),
        new AlphaDefinition("ARC-R12","CHAR_ARCHER",CardRarity.Rare,CardType.Attack,GameplayCatalog.Cards["ARC-R12"].Energy,GameplayCatalog.Cards["ARC-R12"].Mana,"无限剑势",GameplayCatalog.Cards["ARC-R12"].Normal,GameplayCatalog.Cards["ARC-R12"].Upgraded),
        new AlphaDefinition("ARC-R13","CHAR_ARCHER",CardRarity.Rare,CardType.Power,GameplayCatalog.Cards["ARC-R13"].Energy,GameplayCatalog.Cards["ARC-R13"].Mana,"独立行动·超越",GameplayCatalog.Cards["ARC-R13"].Normal,GameplayCatalog.Cards["ARC-R13"].Upgraded),
    });
    public static AlphaDefinition Get(string id)=>Definitions.Single(d=>d.Id==id);
    public static IReadOnlyList<AlphaDefinition> Pool(string owner)=>Definitions.Where(d=>d.Owner==owner).ToArray();
    public static CardModel Card(string id)=>id switch{
        "RIN-C04"=>ModelDb.Card<RinC04>(),
        "RIN-C05"=>ModelDb.Card<RinC05>(),
        "RIN-C08"=>ModelDb.Card<RinC08>(),
        "RIN-C10"=>ModelDb.Card<RinC10>(),
        "RIN-C12"=>ModelDb.Card<RinC12>(),
        "RIN-C13"=>ModelDb.Card<RinC13>(),
        "RIN-C15"=>ModelDb.Card<RinC15>(),
        "RIN-C16"=>ModelDb.Card<RinC16>(),
        "RIN-U01"=>ModelDb.Card<RinU01>(),
        "RIN-U04"=>ModelDb.Card<RinU04>(),
        "RIN-U06"=>ModelDb.Card<RinU06>(),
        "RIN-U10"=>ModelDb.Card<RinU10>(),
        "RIN-U12"=>ModelDb.Card<RinU12>(),
        "RIN-U14"=>ModelDb.Card<RinU14>(),
        "RIN-U15"=>ModelDb.Card<RinU15>(),
        "RIN-U16"=>ModelDb.Card<RinU16>(),
        "RIN-R04"=>ModelDb.Card<RinR04>(),
        "RIN-R05"=>ModelDb.Card<RinR05>(),
        "RIN-R06"=>ModelDb.Card<RinR06>(),
        "RIN-R07"=>ModelDb.Card<RinR07>(),
        "ARC-C03"=>ModelDb.Card<ArcC03>(),
        "ARC-C06"=>ModelDb.Card<ArcC06>(),
        "ARC-C07"=>ModelDb.Card<ArcC07>(),
        "ARC-C10"=>ModelDb.Card<ArcC10>(),
        "ARC-C11"=>ModelDb.Card<ArcC11>(),
        "ARC-C14"=>ModelDb.Card<ArcC14>(),
        "ARC-C15"=>ModelDb.Card<ArcC15>(),
        "ARC-C16"=>ModelDb.Card<ArcC16>(),
        "ARC-U01"=>ModelDb.Card<ArcU01>(),
        "ARC-U02"=>ModelDb.Card<ArcU02>(),
        "ARC-U05"=>ModelDb.Card<ArcU05>(),
        "ARC-U12"=>ModelDb.Card<ArcU12>(),
        "ARC-U13"=>ModelDb.Card<ArcU13>(),
        "ARC-U14"=>ModelDb.Card<ArcU14>(),
        "ARC-U15"=>ModelDb.Card<ArcU15>(),
        "ARC-U16"=>ModelDb.Card<ArcU16>(),
        "ARC-R03"=>ModelDb.Card<ArcR03>(),
        "ARC-R05"=>ModelDb.Card<ArcR05>(),
        "ARC-R06"=>ModelDb.Card<ArcR06>(),
        "ARC-R07"=>ModelDb.Card<ArcR07>(),
        "RIN-C17"=>ModelDb.Card<RinC17>(),
        "RIN-C18"=>ModelDb.Card<RinC18>(),
        "RIN-C19"=>ModelDb.Card<RinC19>(),
        "RIN-C20"=>ModelDb.Card<RinC20>(),
        "RIN-C21"=>ModelDb.Card<RinC21>(),
        "RIN-U17"=>ModelDb.Card<RinU17>(),
        "RIN-U18"=>ModelDb.Card<RinU18>(),
        "RIN-U19"=>ModelDb.Card<RinU19>(),
        "RIN-U20"=>ModelDb.Card<RinU20>(),
        "RIN-U21"=>ModelDb.Card<RinU21>(),
        "RIN-U22"=>ModelDb.Card<RinU22>(),
        "RIN-U23"=>ModelDb.Card<RinU23>(),
        "RIN-R08"=>ModelDb.Card<RinR08>(),
        "RIN-R09"=>ModelDb.Card<RinR09>(),
        "RIN-R10"=>ModelDb.Card<RinR10>(),
        "RIN-R11"=>ModelDb.Card<RinR11>(),
        "RIN-R12"=>ModelDb.Card<RinR12>(),
        "RIN-R13"=>ModelDb.Card<RinR13>(),
        "ARC-C17"=>ModelDb.Card<ArcC17>(),
        "ARC-C18"=>ModelDb.Card<ArcC18>(),
        "ARC-C19"=>ModelDb.Card<ArcC19>(),
        "ARC-C20"=>ModelDb.Card<ArcC20>(),
        "ARC-C21"=>ModelDb.Card<ArcC21>(),
        "ARC-U17"=>ModelDb.Card<ArcU17>(),
        "ARC-U18"=>ModelDb.Card<ArcU18>(),
        "ARC-U19"=>ModelDb.Card<ArcU19>(),
        "ARC-U20"=>ModelDb.Card<ArcU20>(),
        "ARC-U21"=>ModelDb.Card<ArcU21>(),
        "ARC-U22"=>ModelDb.Card<ArcU22>(),
        "ARC-U23"=>ModelDb.Card<ArcU23>(),
        "ARC-R08"=>ModelDb.Card<ArcR08>(),
        "ARC-R09"=>ModelDb.Card<ArcR09>(),
        "ARC-R10"=>ModelDb.Card<ArcR10>(),
        "ARC-R11"=>ModelDb.Card<ArcR11>(),
        "ARC-R12"=>ModelDb.Card<ArcR12>(),
        "ARC-R13"=>ModelDb.Card<ArcR13>(),
        _=>throw new ArgumentException("Unknown Alpha Reward ID")};
}
public abstract class AlphaRewardCard:StarterCard
{
    protected AlphaRewardCard(string id):this(AlphaRewardRegistry.Get(id)){}
    AlphaRewardCard(AlphaDefinition d):base(d.Type,TargetType.Self,d.Energy,false,d.Rarity){Definition=d;}
    public AlphaDefinition Definition{get;}
    public override string SourceCardId=>Definition.Id;
    public override string OwnerCharacterId=>Definition.Owner;
    public override int PrintedManaCost=>IsUpgraded?GameplayCatalog.Cards[SourceCardId].UpMana:Definition.Mana;
    protected override string NameText=>Definition.Name;
    protected override string RulesText=>GameplayCatalog.Text(this);
    public override CardPoolModel Pool=>OwnerCharacterId=="CHAR_RIN"?ModelDb.CardPool<RinAlphaRewardPool>():ModelDb.CardPool<ArcherAlphaRewardPool>();
    public override bool HasJewelChoice=>SourceCardId=="RIN-U01";
    public override IEnumerable<CardKeyword> CanonicalKeywords=>SourceCardId=="ARC-U14"?[CardKeyword.Exhaust]:[];
    internal string? PreparedSelection;
    internal ProjectedArm? PreparedArm;
    internal Creature? PreparedTarget;
    internal FieldStatus? PreparedField;
    public async Task<bool> PrepareChoice()=>await GameplayChoice.Prepare(this,null);
    public void ClearChoice(){PreparedSelection=null;PreparedArm=null;PreparedTarget=null;PreparedField=null;Plan=null;}
    protected override void OnUpgrade(){var s=GameplayCatalog.Cards[SourceCardId];if(s.UpEnergy!=s.Energy)EnergyCost.UpgradeBy(s.UpEnergy-s.Energy);}
}
public sealed class RinC04():AlphaRewardCard("RIN-C04");
public sealed class RinC05():AlphaRewardCard("RIN-C05");
public sealed class RinC08():AlphaRewardCard("RIN-C08");
public sealed class RinC10():AlphaRewardCard("RIN-C10");
public sealed class RinC12():AlphaRewardCard("RIN-C12");
public sealed class RinC13():AlphaRewardCard("RIN-C13");
public sealed class RinC15():AlphaRewardCard("RIN-C15");
public sealed class RinC16():AlphaRewardCard("RIN-C16");
public sealed class RinU01():AlphaRewardCard("RIN-U01");
public sealed class RinU04():AlphaRewardCard("RIN-U04");
public sealed class RinU06():AlphaRewardCard("RIN-U06");
public sealed class RinU10():AlphaRewardCard("RIN-U10");
public sealed class RinU12():AlphaRewardCard("RIN-U12");
public sealed class RinU14():AlphaRewardCard("RIN-U14");
public sealed class RinU15():AlphaRewardCard("RIN-U15");
public sealed class RinU16():AlphaRewardCard("RIN-U16");
public sealed class RinR04():AlphaRewardCard("RIN-R04");
public sealed class RinR05():AlphaRewardCard("RIN-R05");
public sealed class RinR06():AlphaRewardCard("RIN-R06");
public sealed class RinR07():AlphaRewardCard("RIN-R07");
public sealed class ArcC03():AlphaRewardCard("ARC-C03");
public sealed class ArcC06():AlphaRewardCard("ARC-C06");
public sealed class ArcC07():AlphaRewardCard("ARC-C07");
public sealed class ArcC10():AlphaRewardCard("ARC-C10");
public sealed class ArcC11():AlphaRewardCard("ARC-C11");
public sealed class ArcC14():AlphaRewardCard("ARC-C14");
public sealed class ArcC15():AlphaRewardCard("ARC-C15");
public sealed class ArcC16():AlphaRewardCard("ARC-C16");
public sealed class ArcU01():AlphaRewardCard("ARC-U01");
public sealed class ArcU02():AlphaRewardCard("ARC-U02");
public sealed class ArcU05():AlphaRewardCard("ARC-U05");
public sealed class ArcU12():AlphaRewardCard("ARC-U12");
public sealed class ArcU13():AlphaRewardCard("ARC-U13");
public sealed class ArcU14():AlphaRewardCard("ARC-U14");
public sealed class ArcU15():AlphaRewardCard("ARC-U15");
public sealed class ArcU16():AlphaRewardCard("ARC-U16");
public sealed class ArcR03():AlphaRewardCard("ARC-R03");
public sealed class ArcR05():AlphaRewardCard("ARC-R05");
public sealed class ArcR06():AlphaRewardCard("ARC-R06");
public sealed class ArcR07():AlphaRewardCard("ARC-R07");

[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinC17():AlphaRewardCard("RIN-C17");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinC18():AlphaRewardCard("RIN-C18");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinC19():AlphaRewardCard("RIN-C19");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinC20():AlphaRewardCard("RIN-C20");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinC21():AlphaRewardCard("RIN-C21");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU17():AlphaRewardCard("RIN-U17");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU18():AlphaRewardCard("RIN-U18");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU19():AlphaRewardCard("RIN-U19");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU20():AlphaRewardCard("RIN-U20");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU21():AlphaRewardCard("RIN-U21");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU22():AlphaRewardCard("RIN-U22");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinU23():AlphaRewardCard("RIN-U23");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR08():AlphaRewardCard("RIN-R08");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR09():AlphaRewardCard("RIN-R09");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR10():AlphaRewardCard("RIN-R10");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR11():AlphaRewardCard("RIN-R11");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR12():AlphaRewardCard("RIN-R12");
[Pool(typeof(RinAlphaRewardPool))]
public sealed class RinR13():AlphaRewardCard("RIN-R13");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcC17():AlphaRewardCard("ARC-C17");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcC18():AlphaRewardCard("ARC-C18");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcC19():AlphaRewardCard("ARC-C19");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcC20():AlphaRewardCard("ARC-C20");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcC21():AlphaRewardCard("ARC-C21");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU17():AlphaRewardCard("ARC-U17");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU18():AlphaRewardCard("ARC-U18");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU19():AlphaRewardCard("ARC-U19");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU20():AlphaRewardCard("ARC-U20");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU21():AlphaRewardCard("ARC-U21");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU22():AlphaRewardCard("ARC-U22");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcU23():AlphaRewardCard("ARC-U23");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR08():AlphaRewardCard("ARC-R08");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR09():AlphaRewardCard("ARC-R09");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR10():AlphaRewardCard("ARC-R10");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR11():AlphaRewardCard("ARC-R11");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR12():AlphaRewardCard("ARC-R12");
[Pool(typeof(ArcherAlphaRewardPool))]
public sealed class ArcR13():AlphaRewardCard("ARC-R13");
