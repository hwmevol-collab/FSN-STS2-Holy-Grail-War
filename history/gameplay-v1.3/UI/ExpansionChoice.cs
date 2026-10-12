using MegaCrit.Sts2.Core.Models.Powers;
namespace RinArcherCore;
public static class ExpansionChoice
{
    static async Task<T[]?> Select<T>(string title,T[] legal,int max,bool required,Func<T,string> label)
    {
        if(legal.Length==0)return required?null:[];var selected=new List<T>();
        while(selected.Count<max)
        {
            var options=legal.Select((item,i)=>(item,i)).Where(x=>!selected.Contains(x.item)).Select(x=>(x.i.ToString(),label(x.item))).ToList();
            if(!required||selected.Count>0)options.Add(("DONE","确认选择（已选"+selected.Count+"项）"));
            var key=await RewardChoice.Ask(title,options,"取消本次出牌");if(key==null)return null;if(key=="DONE")break;selected.Add(legal[int.Parse(key)]);
        }
        return selected.ToArray();
    }
    public static async Task<bool> Prepare(ContractRuntime d,StarterCard c,GameplayPlayPlan p)
    {
        bool up=c.IsUpgraded;string? key;p.ArmUsesSnapshot=d.ArmUses;
        switch(c.SourceCardId)
        {
            case "RIN_S_REINFORCE_PROJECTION":
                p.Selection=await RewardChoice.Ask(c.Title,[("SELF",$"凛下一次直接伤害或自身格挡增加{(up?12:8)}点"),("ARCHER","强化下一件成功投影的兵装")]);if(p.Selection==null)return false;
                if(p.Selection=="ARCHER"&&d.Jewel>0){key=await RewardChoice.Ask("宝石强化",[("BASE","不使用宝石"),("BOOST","宝石强化：兵装本战斗契约魔力费用降低1")]);if(key==null)return false;p.Boost=key=="BOOST";}break;
            case "ARC_S_COVER":p.Selection=await RewardChoice.Ask(c.Title,[("SELF",$"弓兵获得{(up?14:10)}格挡，抽1张牌"),("SUPPORT",$"凛获得{(up?10:7)}格挡，可整理手牌")]);if(p.Selection==null)return false;break;
            case "RIN-C19":p.Member="CHAR_RIN";var cards=await GameplayChoice.SelectCards(d,d.Rin,2,c,false,false);if(cards==null)return false;p.Cards=cards;break;
            case "RIN-C20":
                var modes=new List<(string,string)>{("BASE","仅获得基础格挡")};if(d.Mana>=2)modes.Add(("EXTRA","额外支付2契约魔力，增加格挡并净化"));key=await RewardChoice.Ask(c.Title,modes);if(key==null)return false;
                if(key=="EXTRA")
                {
                    p.AdditionalMana=2;var statuses=d.Rin.Creature.Powers.Where(s=>s.Amount>0&&s is WeakPower or FrailPower).ToArray();
                    if(statuses.Length>0){var chosen=await Select(c.Title+"：移除1层",statuses,1,true,s=>s.Title.GetFormattedText()+" "+s.Amount);if(chosen==null)return false;p.Cleanse=chosen[0];}
                }break;
            case "RIN-C21":case "ARC-U21":
                var source=c.OwnerCharacterId=="CHAR_RIN"?d.Rin:d.Archer;var dest=source==d.Rin?d.Archer:d.Rin;
                var legal=d.Transferable(source,dest);int max=c.SourceCardId=="RIN-C21"?(up?2:1):(up?3:2);
                if(legal.Length>0){var chosen=await Select(c.Title+"：转移状态",legal,max,true,s=>s.Title.GetFormattedText()+" "+s.Amount);if(chosen==null)return false;p.Debuffs=chosen;}break;
            case "RIN-R13":p.AdditionalMana=d.Mana;p.DirectJewels=d.Jewel;break;
            case "ARC-R12":
                var choices=new List<(string,string)>{("BASE","不追加契约魔力")};if(d.Mana>0)choices.Add(("ALL",$"额外支付全部{d.Mana}契约魔力"));key=await RewardChoice.Ask(c.Title,choices);if(key==null)return false;p.AdditionalMana=key=="ALL"?d.Mana:0;break;
            case "ARC-C20":case "ARC-U23":
                var pile=c.SourceCardId=="ARC-C20"?d.Archer.Exhaust:d.Archer.Hand;
                var arms=pile.Cards.OfType<ProjectedArm>().Where(a=>a.Owner==d.Player&&a.OwnerCharacterId=="CHAR_ARCHER").ToArray();
                int count=c.SourceCardId=="ARC-C20"?Math.Min(up?3:2,CardPile.MaxCardsInHand-d.Archer.Hand.Cards.Count+1):(up?2:1);
                var picked=await Select(c.Title,arms,count,c.SourceCardId=="ARC-U23",a=>a.Title+" · 契约魔力"+a.ModifiedManaCost);if(picked==null)return false;p.Arms=picked;break;
        }
        return true;
    }
}
