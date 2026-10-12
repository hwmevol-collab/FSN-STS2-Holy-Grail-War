using MegaCrit.Sts2.Core.Models.Powers;
namespace RinArcherCore;
public static class ExpansionRules
{
    public static async Task<bool> Play(PlayerChoiceContext ctx,CardPlay play,ContractRuntime d,StarterCard c)
    {
        var r=d.Receipt(c);var p=r.Plan;bool up=c.IsUpgraded;int V(int n,int u)=>up?u:n;var owner=d.Member(c.OwnerCharacterId);
        Task Draw(int n)=>d.DrawMember(ctx,owner,n);
        Task Block(int n)=>CreatureCmd.GainBlock(owner.Creature,d.BlockAmount(c,owner,n),ValueProp.Move,play);
        async Task Damage(Creature? target,int amount,int hits=1,bool unblockable=false)
        {
            if(target?.IsAlive!=true)return;var profile=d.DamageProfile(c,amount,hits,target.CombatId.ToString()!);
            foreach(int n in profile){if(d.Finished||!target.IsAlive)break;await CreatureCmd.Damage(ctx,target,n,unblockable?ValueProp.Move|ValueProp.Unblockable:ValueProp.Move,owner.Creature,c);await d.CheckLethal(ctx);}
        }
        async Task Debuffs(Creature? target,int n,bool frail)
        {
            if(target?.IsAlive!=true)return;
            await PowerCmd.Apply<WeakPower>(ctx,target,n,owner.Creature,c);await PowerCmd.Apply<VulnerablePower>(ctx,target,n,owner.Creature,c);
            if(frail)await PowerCmd.Apply<FrailPower>(ctx,target,n,owner.Creature,c);
        }
        async Task<int> Transfer(CharacterRuntime recipient)
        {int moved=0;if(play.PlayIndex==0)foreach(var status in p.Debuffs)if(await d.TransferDebuff(ctx,status,recipient))moved++;return moved;}
        switch(c.SourceCardId)
        {
            case "RIN-C17":await Damage(d.PlayTarget(c),V(9,12));d.GainMana(V(2,3));break;
            case "RIN-C18":await Block(V(7,9));d.GainJewel(V(1,2));break;
            case "RIN-C19":if(play.PlayIndex==0&&p.Cards.Length>0)await d.DiscardMember(ctx,d.Rin,p.Cards,p.Cards.Length+V(1,2));else await Draw(p.Cards.Length+V(1,2));break;
            case "RIN-C20":await Block(V(10,14)+(p.AdditionalMana>0?V(6,8):0));if(play.PlayIndex==0&&p.Cleanse!=null&&p.Cleanse.Owner.Powers.Contains(p.Cleanse))await PowerCmd.ModifyAmount(ctx,p.Cleanse,-1,null,null);break;
            case "RIN-C21":if(p.Debuffs.Length==0)await Draw(V(1,2));else await Transfer(d.Archer);break;
            case "RIN-U18":await Debuffs(d.PlayTarget(c),V(2,3),true);break;
            case "RIN-U19":await d.ExpansionEnergy(V(2,3));await Draw(V(2,3));break;
            case "RIN-U20":if(play.PlayIndex==0)await CreatureCmd.Damage(ctx,d.Archer.Creature,V(6,4),ValueProp.Unpowered|ValueProp.Unblockable,null,c);await d.ExpansionEnergy(V(2,3));await Draw(V(2,3));break;
            case "RIN-U21":foreach(var enemy in GameplayChoice.Enemies(d,true)){await Debuffs(enemy,V(1,2),true);await Damage(enemy,V(4,6)*ContractRuntime.DebuffTypes(enemy,true));if(d.Finished)break;}break;
            case "RIN-U23":await d.ExpansionEnergy(V(3,4));await Draw(V(2,3));d.BorrowFutureEnergy();break;
            case "RIN-R09":await Damage(d.PlayTarget(c),V(20,26)+V(12,15)*ContractRuntime.DebuffTypes(d.PlayTarget(c)!),unblockable:true);break;
            case "RIN-R10":d.GainJewel(V(2,3));await Draw(3);break;
            case "RIN-R13":foreach(var enemy in GameplayChoice.Enemies(d,true)){await Damage(enemy,V(20,35)+V(8,10)*p.AdditionalMana+V(25,30)*p.DirectJewels);if(d.Finished)break;}break;
            case "ARC-C17":d.GainMana(V(2,3));await Draw(V(1,2));break;
            case "ARC-C18":await Block(V(6,9));await Draw(1);break;
            case "ARC-C19":await Damage(d.PlayTarget(c),V(4,5),RewardRules.Arms(d).Length>0?4:3);break;
            case "ARC-C20":if(play.PlayIndex==0)foreach(var arm in p.Arms){if(!d.HasArcherSpace())break;await CardPileCmd.Add(arm,d.Archer.Hand,skipVisuals:!d.Archer.IsActive);}d.GainMana(V(1,2));break;
            case "ARC-C21":bool low=d.Archer.Creature.CurrentHp<d.Rin.Creature.CurrentHp;await Block(V(9,13));if(low){await d.ExpansionEnergy(V(1,2));await Draw(V(1,2));}break;
            case "ARC-U20":var target=d.PlayTarget(c);bool weak=target?.GetPowerAmount<WeakPower>()>0;await Debuffs(target,V(2,3),false);if(weak)await d.ExpansionEnergy(V(2,3));break;
            case "ARC-U21":if(p.Debuffs.Length==0)await Block(V(8,12));else if(await Transfer(d.Rin)>0){await d.ExpansionEnergy(V(2,3));await Draw(V(1,2));}break;
            case "ARC-U22":if(play.PlayIndex==0)await CreatureCmd.Damage(ctx,d.Rin.Creature,V(6,4),ValueProp.Unpowered|ValueProp.Unblockable,null,c);await d.ExpansionEnergy(V(2,3));await Draw(V(2,3));break;
            case "ARC-U23":if(play.PlayIndex==0)foreach(var arm in p.Arms){arm.CombatFree=true;arm.EnergyCost.SetThisCombat(0);}await Draw(V(1,2));break;
            case "ARC-R10":
                int burst=d.Bound(V(20,28)+V(10,15)*p.ArmUsesSnapshot);
                if(!r.MaterialConsumed){if(p.Arm==null||!d.Archer.Hand.Cards.Contains(p.Arm))return true;r.MaterialConsumed=true;p.Arm.ExhaustSource=c.SourceCardId;await CardPileCmd.Add(p.Arm,d.Archer.Exhaust,skipVisuals:!d.Archer.IsActive);d.ArmResolved(p.Arm,c.SourceCardId);r.ForgeEvent=true;}
                foreach(var enemy in GameplayChoice.Enemies(d,true)){await Damage(enemy,burst);if(d.Finished)break;}break;
            case "ARC-R12":await Damage(d.PlayTarget(c),d.Bound(V(18,24)+V(12,16)*p.ArmUsesSnapshot+8*p.AdditionalMana));break;
            default:return false;
        }
        return true;
    }
}
