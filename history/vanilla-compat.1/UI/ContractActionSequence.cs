using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Rooms;
namespace RinArcherCore;
public sealed partial class PresentationEffect:Node2D
{
    public static int LiveCount,StartedCount,FinishedCount;
    readonly string kind;readonly Vector2 origin,target;readonly bool boost;readonly ContractPresentationBody body;
    float age;bool fired,hit;Texture2D? mist;Vector2 muzzle;
    public PresentationEffect(string type,Vector2 from,Vector2 to,bool boosted,ContractPresentationBody actor)
    {
        kind=type;origin=from;muzzle=from;target=to;boost=boosted;body=actor;Name="FSNAction-"+kind;Draw+=Render;
        Ready+=()=>{LiveCount++;StartedCount++;mist=new NoiseTexture2D{Width=128,Height=128,Seamless=true,Noise=new FastNoiseLite{NoiseType=FastNoiseLite.NoiseTypeEnum.Simplex,Frequency=.055f}};Sound(kind=="weapon"?"construct":"jewel");};
        TreeEntered+=()=>GetTree().ProcessFrame+=Tick;TreeExiting+=()=>{GetTree().ProcessFrame-=Tick;LiveCount--;FinishedCount++;};
    }
    void Sound(string name)
    {
        string p=Path.Combine(Path.GetDirectoryName(typeof(PresentationEffect).Assembly.Location)!,"Presentation","Assets",name+".wav");if(!File.Exists(p))return;
        var player=new AudioStreamPlayer{Stream=AudioStreamWav.LoadFromFile(p),VolumeDb=-13};AddChild(player);player.Play();
    }
    void Tick()
    {
        age+=(float)GetProcessDeltaTime();float release=kind=="weapon"?1.4f:1.04f;
        if(!fired&&age>=release){fired=true;muzzle=Hand;if(kind=="gandr"||kind=="weapon")Sound(kind=="weapon"?"slash":"gandr");}
        if(!hit&&age>=release+.12f){hit=true;if(kind=="gandr"||kind=="weapon")Sound("impact");}
        if(age>2.7f){GetParent().QueueFree();return;}QueueRedraw();
    }
    Vector2 Hand=>GodotObject.IsInstanceValid(body)?body.Emitter:origin;
    void GlowLine(Vector2 a,Vector2 b,Color c,float width,float alpha)
    {
        foreach(var (w,opacity) in new[]{(width*8,.025f),(width*4,.06f),(width*2,.18f),(width,1f)})DrawLine(a,b,new(c.R,c.G,c.B,alpha*opacity),w,true);
        DrawLine(a,b,new Color(1,.91f,.92f,alpha),Math.Max(1,width*.25f),true);
    }
    void Sigil(Vector2 p,float r,Color c,float alpha)
    {
        c.A=alpha;DrawArc(p,r,0,Mathf.Tau,96,c,1.3f,true);DrawArc(p,r*.86f,0,Mathf.Tau,96,c,.8f,true);
        for(int i=0;i<12;i++){float a=i*Mathf.Tau/12+age*.35f;var v=Vector2.FromAngle(a);DrawLine(p+v*(r-7),p+v*(r+4),c,1.2f,true);}
        for(int i=0;i<5;i++){float a=i*Mathf.Tau/5-age*.25f;DrawLine(p+Vector2.FromAngle(a)*r*.65f,p+Vector2.FromAngle(a+Mathf.Tau*2/5)*r*.65f,c,.75f,true);}
    }
    void Impact(Vector2 p,float t,bool swords)
    {
        if(t<0||t>.8f)return;float fade=Math.Max(0,1-t/.8f);var c=swords?PresentationTheme.Silver:new Color("ed2856");
        if(t<.1f){DrawCircle(p,22*(1-t/.1f),new Color(1,.95f,.94f,(1-t/.1f)*.75f));}
        for(int i=0;i<24;i++)
        {
            float a=i*2.39996f,velocity=35+(i%6)*21;var v=Vector2.FromAngle(a);Vector2 q=p+v*(8+t*velocity)+new Vector2(0,t*t*50);
            var color=new Color(c.R,c.G,c.B,fade*(.5f+(i%3)*.15f));DrawLine(q-v*(5+14*t),q,color,1.4f,true);
            if(i%4==0)DrawColoredPolygon([q+v*3,q-v.Rotated(.8f)*3,q-v.Rotated(-.8f)*3],color);
        }
        if(mist!=null){for(int i=0;i<3;i++){float size=35+t*55;Vector2 q=p+new Vector2((i-1)*21,-t*30);DrawTextureRect(mist,new Rect2(q-Vector2.One*size/2,Vector2.One*size),false,new Color(.3f,.035f,.09f,fade*.055f));}}
    }
    void Render()
    {
        Vector2 hand=Hand;float charge=Mathf.SmoothStep(0,1,age/.7f),prepareFade=Math.Min(charge,Math.Max(0,(1.15f-age)*5));
        if(kind is "gandr" or "jewel")
        {
            var red=new Color("df1748");Sigil(hand,26+18*charge,red,prepareFade*.7f);
            // Circuit strokes lead into the hand instead of filling the battle with rings.
            for(int i=0;i<4;i++){Vector2 p=hand+new Vector2(-52-i*7,18+i*8);var c=new Color(.25f,.88f,.83f,prepareFade*.55f);DrawPolyline([p,p+new Vector2(18,0),p+new Vector2(26,-18),hand+new Vector2(-10,i*4)],c,1.1f,true);}
            if(kind=="gandr"&&age>=1.04f)
            {
                float flight=Mathf.Clamp((age-1.04f)/.12f,0,1);Vector2 tip=muzzle.Lerp(target,flight);if(age<1.23f)GlowLine(muzzle.Lerp(target,Math.Max(0,flight-.32f)),tip,red,boost?7:5,1);
                Impact(target,age-1.16f,false);
                if(age>1.16f&&age<1.36f)GlowLine(target-new Vector2(0,37),target+new Vector2(0,37),red,2,Math.Max(0,1-(age-1.16f)*5));
            }
        }
        else if(kind is "weapon" or "projection")
        {
            float construct=Math.Min(Mathf.Clamp(age*2,0,1),Math.Max(0,(1.12f-age)*3));
            var steel=new Color(.43f,.74f,.9f,construct*.6f);
            for(int i=0;i<7;i++){float y=origin.Y-60+i*17;DrawLine(new(origin.X-46,y),new(origin.X+42,y),steel,.8f,true);}
            Sigil(origin,46,steel,construct*.35f);
            if(kind=="weapon"&&age>1.3f&&age<1.72f)
            {
                float f=Mathf.Clamp((age-1.3f)/.19f,0,1);Vector2 center=origin.Lerp(target,f);float alpha=Math.Min(1,(1.72f-age)*5);
                Vector2[] Arc(Vector2 p,float radius,float start,float end)=>Enumerable.Range(0,34).Select(i=>p+Vector2.FromAngle(start+(end-start)*i/33)*radius).ToArray();
                DrawPolyline(Arc(center,65,-1.9f,1.05f),new Color(.6f,.86f,1,alpha*.13f),18,true);
                DrawPolyline(Arc(center,65,-1.9f,1.05f),new Color(.95f,.96f,1,alpha),3.2f,true);
                DrawPolyline(Arc(center+new Vector2(-8,10),58,-2.3f,1.2f),new Color(.76f,.12f,.2f,alpha*.6f),7,true);
                DrawPolyline(Arc(center+new Vector2(-8,10),58,-2.3f,1.2f),new Color(.98f,.78f,.82f,alpha),1.5f,true);
                Impact(target,age-1.44f,true);
            }
            else if(kind=="weapon")Impact(target,age-1.44f,true);
        }
    }
}
public static class PresentationEffects
{
    public static async Task Play(ContractRuntime d,StarterCard c)
    {
        if(MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn||NCombatRoom.Instance is not {} room)return;
        string? kind=c.SourceCardId switch{"RIN_S_GANDR" or "RIN_S_JEWEL_RELEASE"=>"gandr","RIN_S_REINFORCEMENT"=>"reinforce","ARC_S_BOW_SHOT"=>"bow","ARC_S_DEFLECT"=>"deflect","RIN_S_REINFORCE_PROJECTION" or "RIN_S_JEWEL_PREPARATION"=>"skill","ARC_S_TRACE"=>"projection","ARM_KANSHOU_BAKUYA" or "ARC_S_CLOSE_COMBAT"=>"weapon",_=>"skill"};
        var source=room.GetCreatureNode(d.Member(c.OwnerCharacterId).Creature);if(source==null)return;
        var body=Descendants(source).OfType<ContractPresentationBody>().FirstOrDefault();if(body==null)return;
        var receipt=d.Receipt(c);var target=d.PlayTarget(c)??receipt.Plan.Target;
        if(c.SourceCardId=="RIN_S_GANDR"&&target!=null&&room.GetCreatureNode(target) is {} targetNode)
        {
            body.Cast("gandr");
            // A single foreground battle pass: Archer cannot cut the beam into pieces.
            var spellLayer=new Node2D{Name="Rin2DGandrLayer",Transform=room.GetGlobalTransformWithCanvas().AffineInverse()};room.AddChild(spellLayer);
            var spell=new RinGandrRuntimeEffect(body,target,targetNode,receipt.JewelBoostUsed);spellLayer.AddChild(spell);
            while(GodotObject.IsInstanceValid(spell)&&spell.IsInsideTree()&&!spell.Released)
                await NGame.Instance!.ToSignal(NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
            // Only the .375 s hit cue gates damage. Recovery plays concurrently.
            return;
        }
        if(kind is "reinforce" or "bow" or "deflect" or "skill"){await BasicActionEffect.Play(d,c,body,kind);return;}
        body.Cast(kind=="projection"?"trace":kind);
        Vector2 from=source.GlobalPosition+new Vector2(50,-145),to=target!=null?room.GetCreatureNode(target)?.GlobalPosition+new Vector2(0,-105)??from:from;
        var layer=new CanvasLayer{Layer=69,Name="ContractActionSequence"};NGame.Instance!.AddChild(layer);layer.AddChild(new PresentationEffect(kind,from,to,receipt.JewelBoostUsed,body));
        // Presentation-only lead-in; original cost, owner, target and damage logic resume unchanged at the action cue.
        float cue=kind=="weapon"?1.4f:kind=="gandr"?1.04f:.75f;
        await NGame.Instance.ToSignal(NGame.Instance.GetTree().CreateTimer(cue),SceneTreeTimer.SignalName.Timeout);
    }
    static IEnumerable<Node> Descendants(Node root){yield return root;foreach(var node in root.GetChildren())foreach(var child in Descendants(node))yield return child;}
}
