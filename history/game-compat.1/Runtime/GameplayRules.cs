using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Entities.Powers;
namespace RinArcherCore;
public static class GameplayRules
{
    public static string Availability(ContractRuntime d,StarterCard c,bool auto=false)
    {
        if(d.Active.CharacterId!=c.OwnerCharacterId)return FsnLoc.Text("UI_54C271A6F462");
        if(!auto&&!d.CanSpendMana(d.EffectiveManaCost(c.OwnerCharacterId,c.PrintedManaCost,c.ModifiedManaCost)))return FsnLoc.Text("UI_AF6E94512963");
        int exchange=c.IsUpgraded?2:3;
        return c.SourceCardId switch
        {
            "RIN_S_MANA_SUPPLY" when d.Mana==d.MaxMana&&d.Mana<exchange=>FsnLoc.Text("UI_B3848CE13C6B"),
            "RIN_S_REINFORCE_PROJECTION" when d.PendingReinforcement.Active||d.SelfReinforcement>0=>FsnLoc.Text("UI_DCF519661ED9"),
            "RIN-U10" when d.U10Charges>0=>FsnLoc.Text("UI_5BD87A6A3410"),
            "RIN-U10" or "RIN-U14" or "RIN-R07" when d.Jewel<1=>FsnLoc.Text("UI_D229C9250F45"),
            "RIN-U15" when d.U15Pending=>FsnLoc.Text("UI_D1A7F98A495E"),
            "RIN-C15" when !d.CanTune(d.Rin,c)&&!d.CanTune(d.Archer,c)=>FsnLoc.Text("UI_016A4D303384"),
            "RIN-U20" when d.Archer.Creature.CurrentHp<=(c.IsUpgraded?4:6)=>FsnLoc.Text("UI_5B0F8052068B"),
            "ARC-U22" when d.Rin.Creature.CurrentHp<=(c.IsUpgraded?4:6)=>FsnLoc.Text("UI_307418B8E994"),
            "ARC-U23" or "ARC-R10" when RewardRules.Arms(d).Length==0=>FsnLoc.Text("UI_420A67D1BAEC"),
            "ARC-C15" when d.TuningCards(d.Archer,c).Length==0=>FsnLoc.Text("UI_30E974FE979B"),
            "ARC-C07" or "ARC-C11" when RewardRules.Arms(d).Length==0=>FsnLoc.Text("UI_63C147159D3D"),
            "ARC-U02" or "ARC-R03" when RewardRules.Arms(d,true).Length==0=>FsnLoc.Text("UI_9A2A80E3889A"),
            "ARC_S_TRACE" or "ARC-C06" or "ARC-U14" when !d.HasArcherSpace(c)=>FsnLoc.Text("UI_D78BF118B3F2"),
            "ARC-U14" when Arsenal.Ids.All(d.ProjectedArmsResolvedThisCombat.Contains)&&d.Mana<1=>FsnLoc.Text("UI_342D1DEBC278"),
            _=>""
        };
    }
    public static bool ValidPlan(ContractRuntime d,StarterCard c,GameplayPlayPlan p,bool auto=false)
    {
        if(Availability(d,c,auto).Length>0)return false;
        int cost=(auto?0:d.EffectiveManaCost(c.OwnerCharacterId,c.PrintedManaCost,c.ModifiedManaCost))+p.AdditionalMana;
        if(d.Mana<cost||d.Jewel<p.DirectJewels+(p.Boost?1:0))return false;
        if(p.Arm!=null&&!d.Archer.Hand.Cards.Contains(p.Arm))return false;
        if(p.Arms.Any(a=>a.Owner!=d.Player||a.OwnerCharacterId!="CHAR_ARCHER"||!(c.SourceCardId=="ARC-C20"?d.Archer.Exhaust:d.Archer.Hand).Cards.Contains(a)))return false;
        if(p.Debuffs.Any(s=>!d.Transferable(c.OwnerCharacterId=="CHAR_RIN"?d.Rin:d.Archer,c.OwnerCharacterId=="CHAR_RIN"?d.Archer:d.Rin).Contains(s)))return false;
        if(p.Target!=null&&!p.Target.IsAlive)return false;
        if(p.Cards.Length>0)
        {
            if(p.Member==null)return false;var member=d.Member(p.Member);
            if(c.SourceCardId!="ARC-C15"&&!d.CanTune(member,c))return false;
            if(p.Cards.Any(card=>!d.TuningCards(member,c).Contains(card)))return false;
        }
        return true;
    }
    public static async Task Play(PlayerChoiceContext ctx,CardPlay play,ContractRuntime d,StarterCard c)
    {
        var r=d.Receipt(c);var p=r.Plan;bool up=c.IsUpgraded;int V(int n,int u)=>up?u:n;
        Task Block(CharacterRuntime member,int n){d.SetAlphaTarget(c,member.CharacterId);return CreatureCmd.GainBlock(member.Creature,d.BlockAmount(c,member,n),ValueProp.Move,play);}
        async Task Damage(int n,int hits=1)
        {
            var target=d.PlayTarget(c);if(target==null||!target.IsAlive)return;
            var profile=d.DamageProfile(c,n,hits);d.SetAlphaTarget(c,target.CombatId.ToString()!);
            for(int i=0;i<hits&&!d.Finished&&target.IsAlive;i++)await Targeting.Damage(ctx,d,ContractTarget.ANY_CONTRACT_MEMBER,profile[i],d.Member(c.OwnerCharacterId).Creature,c,true,i+1,target);
        }
        async Task Weak(int n){var target=d.PlayTarget(c);if(target?.IsAlive==true)await PowerCmd.Apply<WeakPower>(ctx,target,n,d.Rin.Creature,c);}
        async Task Tuning(){if(play.PlayIndex==0&&p.Member!=null&&p.Cards.Length>0)await d.Tune(ctx,d.Member(p.Member),p.Cards);}
        async Task<bool> ConsumeArm()
        {
            if(r.MaterialConsumed)return true;
            if(p.Arm==null||!d.Archer.Hand.Cards.Contains(p.Arm))return false;
            r.MaterialConsumed=true;p.Arm.ExhaustSource=c.SourceCardId;
            await CardPileCmd.Add(p.Arm,d.Archer.Exhaust,skipVisuals:!d.Archer.IsActive);return true;
        }
        // Self/member effects need no enemy lookup. Damaging effects resolve their prepared target below.
        var target=p.Target??c.CurrentTarget;
        switch(c.SourceCardId)
        {
            case "RIN_S_GANDR":await Damage(r.JewelBoostUsed?V(9,12):V(6,8));if(r.JewelBoostUsed)await Weak(1);break;
            case "RIN_S_REINFORCEMENT":await Block(d.Rin,r.JewelBoostUsed?V(9,11):V(5,7));break;
            case "RIN_S_JEWEL_PREPARATION":d.GainJewel(1);await d.DrawMember(ctx,d.Rin,1);await Block(d.Rin,V(2,5));break;
            case "RIN_S_JEWEL_RELEASE":await Damage(r.JewelBoostUsed?V(14,18):V(6,8));break;
            case "RIN_S_MANA_SUPPLY":
                if(p.Selection=="GAIN_MANA")d.GainMana(V(2,3));
                else if(p.Selection=="MANA_TO_ENERGY")await d.ExpansionEnergy(1);break;
            case "RIN_S_REINFORCE_PROJECTION":if(play.PlayIndex==0){if(p.Selection=="SELF")d.SelfReinforcement=V(8,12);else d.ApplyReinforcement(r.JewelBoostUsed);}break;
            case "ARC_S_BOW_SHOT":await Damage(V(7,9));break;
            case "ARC_S_CLOSE_COMBAT":await Damage(V(3,4),2);break;
            case "ARC_S_DEFLECT":await Block(d.Archer,V(5,7));break;
            case "ARC_S_COVER":if(p.Selection=="SELF"){await Block(d.Archer,V(10,14));await d.DrawArcher(ctx,1);}else{await Block(d.Rin,V(7,10));await Tuning();}break;
            case "ARC_S_TRACE":if(p.ArmId!=null&&await d.GenerateArm(ctx,p.ArmId,c.SourceCardId,up)!=null){await d.DrawArcher(ctx,1);d.GainMana(V(1,2));}break;
            case "RIN-C04":bool threat=Targeting.IsRinTargetedByAttackIntent(d);await Damage(V(7,9));if(threat&&!d.Finished)await Block(d.Rin,V(4,6));break;
            case "RIN-C05":if(d.Jewel<d.JewelCap){d.GainJewel(1);await Block(d.Rin,V(3,5));}else await Block(d.Rin,V(8,11));break;
            case "RIN-C08":await Block(d.Archer,V(7,10));await Tuning();break;
            case "RIN-C10":await Damage(V(3,4));await Weak(V(2,3));break;
            case "RIN-C12":if(p.Selection=="DEFENSE")await Block(d.Rin,V(8,11));else{d.GainMana(V(2,3));await d.DrawMember(ctx,d.Member(p.Member!),V(1,2));}break;
            case "RIN-C13":if(d.Jewel<d.JewelCap){d.GainJewel(1);if(up)await d.DrawMember(ctx,d.Rin,1);}else await Block(d.Rin,V(4,6));break;
            case "RIN-C15":await Tuning();break;
            case "RIN-C16":var member=d.Member(p.Member!);await Block(member,V(6,9));if(!member.IsActive)await d.DrawMember(ctx,member,1);break;
            case "RIN-U01":bool weak=target?.Powers.OfType<WeakPower>().Any()==true;await Damage(r.JewelBoostUsed?V(18,22):V(8,10));if(weak&&target?.IsAlive==true)await PowerCmd.Apply<VulnerablePower>(ctx,target,1,d.Rin.Creature,c);break;
            case "RIN-U04":threat=Targeting.IsRinTargetedByAttackIntent(d);await Damage(V(3,4),3);if(threat&&!d.Finished)await Block(d.Rin,V(4,6));break;
            case "RIN-U06":if(p.Field!=null)d.SuppressField(p.Field);else await Weak(V(2,3));if(!d.Finished)await Block(d.Rin,V(4,7));break;
            case "RIN-U10":if(play.PlayIndex==0)d.ActivateAllProjection(c);break;
            case "RIN-U14":if(p.Selection=="ATTACK")await Damage(V(14,18));else if(p.Selection=="DEFENSE")await Block(d.Member(p.Member!),V(14,18));else await Tuning();break;
            case "RIN-U15":if(play.PlayIndex==0)d.U15Pending=true;break;
            case "RIN-U16":member=d.Member(p.Member!);await Block(member,V(12,15));await Block(member==d.Rin?d.Archer:d.Rin,V(7,10));break;
            case "RIN-R07":await Damage(V(12,16)+V(10,12)*p.DirectJewels+V(4,5)*p.AdditionalMana);break;
            case "ARC-C03":await Damage(d.ArmActivityThisTurn?V(11,14):V(7,9));break;
            case "ARC-C06":if(p.ArmId!=null&&await d.GenerateArm(ctx,p.ArmId,c.SourceCardId,zeroManaThisTurn:true)!=null&&up)await d.DrawArcher(ctx,1);break;
            case "ARC-C07":if(p.Arm==null)break;if(play.PlayIndex==0){int discount=Math.Min(1,p.Arm.ModifiedManaCost);if(up)p.Arm.ManaDiscount+=discount;else{p.Arm.TemporaryManaDiscount+=discount;p.Arm.TemporaryDiscountTurn=d.Turn;}}await d.DrawArcher(ctx,2);break;
            case "ARC-C10":await Block(d.Archer,V(7,9)+(p.AdditionalMana>0?V(5,7):0));if(p.AdditionalMana>0)await Block(d.Rin,V(3,4));break;
            case "ARC-C11":if(await ConsumeArm()){await Block(d.Archer,V(5,8));await d.DrawArcher(ctx,1);}break;
            case "ARC-C14":await Block(d.Archer,V(5,8));d.GiveGuardMaster();break;
            case "ARC-C15":if(play.PlayIndex==0)await d.DiscardMember(ctx,d.Archer,p.Cards,V(2,3));else await d.DrawArcher(ctx,V(2,3));break;
            case "ARC-C16":await Block(d.Archer,V(6,9));await d.C16(ctx,c);break;
            case "ARC-U01":await Damage(V(7,9)+V(5,6)*Math.Min(3,d.ProjectedArmsResolvedThisCombat.Count));break;
            case "ARC-U02":if(await ConsumeArm()){await Damage(p.Arm!.Reinforced?V(23,26):V(18,21));if(!r.ForgeEvent){d.ArmResolved(p.Arm,c.SourceCardId);r.ForgeEvent=true;}}break;
            case "ARC-U05":bool debuff=target?.Powers.Any(power=>power.Type==PowerType.Debuff)==true;await Damage(V(8,11)+(debuff?V(5,6):0));if(debuff&&!d.Finished)await d.DrawArcher(ctx,1);break;
            case "ARC-U14":if(p.ArmId!=null)await d.GenerateArm(ctx,p.ArmId,c.SourceCardId,up,energyOverrideThisTurn:0);break;
            case "ARC-U15":await Damage(V(5,6),target?.Powers.OfType<WeakPower>().Any()==true?3:2);break;
            case "ARC-U16":member=d.Member(p.Member!);await Block(member,V(12,16));await Tuning();break;
            case "ARC-R03":if(await ConsumeArm()){if(p.Arm!.ArmId=="ARM_KANSHOU_BAKUYA")await Damage(V(10,12),4);else{await Damage(V(36,44));if(target?.IsAlive==true)await PowerCmd.Apply<VulnerablePower>(ctx,target,2,d.Archer.Creature,c);}if(!r.ForgeEvent){d.ArmResolved(p.Arm,c.SourceCardId);r.ForgeEvent=true;}}break;
            case "ARC-R07":await Damage(V(5,6),d.RinSuccessful?5:4);break;
            default:if(c is AlphaRewardCard power&&c.Type==CardType.Power){await d.ActivatePower(power,play,ctx);if(c.SourceCardId=="RIN-R11"&&up)d.GainJewel(1);}else if(!await ExpansionRules.Play(ctx,play,d,c))throw new InvalidOperationException("Unimplemented gameplay card "+c.SourceCardId);break;
        }
    }
}
