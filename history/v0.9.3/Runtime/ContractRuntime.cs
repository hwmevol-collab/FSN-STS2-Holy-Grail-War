using System.Runtime.CompilerServices;
using System.Text.Json;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
public sealed partial class ContractRuntime
{
    static readonly ConditionalWeakTable<Player,ContractRuntime> States=new();
    public const string ContractId="CONTRACT_RIN_ARCHER_ALPHA";
    public Player Player{get;}
    public CombatState Combat{get;}
    public CharacterRuntime Rin{get;}
    public CharacterRuntime Archer{get;}
    public CharacterRuntime Active{get;private set;}
    public CharacterRuntime Reserve=>Active==Rin?Archer:Rin;
    public QaEnemyContract? Enemy{get;}
    public string Seed=>Player.RunState.Rng.StringSeed;
    public int Energy=>Player.PlayerCombatState!.Energy;
    public int MaxEnergy=>GenericCompatibility.Enabled(Player)?(int)Hook.ModifyMaxEnergy(Combat,Player,3):3;
    public int Mana{get;private set;}=3;
    public int MaxMana=>10;
    public int Jewel{get=>Rin.CharacterResources.GetValueOrDefault("JEWEL",1);private set=>Rin.CharacterResources["JEWEL"]=value;}
    public int JewelCap=>3;
    public int Turn{get;private set;}
    public bool FreeSwitchAvailable{get;private set;}=true;
    public bool IndependentActionAvailable{get;private set;}=true;
    public bool StartingSelected{get;private set;}
    public bool Defeated{get;private set;}
    public bool Finished{get;private set;}
    public bool Switching{get;private set;}
    public int StartStatusesAppliedTurn{get;set;}=-1;
    public int CommandSpellCount=>ContractSave.Get(Player).CommandSpellCount;
    public bool CommandSpellEnabled=>ContractSave.Get(Player).CommandSpellGameplayEnabled;
    int rinHpStart,archerHpStart,rinDeckSizeStart,archerDeckSizeStart;
    public readonly List<string> ContractStatuses=[];
    public readonly List<FieldStatus> FieldStatuses=[];
    public PendingProjectionReinforcement PendingReinforcement{get;}=new();
    public int GuardCharges{get;private set;}
    public readonly List<(string Event,object? Detail)> Telemetry=[];
    int generatedArmCount;
    public readonly Dictionary<string,bool> CombatFlags=[];
    readonly Dictionary<CardModel,string> InstanceIds=new(ReferenceEqualityComparer.Instance);
    int supplyAppliedTurn=-1;
    bool deferredActiveOpening;
    public void DeferActiveOpeningForNativeDraw()
    {
        if(Turn!=0||!StartingSelected)throw new InvalidOperationException("Opening hand deferral must precede combat triggers");
        // A starting bank switch can already have created native card holders.
        // Remove those views before the native draw recreates them once.
        if(!TestMode.IsOn&&NPlayerHand.Instance is {} hand)
            foreach(var card in Active.Hand.Cards.ToArray())if(hand.GetCard(card)!=null)hand.Remove(card);
        foreach(var card in Active.Hand.Cards.Reverse().ToArray())
        {Active.Hand.RemoveInternal(card,true);Active.DrawPile.AddInternal(card,0,true);}
        deferredActiveOpening=true;
    }
    public static ContractRuntime? For(Player? p)=>p!=null&&States.TryGetValue(p,out var d)?d:null;
    public static ContractRuntime? For(Creature c)=>CombatManager.Instance.DebugOnlyGetState()?.Players.Select(For).OfType<ContractRuntime>().FirstOrDefault(d=>d.Rin.Creature==c||d.Archer.Creature==c);
    ContractRuntime(Player player,CombatState combat,Creature archer)
    {
        Player=player;Combat=combat;Rin=new(this,"CHAR_RIN","MASTER",player.Creature);Archer=new(this,"CHAR_ARCHER","SERVANT",archer);Active=Rin;
        if(combat.Enemies.Any(c=>c.Monster is QaMaster or QaFieldMaster))Enemy=new QaEnemyContract(this);
        if(Enemy?.IsField==true)FieldStatuses.Add(new(){FieldId="FIELD_PRESSURE",Owner="ENEMY_CONTRACT",Duration=-1});
    }
    public static async Task<ContractRuntime> Initialize(Player p,CombatState combat,PlayerChoiceContext ctx,bool addVisuals=true)
    {
        if(p.Character is not RinContractCharacter)throw new InvalidOperationException("Not a Rin/Archer contract");
        States.Remove(p);
        var archer=combat.CreateCreature(ModelDb.Monster<ArcherBody>().ToMutable(),CombatSide.Player,null);
        // Do not set PetOwner: vanilla pet damage borrows the owner's block, violating independent block.
        combat.AddCreature(archer);
        if(addVisuals&&!TestMode.IsOn)
        {
            CombatManager.Instance.AddCreature(archer);
            if(MegaCrit.Sts2.Core.Nodes.Rooms.NCombatRoom.Instance is {} room)
            {
                room.AddCreature(archer);
                var archerNode=room.GetCreatureNode(archer)??throw new InvalidOperationException("Archer visual missing");var rinNode=room.GetCreatureNode(p.Creature)??throw new InvalidOperationException("Rin visual missing");
                archerNode.Reparent(rinNode.GetParent());archerNode.GlobalPosition=rinNode.GlobalPosition+new Vector2(190,0);
            }
        }
        var d=new ContractRuntime(p,combat,archer);States.Add(p,d);
        var saved=ContractSave.Get(p);archer.SetMaxHpInternal(saved.ArcherMaxHp);archer.SetCurrentHpInternal(saved.ArcherHp);
        ContractSave.EnsureDecks(p);
        AlphaQaSession.Inject(d);
        foreach(var f in new[]{d.Rin,d.Archer})
        {
            foreach(var c in f.Deck.Cards.OfType<StarterCard>())if(string.IsNullOrEmpty(c.InstanceId))c.InstanceId=$"permanent:{f.CharacterId}:{Array.IndexOf(f.Deck.Cards.ToArray(),c)}";
            foreach(var type in d.PileTypes)f.Pile(type).Clear(true);
            int i=0;
            foreach(var c in f.Deck.Cards)
            {
                var clone=combat.CloneCard(c);clone.DeckVersion=c;string instance=$"{d.Seed}:{f.CharacterId}:{i++}";
                if(clone is StarterCard owned)owned.InstanceId=instance;else GenericCombatCardOwnership.BindPermanentClone(clone,f.CharacterId,instance);
                d.InstanceIds.Add(clone,instance);f.DrawPile.AddInternal(clone,silent:true);
            }
            f.DrawPile.RandomizeOrderInternal(p,p.RunState.Rng.Shuffle,combat);
            foreach(var c in f.DrawPile.Cards.Take(5).ToArray()){f.DrawPile.RemoveInternal(c,true);f.Hand.AddInternal(c,silent:true);}
            foreach(var type in d.PileTypes){f.Pile(type).InvokeContentsChanged();f.Pile(type).InvokeCardAddFinished();}
        }
        p.PlayerCombatState!.Energy=3;
        d.rinHpStart=d.Rin.Creature.CurrentHp;d.archerHpStart=archer.CurrentHp;d.rinDeckSizeStart=d.Rin.Deck.Cards.Count;d.archerDeckSizeStart=d.Archer.Deck.Cards.Count;
        ContractSave.Get(p).CombatSummary=new(){RunSeed=d.Seed,Act=p.RunState.CurrentActIndex,RoomIndex=p.RunState.TotalFloor,RinHpStart=d.rinHpStart,ArcherHpStart=d.archerHpStart,RinDeckSizeStart=d.rinDeckSizeStart,ArcherDeckSizeStart=d.archerDeckSizeStart};
        ContractSave.Sync(p);
        ContractSave.Log(p,"ROOM_ENTERED",new{roomId=ContractSave.RoomKey(p),roomType=p.RunState.CurrentRoom?.RoomType.ToString(),act=p.RunState.CurrentActIndex,roomIndex=p.RunState.TotalFloor});
        ContractSave.Log(p,"COMBAT_STARTED",new{rinHp=d.rinHpStart,archerHp=d.archerHpStart,rinDeckSize=d.rinDeckSizeStart,archerDeckSize=d.archerDeckSizeStart,manaInitial=d.Mana,jewelInitial=d.Jewel});
        d.Log("COMBAT_START",new{openingRin=d.Ids(d.Rin.Hand),openingArcher=d.Ids(d.Archer.Hand)});
        d.AssertInvariants();return await Task.FromResult(d);
    }
    public readonly PileType[] PileTypes=[PileType.Hand,PileType.Draw,PileType.Discard,PileType.Exhaust,PileType.Play];
    public void SelectStartingActive(string id)
    {
        if(StartingSelected)throw new InvalidOperationException("Starting Active already chosen");
        if(id!="CHAR_RIN"&&id!="CHAR_ARCHER")throw new ArgumentException("Unknown starting member");
        if(id=="CHAR_ARCHER")SwapPiles();
        StartingSelected=true;Log("STARTING_ACTIVE_SELECTED",new{character=id});AssertInvariants();
    }
    public void BeginSharedTurn()
    {
        if(!StartingSelected||Finished)return;
        Turn++;
        BeginAlphaTurn();
        GuardCharges=0;
        foreach(var arm in PileTypes.SelectMany(t=>Archer.Pile(t).Cards).OfType<ProjectedArm>())arm.ExpireTemporary(Turn);
        foreach(var field in FieldStatuses)field.BeginTurn(this);
        QaTargetTag.RefreshNumbers(this);
        if(!GenericCompatibility.Enabled(Player)||Turn>1){Rin.Creature.LoseBlockInternal(Rin.Creature.Block);Archer.Creature.LoseBlockInternal(Archer.Creature.Block);}
        if(E2CCustomAdapters.ResetEnergy(this))Player.PlayerCombatState!.Energy=MaxEnergy;
        else Player.PlayerCombatState!.Energy+=MaxEnergy;
        FreeSwitchAvailable=true;IndependentActionAvailable=true;
        ApplyNextTurnEnergy();
        ApplyEnergyDebt();
        Log("PLAYER_TURN_START",new{stage="block_clear_energy_switch_independent_ready"});
    }
    public async Task SetupActiveHand(PlayerChoiceContext ctx)
    {
        if(supplyAppliedTurn==Turn)throw new InvalidOperationException("Duplicate player turn setup");
        if(Active==Rin){GainMana(1);Log("NORMAL_MANA_SUPPLY",new{amount=1});if(AlphaPowers.ContainsKey("RIN-U12")){GainMana(1);Log("RIN_START_TURN_MANA",new{stage="AFTER_NORMAL_SUPPLY"});}}supplyAppliedTurn=Turn;
        if(GenericCompatibility.Enabled(Player))
        {
            decimal draw=MegaCrit.Sts2.Core.Hooks.Hook.ModifyHandDraw(Combat,Player,5,out var modifiers);
            await MegaCrit.Sts2.Core.Hooks.Hook.AfterModifyingHandDraw(Combat,modifiers);
            if(Turn==1&&deferredActiveOpening)
            {
                var bottom=Active.DrawPile.Cards.Where(c=>c.Enchantment?.ShouldStartAtBottomOfDrawPile??false).ToArray();
                foreach(var card in bottom)Active.DrawPile.MoveToBottomInternal(card);
                var innate=Active.DrawPile.Cards.Where(c=>c.Keywords.Contains(CardKeyword.Innate)).Except(bottom).ToArray();
                foreach(var card in innate)Active.DrawPile.MoveToTopInternal(card);
                draw=Math.Min(CardPile.MaxCardsInHand,Math.Max(draw,innate.Length));
            }
            decimal amount=Turn==1&&!deferredActiveOpening?Math.Max(0,draw-5):draw;
            if(amount>0)await CardPileCmd.Draw(ctx,amount,Player,fromHandDraw:true);
        }
        else if(Turn>1)await CardPileCmd.Draw(ctx,5,Player,fromHandDraw:true);
        if(!TestMode.IsOn&&Turn==1)RefreshNativeHand();
        Log("PLAYER_ACTION",new{openingHandReused=Turn==1});AssertInvariants();
    }
    public async Task<bool> Switch()
    {
        Log("SWITCH_REQUEST",new{from=Active.CharacterId,to=Reserve.CharacterId});
        if(!StartingSelected||Finished||Defeated||Switching||!FreeSwitchAvailable||Player.PlayerCombatState?.Phase!=PlayerTurnPhase.Play
            ||Combat.CurrentSide!=CombatSide.Player||!Active.Pile(PileType.Play).IsEmpty){Log("SWITCH_REJECTED",new{freeSwitch=FreeSwitchAvailable});return false;}
        Switching=true;
        try
        {
            var outgoing=Active;var incoming=Reserve;var before=Ids(outgoing.Hand);var incomingBefore=Ids(incoming.Hand);
            foreach(var arm in outgoing.Hand.Cards.OfType<ProjectedArm>())Log("BANKED",new{instanceId=arm.InstanceId,armId=arm.ArmId,sameInstance=true});
            Log("BEFORE_SWITCH_OUT",new{from=outgoing.CharacterId,to=incoming.CharacterId});
            NPlayerHand.Instance?.CancelAllCardPlay();
            Log("SWITCH_OUT");SwapPiles();Log("ACTIVE_POINTER_SWAP");Log("SWITCH_IN");
            if(!before.SequenceEqual(Ids(outgoing.Hand))||!incomingBefore.SequenceEqual(Ids(incoming.Hand)))throw new InvalidOperationException("SWITCH instance identity violation");
            FreeSwitchAvailable=false;Log("AFTER_SWITCH_IN");Targeting.Refresh(this);Log("TARGETING_REFRESH");
            foreach(var arm in Active.Hand.Cards.OfType<ProjectedArm>())Log("ARM_RESTORED",new{instanceId=arm.InstanceId,armId=arm.ArmId,sameInstance=true});
            Log("SWITCH",new{from=outgoing.CharacterId,to=Active.CharacterId,handInstanceIdsBefore=before,handInstanceIdsAfter=Ids(outgoing.Hand),incomingBefore,incomingAfter=Ids(Active.Hand)});
            AssertInvariants();Log("RETURN_PLAYER_CONTROL");return await Task.FromResult(true);
        }
        finally{Switching=false;}
    }
    void SwapPiles()
    {
        if(!TestMode.IsOn&&NPlayerHand.Instance is {} ui)foreach(var card in Active.Hand.Cards.ToArray())if(ui.GetCard(card)!=null)ui.Remove(card);
        foreach(var type in PileTypes)
        {
            var native=CardPile.Get(type,Player)!;var bank=CardBanks.Bank(type,Player);
            var a=native.Cards.ToArray();var b=bank.Cards.ToArray();
            foreach(var c in a)native.RemoveInternal(c,true);foreach(var c in b)bank.RemoveInternal(c);
            foreach(var c in a)bank.AddInternal(c);foreach(var c in b)native.AddInternal(c,silent:true);
            bank.InvokeContentsChanged();native.InvokeContentsChanged();bank.InvokeCardAddFinished();native.InvokeCardAddFinished();
        }
        Active=Reserve;
        if(!TestMode.IsOn)RefreshNativeHand();
    }
    public void RefreshNativeHand()
    {
        if(NPlayerHand.Instance is not {} ui)return;
        foreach(var card in Player.PlayerCombatState!.Hand.Cards){if(ui.GetCard(card)!=null)continue;var node=NCard.Create(card);if(node!=null)ui.Add(node);}
        CoreHud.RefreshReserve(this);
    }
    public string[] Ids(CardPile pile)=>pile.Cards.Select(c=>c is StarterCard owned?owned.InstanceId:GenericCombatCardOwnership.Get(c)?.InstanceId??throw new InvalidOperationException("Unbound combat instance")).ToArray();
    public CharacterRuntime Member(string id)=>id=="CHAR_RIN"?Rin:id=="CHAR_ARCHER"?Archer:throw new ArgumentException("Unknown owner");
    public void GainMana(int n){if(n<0)throw new ArgumentOutOfRangeException(nameof(n));Mana=Math.Min(10,Mana+n);Log("MANA_GAIN",new{amount=n});}
    public bool CanSpendMana(int n)=>n>=0&&Mana>=n;
    public bool SpendMana(int n){if(!CanSpendMana(n))return false;Mana-=n;Log("MANA_SPEND",new{amount=n});return true;}
    public void GainJewel(int n){if(n<0)throw new ArgumentOutOfRangeException(nameof(n));Jewel=Math.Min(3,Jewel+n);Log("JEWEL_GAIN",new{amount=n});}
    public bool SpendJewel(bool confirmed){if(!confirmed||Jewel<1)return false;Jewel--;Log("JEWEL_SPEND",new{confirmed});return true;}
    public int EffectiveManaCost(string owner,int printed,int modified)=>IndependentActionAvailable&&owner=="CHAR_ARCHER"&&printed==1&&modified==1?0:Math.Max(0,modified);
    public bool CommitManaCost(string owner,int printed,int modified)
    {
        int effective=EffectiveManaCost(owner,printed,modified);if(!SpendMana(effective))return false;
        if(effective==0&&modified==1&&printed==1&&owner=="CHAR_ARCHER"&&IndependentActionAvailable){IndependentActionAvailable=false;Log("INDEPENDENT_ACTION",new{printed,modified,effective});}return true;
    }
    public async Task EndHandForTest(PlayerChoiceContext ctx)
    {
        foreach(var c in Active.Hand.Cards.Where(c=>!c.Keywords.Contains(CardKeyword.Retain)).ToArray())await CardPileCmd.Add(c,Active.Discard,skipVisuals:true);
    }
    public async Task CheckLethal(PlayerChoiceContext ctx)
    {
        if(Finished)return;
        if(Rin.Creature.IsDead||Archer.Creature.IsDead){Defeated=true;Finished=true;Log("CONTRACT_DEFEAT");ContractSave.Log(Player,"RUN_DEFEAT",new{deadMember=Rin.Creature.IsDead?"CHAR_RIN":"CHAR_ARCHER"});if(!TestMode.IsOn&&Rin.Creature.IsAlive)await CreatureCmd.Kill(Rin.Creature,true);}
        else if(Enemy is {} enemy&&(enemy.Master.IsDead||enemy.Servant.IsDead)){Finished=true;Log("ENEMY_CONTRACT_DEFEAT",new{master=enemy.Master.CurrentHp,servant=enemy.Servant.CurrentHp});if(!TestMode.IsOn){var survivor=enemy.Master.IsAlive?enemy.Master:enemy.Servant;await CreatureCmd.Escape(survivor);await CombatManager.Instance.CheckWinCondition();}}
        if(Finished)Jewel=0;
    }
    public void Finish()
    {
        if(!Finished)Log("COMBAT_END");Finished=true;Jewel=0;ContractSave.Store(this);ContractSave.Sync(Player);EmitAlphaSummary();
        ContractSave.Log(Player,"COMBAT_ENDED",new{rinHp=Rin.Creature.CurrentHp,archerHp=Archer.Creature.CurrentHp,victory=!Defeated});
        var summary=ContractSave.Get(Player).CombatSummary;if(summary!=null){summary.RinHpEnd=Rin.Creature.CurrentHp;summary.ArcherHpEnd=Archer.Creature.CurrentHp;summary.RinDeckSizeEnd=Rin.Deck.Cards.Count;summary.ArcherDeckSizeEnd=Archer.Deck.Cards.Count;ContractSave.Log(Player,"COMBAT_SUMMARY_RUN",summary);}
        if(D1Run.IsQa(Player)||RunEconomy.Enabled(Player)){ClearEncounterState();CoreHud.DetachCombat();}
    }
    public void ClearEncounterState()
    {
        ClearGameplayState();
        foreach(var f in new[]{Rin,Archer}){foreach(var type in PileTypes)f.Pile(type).Clear(true);f.Creature.LoseBlockInternal(f.Creature.Block);f.Creature.RemoveAllPowersInternalExcept();f.CharacterResources.Clear();f.TemporaryFlags.Clear();}
        Mana=0;Jewel=0;PendingReinforcement.Active=false;PendingReinforcement.ManaDiscount=0;ProjectedArmsResolvedThisCombat.Clear();FieldStatuses.Clear();ContractStatuses.Clear();GuardCharges=0;CombatFlags.Clear();IndependentActionAvailable=false;FreeSwitchAvailable=false;ReinforceAllThisTurn=false;FreeJewelBoostUsed=false;ProjectedExhaustUsed=false;AlphaPowers.Clear();
    }
    public bool ApplyReinforcement(bool jewelBoost)
    {
        if(PendingReinforcement.Active||SelfReinforcement>0){Log("PENDING_REINFORCEMENT_ALREADY_ACTIVE");return false;}
        PendingReinforcement.Active=true;PendingReinforcement.ManaDiscount=jewelBoost?1:0;
        Log("REINFORCEMENT_PENDING",new{jewelBoost,manaDiscount=PendingReinforcement.ManaDiscount});return true;
    }
    public async Task<ProjectedArm?> GenerateArm(PlayerChoiceContext ctx,string armId,string sourceCardId,bool traceUpgrade=false,bool zeroManaThisTurn=false,int? energyOverrideThisTurn=null)
    {
        if(Finished||!HasArcherSpace()){Log("PROJECTION_UNAVAILABLE",new{reason=FsnLoc.Text("UI_827ABD4D31EE"),sourceCardId});return null;}
        var arm=(ProjectedArm)Combat.CreateCard(Arsenal.Get(armId),Player);
        arm.InstanceId=$"{Seed}:ARM:{++generatedArmCount}";arm.GeneratedBy=sourceCardId;
        bool starter=PendingReinforcement.Active;
        arm.Reinforced=starter||U10Charges>0;arm.ReinforcedByAllProjection=!starter&&U10Charges>0;arm.ManaDiscount=starter?PendingReinforcement.ManaDiscount:0;
        arm.TemporaryManaDiscount=traceUpgrade?1:0;arm.TemporaryDiscountTurn=Turn;
        arm.TemporaryZeroMana=zeroManaThisTurn;arm.TemporaryEnergyOverride=energyOverrideThisTurn;
        if(energyOverrideThisTurn is int overrideCost)arm.EnergyCost.SetThisTurn(overrideCost);
        InstanceIds.Add(arm,arm.InstanceId);
        await CardPileCmd.Add(arm,Archer.Hand,skipVisuals:!Archer.IsActive);
        if(!Archer.Hand.Cards.Contains(arm)){Log("PROJECTION_FAILED",new{sourceCardId});return null;}
        var reinforcementSource=ConsumeProjectionSource();ArmActivityThisTurn=true;Log("PROJECTION_SOURCE",new{reinforcementSource});
        Log("ARM_GENERATED",arm.Metadata());AssertInvariants();return arm;
    }
    public void QaGuardMaster(){if(Finished)return;GuardCharges=1;Log("QA_GUARD_MASTER_ACTION",new{charges=GuardCharges});}
    public Creature Intercept(Creature target,Creature? source,bool attack)
    {
        if(!attack||GuardCharges==0||target!=Rin.Creature||!Archer.Creature.IsAlive||source==Rin.Creature||source==Archer.Creature)return target;
        GuardCharges--;Metric("guardMasterTriggers");Log("GUARD_INTERCEPT",new{stage="BEFORE_DAMAGE",originalTarget=target.CombatId,target=Archer.Creature.CombatId,charges=GuardCharges});return Archer.Creature;
    }
    public bool QaSuppressField()
    {
        var field=FieldStatuses.FirstOrDefault(f=>f.Duration!=0);if(field==null)return false;
        field.Suppressed=true;field.SuppressUntil=Turn+1;QaTargetTag.RefreshNumbers(this);Log("FIELD_SUPPRESSED",new{field.FieldId,field.Duration,field.SuppressUntil});return true;
    }
    public void AssertInvariants()
    {
        if(Active==Reserve||new[]{Rin,Archer}.Count(f=>f.IsActive)!=1)throw new InvalidOperationException("Exactly one ACTIVE required");
        if(Mana is <0 or >10||Jewel is <0 or >3)throw new InvalidOperationException("Resource bounds violated");
        var found=new HashSet<CardModel>(ReferenceEqualityComparer.Instance);var ids=new HashSet<string>();
        foreach(var f in new[]{Rin,Archer})foreach(var pile in PileTypes.Select(f.Pile).Prepend(f.Deck))foreach(var c in pile.Cards)
        {
            if(c is not StarterCard)
            {
                var native=pile==f.Deck?NativePermanentCards.Get(c):GenericCombatCardOwnership.Get(c);
                if(!GenericCompatibility.Enabled(Player)||native?.Member!=f.CharacterId||c.Owner!=Player||!found.Add(c)||!ids.Add(native.InstanceId))throw new InvalidOperationException("Card owner/deck contamination");
                continue;
            }
            var card=(StarterCard)c;if(card.OwnerCharacterId!=f.CharacterId)throw new InvalidOperationException("Card owner/deck contamination");
            if(card is ProjectedArm&&pile==f.Deck)throw new InvalidOperationException("Projected arm in permanent deck");
            if(!found.Add(c))throw new InvalidOperationException("Card instance present in multiple piles");
            if(string.IsNullOrEmpty(card.InstanceId)||!ids.Add(card.InstanceId))throw new InvalidOperationException("Missing/duplicate card instance ID");
            if(InstanceIds.TryGetValue(c,out var original)&&original!=card.InstanceId)throw new InvalidOperationException("Card identity changed after creation");
        }
    }
    public string SnapshotFingerprint()=>JsonSerializer.Serialize(new{active=Active.CharacterId,Turn,Energy,Mana,Jewel,rin=PileTypes.Select(t=>Ids(Rin.Pile(t))),archer=PileTypes.Select(t=>Ids(Archer.Pile(t)))});
    public void Log(string ev,object? detail=null)
    {
        Telemetry.Add((ev,detail));
        ContractSave.Store(this);
        var text=JsonSerializer.Serialize(new{ev,seed=Seed,turn=Turn,active=Active.CharacterId,reserve=Reserve.CharacterId,energy=Energy,mana=Mana,jewel=Jewel,switchUsed=!FreeSwitchAvailable,
            rinHp=Rin.Creature.CurrentHp,rinBlock=Rin.Creature.Block,archerHp=Archer.Creature.CurrentHp,archerBlock=Archer.Creature.Block,enemyActive=Enemy?.ActiveId,detail});
        GD.Print("[RIN_ARCHER] "+text);
        if(!TestMode.IsOn)System.IO.File.AppendAllText(System.IO.Path.Combine(OS.GetUserDataDir(),"rin-archer-telemetry.jsonl"),text+System.Environment.NewLine);
    }
}
