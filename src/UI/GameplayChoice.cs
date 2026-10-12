namespace RinArcherCore;
public static class GameplayChoice
{
    static readonly string[] DamageIds=["RIN-C17","RIN-U18","RIN-R09","ARC-C19","ARC-U20","ARC-R12","RIN_S_GANDR","RIN_S_JEWEL_RELEASE","ARC_S_BOW_SHOT","ARC_S_CLOSE_COMBAT","RIN-C04","RIN-C10","RIN-U01","RIN-U04","RIN-R07","ARC-C03","ARC-U01","ARC-U02","ARC-U05","ARC-U15","ARC-R03","ARC-R07","ARM_KANSHOU_BAKUYA","ARM_HRUNTING"];
    public static Creature[] Enemies(ContractRuntime d,bool any=false)=>d.Enemy==null?d.Combat.Enemies.Where(e=>e.IsAlive).ToArray():any?new[]{d.Enemy.Master,d.Enemy.Servant}.Where(e=>e.IsAlive).ToArray():d.Enemy.Active.IsAlive?[d.Enemy.Active]:[];
    public static async Task<Creature?> Enemy(StarterCard c,Creature[] targets)
    {
        if(targets.Length==1)return targets[0];
        var id=await RewardChoice.Ask(c.Title+FsnLoc.Text("UI_C48BB959A7BE"),targets.Select((t,i)=>(i.ToString(),FsnLoc.Format("UI_589DE24E95E5", t.Monster?.Title.GetFormattedText()??t.LogName, t.CurrentHp, t.Block))).ToArray());return id==null?null:targets[int.Parse(id)];
    }
    static async Task<string?> Member(ContractRuntime d,string title,bool tuning=false,StarterCard? source=null)
        =>await RewardChoice.Ask(title,new[]{d.Rin,d.Archer}.Where(m=>!tuning||d.CanTune(m,source)).Select(m=>(m.CharacterId,FsnLoc.Format("UI_F3BF9FF4FE0E", (m==d.Rin?FsnLoc.Text("UI_D5116EA0D04E"):FsnLoc.Text("UI_7DD139DD5204")), (m.IsActive?FsnLoc.Text("UI_5E1FCDEF674C"):FsnLoc.Text("UI_CF2E968D2598")), m.Hand.Cards.Count))).ToArray());
    // Real references selected in real hand order. Preview selection is read-only.
    public static async Task<CardModel[]?> SelectCards(ContractRuntime d,CharacterRuntime member,int max,StarterCard? source,bool required,bool tuning=true)
    {
        var legal=d.TuningCards(member,source);if(tuning&&!d.CanTune(member,source))return required?null:[];
        if(legal.Length==0)return required?null:[];
        var selected=new List<CardModel>();
        while(selected.Count<max)
        {
            var options=legal.Where(c=>!selected.Contains(c)).Select((c,i)=>("CARD:"+Array.IndexOf(legal,c),c.Title)).ToList();
            if(!required||selected.Count>0)options.Add(("DONE",selected.Count==0?FsnLoc.Text("UI_AAC793E26042"):FsnLoc.Text("UI_DEC92FE2243E")+selected.Count+FsnLoc.Text("UI_FF1D9810196F")));
            var id=await RewardChoice.Ask(FsnLoc.Format("UI_4CC9BAA18AC6", (member==d.Rin?FsnLoc.Text("UI_D5116EA0D04E"):FsnLoc.Text("UI_7DD139DD5204")), max, selected.Count),options,FsnLoc.Text("UI_3B45635F196B"));
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
            id=await RewardChoice.Ask(c.Title+FsnLoc.Text("UI_D7E4323C6B6B"),[("BASE",FsnLoc.Text("UI_F78F7882E4B8")),("BOOST",d.AlphaPowers.ContainsKey("RIN-R04")&&!d.FreeJewelBoostUsed?FsnLoc.Text("UI_1FCFA8AC3F35"):FsnLoc.Text("UI_F49AAEF6460B"))]);if(id==null)return false;p.Boost=id=="BOOST";
        }
        switch(c.SourceCardId)
        {
            case "RIN_S_MANA_SUPPLY":var modes=new List<(string,string)>();if(d.Mana<d.MaxMana)modes.Add(("GAIN_MANA",FsnLoc.Format("UI_8078C83255B2", (up?3:2))));if(d.Mana>=(up?2:3))modes.Add(("MANA_TO_ENERGY",FsnLoc.Format("UI_93BD98621482", (up?2:3))));p.Selection=await RewardChoice.Ask(c.Title,modes);if(p.Selection==null)return false;if(p.Selection=="MANA_TO_ENERGY")p.AdditionalMana=up?2:3;break;
            case "ARC_S_COVER":if(p.Selection=="SUPPORT"&&!await Tune("CHAR_RIN",up?2:1,false))return false;break;
            case "RIN-C08":if(!await Tune("CHAR_ARCHER",up?2:1,false))return false;break;
            case "RIN-C15":p.Member=await Member(d,c.Title,true,c);if(p.Member==null||!await Tune(p.Member,up?2:1,true))return false;break;
            case "RIN-C16":case "RIN-U16":p.Member=await Member(d,c.Title);if(p.Member==null)return false;break;
            case "ARC-U16":p.Member=await Member(d,c.Title);if(p.Member==null)return false;if(!d.Member(p.Member).IsActive&&!await Tune(p.Member,up?2:1,false))return false;break;
            case "RIN-C12":p.Selection=await RewardChoice.Ask(c.Title,[("DEFENSE",FsnLoc.Format("UI_6B5925A7EB77", (up?11:8))),("SUPPLY",FsnLoc.Format("UI_3F5777EF16E2", (up?3:2), (up?2:1)))]);if(p.Selection==null)return false;if(p.Selection=="SUPPLY"){p.Member=await Member(d,c.Title);if(p.Member==null)return false;}break;
            case "RIN-U10":p.DirectJewels=1;break;
            case "RIN-U14":
                var branches=new List<(string,string)>{("ATTACK",FsnLoc.Format("UI_2D828437E4CB", (up?18:14))),("DEFENSE",FsnLoc.Format("UI_3A924F79F0A7", (up?18:14)))};if(d.CanTune(d.Rin,c)||d.CanTune(d.Archer,c))branches.Add(("TUNING",FsnLoc.Format("UI_D3089C758D6A", (up?3:2))));p.Selection=await RewardChoice.Ask(c.Title,branches);if(p.Selection==null)return false;p.DirectJewels=1;
                if(p.Selection!="ATTACK"){p.Member=await Member(d,c.Title,p.Selection=="TUNING",c);if(p.Member==null)return false;if(p.Selection=="TUNING"&&!await Tune(p.Member,up?3:2,true))return false;}break;
            case "RIN-R07":
                id=await RewardChoice.Ask(c.Title+FsnLoc.Text("UI_15CD89736F4A"),Enumerable.Range(1,Math.Min(3,d.Jewel)).Select(j=>(j.ToString(),FsnLoc.Format("UI_8E38EC31A7DD", j))).ToArray());if(id==null)return false;p.DirectJewels=int.Parse(id);
                id=await RewardChoice.Ask(c.Title+FsnLoc.Text("UI_BE7414CAD779"),Enumerable.Range(0,Math.Min(4,d.Mana)+1).Select(m=>(m.ToString(),FsnLoc.Format("UI_68926E5A51BB", m, (up?16:12)+(up?12:10)*p.DirectJewels+(up?5:4)*m))).ToArray());if(id==null)return false;p.AdditionalMana=int.Parse(id);break;
            case "ARC-C10":var defense=new List<(string,string)>{("BASE",FsnLoc.Text("UI_5BED112B754E"))};if(d.Mana>=2)defense.Add(("EXTRA",FsnLoc.Text("UI_BF5803C72282")));id=await RewardChoice.Ask(c.Title,defense);if(id==null)return false;p.AdditionalMana=id=="EXTRA"?2:0;break;
            case "ARC-C15":p.Member="CHAR_ARCHER";var discards=await SelectCards(d,d.Archer,1,c,true,false);if(discards==null)return false;p.Cards=discards;break;
            case "RIN-U06":var fields=RewardRules.Fields(d);if(fields.Length>0){id=await RewardChoice.Ask(c.Title,fields.Select((f,i)=>(i.ToString(),FsnLoc.Text("UI_894E42C148D7")+f.FieldId)).ToArray());if(id==null)return false;p.Field=fields[int.Parse(id)];}break;
            case "ARC_S_TRACE":case "ARC-C06":case "ARC-U14":
                var arms=c.SourceCardId=="ARC-C06"?Arsenal.Ids.Take(2):c.SourceCardId=="ARC-U14"?Arsenal.Ids.Where(a=>!d.ProjectedArmsResolvedThisCombat.Contains(a)):Arsenal.Ids;
                if(c.SourceCardId=="ARC-U14"&&!arms.Any()){arms=Arsenal.Ids;p.AdditionalMana=1;}
                p.ArmId=await RewardChoice.Ask(c.Title+FsnLoc.Text("UI_C92FEF22854F")+(p.AdditionalMana>0?FsnLoc.Text("UI_A4BC92B8B152"):""),arms.Select(a=>(a,Arsenal.Get(a).Title)).ToArray());if(p.ArmId==null)return false;break;
            case "ARC-C07":case "ARC-C11":case "ARC-U02":case "ARC-R03":case "ARC-R10":var weapons=RewardRules.Arms(d,c.SourceCardId is "ARC-U02" or "ARC-R03");id=await RewardChoice.Ask(c.Title,weapons.Select(a=>(a.InstanceId,FsnLoc.Format("UI_0253AD3A48C1", a.Title, a.ModifiedManaCost))).ToArray());if(id==null)return false;p.Arm=weapons.Single(a=>a.InstanceId==id);break;
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
