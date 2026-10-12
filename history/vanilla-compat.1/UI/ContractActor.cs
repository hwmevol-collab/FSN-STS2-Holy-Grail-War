using MegaCrit.Sts2.Core.Nodes.Combat;
namespace RinArcherCore;
public sealed partial class ContractPresentationBody:Node2D
{
    readonly bool rin;Node2D? actor;Label? tag;ContractRuntime? contract;Creature? entity;
    static bool packed;int lastHp=-1;float hurt;NCreature? body;bool? lastActive;string? lastLanguage;
    public ContractPresentationBody(bool master)
    {
        rin=master;Name="Visuals";Ready+=Initialize;
        TreeEntered+=()=>GetTree().ProcessFrame+=Tick;TreeExiting+=()=>GetTree().ProcessFrame-=Tick;
    }
    public static NCreatureVisuals Create(bool rin)
    {
        var root=new NCreatureVisuals{Name=rin?"RinReboot":"ArcherReboot"};
        void Add(Node node){root.AddChild(node);node.Owner=root;node.UniqueNameInOwner=true;}
        Add(new ContractPresentationBody(rin));
        Add(new Control{Name="Bounds",Position=new(-95,-320),Size=new(190,320),MouseFilter=Control.MouseFilterEnum.Ignore});
        Add(new Marker2D{Name="IntentPos",Position=new(0,-340)});Add(new Marker2D{Name="CenterPos",Position=new(0,-150)});Add(new Marker2D{Name="TalkPos",Position=new(0,-340)});return root;
    }
    void Initialize()
    {
        if(!packed){string path=Path.Combine(Path.GetDirectoryName(typeof(ContractPresentationBody).Assembly.Location)!,"FSNArtReboot.pck");if(!ProjectSettings.LoadResourcePack(path,false))throw new InvalidOperationException("Cannot load art scene pack");packed=true;}
        actor=ResourceLoader.Load<PackedScene>(rin?"res://Rin2D/scenes/rin_a.tscn":"res://FSNReboot/actor.tscn").Instantiate<Node2D>();
        if(rin)actor.Scale=Vector2.One*.202f;else actor.Set("is_rin",false);AddChild(actor);
        tag=PresentationTheme.Label("",15);tag.Position=new(-90,-344);tag.Size=new(180,42);tag.HorizontalAlignment=HorizontalAlignment.Center;AddChild(tag);
    }
    public void Cast(string kind){actor?.Call("perform",kind);}
    public Node2D? Actor=>actor;
    public bool IsRin=>rin;
    public Vector2 Emitter=>actor==null?GlobalPosition+new Vector2(50,-145):actor.GlobalTransform*actor.Call("emitter_position").AsVector2();
    void Tick()
    {
        if(body==null){Node? n=GetParent();while(n!=null&&n is not NCreature)n=n.GetParent();body=n as NCreature;}
        if(body!=null&&(entity!=body.Entity||contract==null)){entity=body.Entity;contract=ContractRuntime.For(entity);}
        bool active=contract==null||entity==contract.Active.Creature;
        if(entity!=null){if(lastHp>=0&&entity.CurrentHp<lastHp)hurt=1;lastHp=entity.CurrentHp;}
        hurt=Math.Max(0,hurt-(float)GetProcessDeltaTime()*4);
        string language=MegaCrit.Sts2.Core.Localization.LocManager.Instance.Language;
        if(tag!=null&&(lastActive!=active||lastLanguage!=language)){lastActive=active;lastLanguage=language;tag.Text=(rin?FsnLoc.Text("UI_D5116EA0D04E"):"Archer")+"  ·  "+(active?FsnLoc.Text("UI_8065FA1C7928"):FsnLoc.Text("UI_CF2E968D2598"));tag.AddThemeColorOverride("font_color",active?PresentationTheme.Paper:PresentationTheme.Muted);}
        if(actor!=null)actor.Modulate=new Color(active?1:.75f,active?1:.75f,active?1:.8f,1).Lerp(new Color(1,.4f,.45f),hurt*.55f);
    }
}
