namespace RinArcherCore;
public static class GameplayChoice
{
    static readonly string[] DamageIds=["RIN-C17","RIN-U18","RIN-R09","ARC-C19","ARC-U20","ARC-R12","RIN_S_GANDR","RIN_S_JEWEL_RELEASE","ARC_S_BOW_SHOT","ARC_S_CLOSE_COMBAT","RIN-C04","RIN-C10","RIN-U01","RIN-U04","RIN-R07","ARC-C03","ARC-U01","ARC-U02","ARC-U05","ARC-U15","ARC-R03","ARC-R07","ARM_KANSHOU_BAKUYA","ARM_HRUNTING"];
    public static Creature[] Enemies(ContractRuntime d,bool any=false)=>d.Enemy==null?d.Combat.Enemies.Where(e=>e.IsAlive).ToArray():any?new[]{d.Enemy.Master,d.Enemy.Servant}.Where(e=>e.IsAlive).ToArray():d.Enemy.Active.IsAlive?[d.Enemy.Active]:[];
    public static async Task<Creature?> Enemy(StarterCard c,Creature[] targets)
    {
        if(targets.Length==1)return targets[0];
        var id=await RewardChoice.Ask(c.Title+"：选择敌方目标",targets.Select((t,i)=>(i.ToString(),$"{t.Monster?.Title.GetFormattedText()??t.LogName} · 生命 {t.CurrentHp} · 格挡 {t.Block}")).ToArray());return id==null?null:targets[int.Parse(id)];
    }
    static async Task<string?> Member(ContractRuntime d,string title,bool tuning=false,StarterCard? source=null)
        =>await RewardChoice.Ask(title,new[]{d.Rin,d.Archer}.Where(m=>!tuning||d.CanTune(m,source)).Select(m=>(m.CharacterId,$"{(m==d.Rin?"凛":"弓兵")} · {(m.IsActive?"前排":"后备")} · 手牌 {m.Hand.Cards.Count}/10")).ToArray());
    // Real references selected in real hand order. Preview selection is read-only.
    public static async Task<CardModel[]?> SelectCards(ContractRuntime d,CharacterRuntime member,int max,StarterCard? source,bool required,bool tuning=true)
    {
        var legal=d.TuningCards(member,source);if(tuning&&!d.CanTune(member,source))return required?null:[];
        if(legal.Length==0)return required?null:[];
        var selected=new List<CardModel>();
        while(selected.Count<max)
        {
            var options=legal.Where(c=>!selected.Contains(c)).Select((c,i)=>("CARD:"+Array.IndexOf(legal,c),c.Title)).ToList();
            if(!required||selected.Count>0)options.Add(("DONE",selected.Count==0?"不整理，只结算基础效果":"确认弃置 "+selected.Count+" 张并尝试等量抽牌"));
            var id=await RewardChoice.Ask($"{(member==d.Rin?"凛":"弓兵")}手牌 · 最多{max}张 · 已选{selected.Count} · 手牌上限10",options,"取消本次选择");
            if(id==null)return null;if(id=="DONE")break;selected.Add(legal[int.Parse(id[5..])]);
        }
        return legal.Where(selected.Contains).ToArray();
    }
    public static Task<CardModel[]?> OptionalTuning(ContractRuntime d,CharacterRuntime member,int max,StarterCard? source)
        =>SelectCards(d,member,max,source,false);
    public static async Task<bool> Prepare(StarterCard c,Creature? nativeTarget,bool auto=false)
    {
        var d=ContractRuntime.For(c.Owner)!;var p=new GameplayPlayPlan();c.Plan=null;bool up=c.IsUpgraded;string? id;
        async Task<bool> Tune(string member,int max,bool required)
        {p.Member=member;var cards=await SelectCards(d,d.Member(member),max,c,required);if(cards==null)return false;p.Cards=cards;return true;}
        if(!await ExpansionChoice.Prepare(d,c,p))return false;
        if(c.HasJewelChoice&&c.SourceCardId!="RIN_S_REINFORCE_PROJECTION"&&d.Jewel>0)
        {
            id=await RewardChoice.Ask(c.Title+"：宝石强化",[("BASE","普通效果，不使用宝石"),("BOOST",d.AlphaPowers.ContainsKey("RIN-R04")&&!d.FreeJewelBoostUsed?"使用宝石强化（本轮首次免费）":"使用宝石强化，支付1宝石")]);if(id==null)return false;p.Boost=id=="BOOST";
        }
        switch(c.SourceCardId)
        {
            case "RIN_S_MANA_SUPPLY":var modes=new List<(string,string)>();if(d.Mana<d.MaxMana)modes.Add(("GAIN_MANA",$"获得{(up?3:2)}契约魔力"));if(d.Mana>=(up?2:3))modes.Add(("MANA_TO_ENERGY",$"支付{(up?2:3)}契约魔力，获得1能量"));p.Selection=await RewardChoice.Ask(c.Title,modes);if(p.Selection==null)return false;if(p.Selection=="MANA_TO_ENERGY")p.AdditionalMana=up?2:3;break;
            case "ARC_S_COVER":if(p.Selection=="SUPPORT"&&!await Tune("CHAR_RIN",up?2:1,false))return false;break;
            case "RIN-C08":if(!await Tune("CHAR_ARCHER",up?2:1,false))return false;break;
            case "RIN-C15":p.Member=await Member(d,c.Title,true,c);if(p.Member==null||!await Tune(p.Member,up?2:1,true))return false;break;
            case "RIN-C16":case "RIN-U16":p.Member=await Member(d,c.Title);if(p.Member==null)return false;break;
            case "ARC-U16":p.Member=await Member(d,c.Title);if(p.Member==null)return false;if(!d.Member(p.Member).IsActive&&!await Tune(p.Member,up?2:1,false))return false;break;
            case "RIN-C12":p.Selection=await RewardChoice.Ask(c.Title,[("DEFENSE",$"凛获得{(up?11:8)}格挡"),("SUPPLY",$"获得{(up?3:2)}契约魔力，指定成员抽{(up?2:1)}张")]);if(p.Selection==null)return false;if(p.Selection=="SUPPLY"){p.Member=await Member(d,c.Title);if(p.Member==null)return false;}break;
            case "RIN-U10":p.DirectJewels=1;break;
            case "RIN-U14":
                var branches=new List<(string,string)>{("ATTACK",$"前排{(up?18:14)}伤害"),("DEFENSE",$"指定成员{(up?18:14)}格挡")};if(d.CanTune(d.Rin,c)||d.CanTune(d.Archer,c))branches.Add(("TUNING",$"指定成员整理最多{(up?3:2)}张"));p.Selection=await RewardChoice.Ask(c.Title,branches);if(p.Selection==null)return false;p.DirectJewels=1;
                if(p.Selection!="ATTACK"){p.Member=await Member(d,c.Title,p.Selection=="TUNING",c);if(p.Member==null)return false;if(p.Selection=="TUNING"&&!await Tune(p.Member,up?3:2,true))return false;}break;
            case "RIN-R07":
                id=await RewardChoice.Ask(c.Title+"：支付宝石",Enumerable.Range(1,Math.Min(3,d.Jewel)).Select(j=>(j.ToString(),$"支付{j}宝石（直接消费）")).ToArray());if(id==null)return false;p.DirectJewels=int.Parse(id);
                id=await RewardChoice.Ask(c.Title+"：追加契约魔力",Enumerable.Range(0,Math.Min(4,d.Mana)+1).Select(m=>(m.ToString(),$"追加{m}契约魔力 · 总伤害{(up?16:12)+(up?12:10)*p.DirectJewels+(up?5:4)*m}")).ToArray());if(id==null)return false;p.AdditionalMana=int.Parse(id);break;
            case "ARC-C10":var defense=new List<(string,string)>{("BASE","仅基础格挡")};if(d.Mana>=2)defense.Add(("EXTRA","追加支付2契约魔力，双方额外格挡"));id=await RewardChoice.Ask(c.Title,defense);if(id==null)return false;p.AdditionalMana=id=="EXTRA"?2:0;break;
            case "ARC-C15":p.Member="CHAR_ARCHER";var discards=await SelectCards(d,d.Archer,1,c,true,false);if(discards==null)return false;p.Cards=discards;break;
            case "RIN-U06":var fields=RewardRules.Fields(d);if(fields.Length>0){id=await RewardChoice.Ask(c.Title,fields.Select((f,i)=>(i.ToString(),"压制 "+f.FieldId)).ToArray());if(id==null)return false;p.Field=fields[int.Parse(id)];}break;
            case "ARC_S_TRACE":case "ARC-C06":case "ARC-U14":
                var arms=c.SourceCardId=="ARC-C06"?Arsenal.Ids.Take(2):c.SourceCardId=="ARC-U14"?Arsenal.Ids.Where(a=>!d.ProjectedArmsResolvedThisCombat.Contains(a)):Arsenal.Ids;
                if(c.SourceCardId=="ARC-U14"&&!arms.Any()){arms=Arsenal.Ids;p.AdditionalMana=1;}
                p.ArmId=await RewardChoice.Ask(c.Title+"：生成兵装"+(p.AdditionalMana>0?"（额外支付1契约魔力）":""),arms.Select(a=>(a,Arsenal.Get(a).Title)).ToArray());if(p.ArmId==null)return false;break;
            case "ARC-C07":case "ARC-C11":case "ARC-U02":case "ARC-R03":case "ARC-R10":var weapons=RewardRules.Arms(d,c.SourceCardId is "ARC-U02" or "ARC-R03");id=await RewardChoice.Ask(c.Title,weapons.Select(a=>(a.InstanceId,$"{a.Title} · 契约魔力{a.ModifiedManaCost}")).ToArray());if(id==null)return false;p.Arm=weapons.Single(a=>a.InstanceId==id);break;
        }
        bool damage=DamageIds.Contains(c.SourceCardId)||c.SourceCardId=="RIN-U14"&&p.Selection=="ATTACK"||c.SourceCardId=="RIN-U06"&&p.Field==null;
        if(damage)
        {
            var legal=c.SourceCardId=="ARC-U05"?RewardRules.PrecisionTargets(d):Enemies(d,c.SourceCardId=="ARM_HRUNTING"||c.SourceCardId=="ARC-R03"&&p.Arm?.ArmId=="ARM_HRUNTING");
            p.Target=nativeTarget!=null&&legal.Contains(nativeTarget)?nativeTarget:await Enemy(c,legal);if(p.Target==null)return false;
        }
        int mana=(auto?0:d.EffectiveManaCost(c.OwnerCharacterId,c.PrintedManaCost,c.ModifiedManaCost))+p.AdditionalMana;
        if(d.AlphaPowers.ContainsKey("RIN-U12")&&!d.U12ManaEventUsed&&mana>=2&&d.CanTune(d.Reserve,c)&&p.Member!=d.Reserve.CharacterId)
        {p.ReserveMember=d.Reserve.CharacterId;var cards=await OptionalTuning(d,d.Reserve,1,c);if(cards==null)return false;p.ReserveCards=cards;}
        if(!GameplayRules.ValidPlan(d,c,p,auto))return false;c.Plan=p;return true;
    }
}
