using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.TestSupport;
namespace FateStayNight;
public static class CastVfx
{
    public static void Play(CardModel card,Creature? target=null){
        if(TestMode.IsOn||NCombatRoom.Instance==null||card.Owner.Creature.GetCreatureNode() is not {} creature)return;
        var room=NCombatRoom.Instance;
        // Bound effects during autoplay chains; each node owns its short lifetime.
        if(room.GetChildren().OfType<FateCastEffect>().Count()>=10)return;
        bool saber=card is SwiftStrike or SwordGuard or LuckyProtection;
        var root=new FateCastEffect{Name="FSN"+card.GetType().Name+"Cast",Kind=card.GetType().Name,Saber=saber,ZIndex=25};
        room.AddChild(root);root.GlobalPosition=creature.GlobalPosition;
        root.Destination=target?.GetCreatureNode() is {} enemy?root.ToLocal(enemy.GlobalPosition)+new Vector2(0,-100):new Vector2(430,-130);
        root.Start();
        creature.Visuals?.GetNodeOrNull<Sprite2D>("FSNPortrait")?.GetNodeOrNull<FighterMotion>("FSNMotion")?.Strike();
    }
}
// Hook each FSN OnPlay, after the native wrapper has accepted and scheduled the card.
[HarmonyPatch]
public static class FateCastPatch
{
    static IEnumerable<System.Reflection.MethodBase> TargetMethods()=>typeof(FateCard).Assembly.GetTypes().Where(t=>!t.IsAbstract&&typeof(FateCard).IsAssignableFrom(t)).Select(t=>AccessTools.DeclaredMethod(t,"OnPlay"));
    static void Prefix(CardModel __instance,CardPlay play)=>CastVfx.Play(__instance,play.Target);
}
public partial class FateCastEffect : Node2D
{
    public string Kind="";
    public bool Saber;
    public Vector2 Destination;
    float time;
    public void Start()=>NativeAnimation.Start(this,_Process,_Draw);
    float Duration=>Kind is nameof(FateNight) or nameof(Coordination)?1.15f:.78f;
    public override void _Process(double delta){time+=(float)delta;if(time>=Duration){QueueFree();return;}QueueRedraw();}
    void Glow(Vector2[] points,Color color,float width=2){
        DrawPolyline(points,new Color(color,.08f),width*9,true);
        DrawPolyline(points,new Color(color,.24f),width*3,true);
        DrawPolyline(points,color,width,true);
    }
    void Ring(Vector2 center,float rx,float ry,Color c,float phase=0){
        var p=new Vector2[81];for(int i=0;i<=80;i++){float a=i*Mathf.Tau/80+phase;p[i]=center+new Vector2(Mathf.Cos(a)*rx,Mathf.Sin(a)*ry);}Glow(p,c,1.5f);
    }
    public override void _Draw(){
        float t=time/Duration, fade=Mathf.Sin(t*Mathf.Pi), grow=1-Mathf.Pow(1-t,3);
        Color c=new(Saber?"90d9ff":"65ffd0");c.A=fade;
        var origin=new Vector2(0,-135);
        if(Kind is nameof(PosterStrike) or nameof(SwiftStrike)){
            // Travelling slash then impact at the actual selected creature.
            float travel=Mathf.Clamp(t*2.7f,0,1);var hit=origin.Lerp(Destination,travel);
            for(int j=0;j<3;j++){
                var arc=new Vector2[32];for(int i=0;i<32;i++){float a=-2.1f+i/31f*2.6f;arc[i]=hit+new Vector2(Mathf.Cos(a)*(95+j*24),Mathf.Sin(a)*(65+j*15));}
                Glow(arc,new Color(j==0?Colors.White:c,fade*(1-j*.22f)),j==0?3:2);
            }
            if(t>.34f){float impact=(t-.34f)/.66f;for(int i=0;i<12;i++){var direction=Vector2.FromAngle(i*Mathf.Tau/12+.22f);Glow([Destination+direction*(15+impact*30),Destination+direction*(35+impact*105)],new Color(i%3==0?new Color("ffe8a8"):c,(1-impact)*.8f),1.4f);}}
        }else if(Kind is nameof(SwordGuard) or nameof(PaperShield) or nameof(Precaution) or nameof(LuckyProtection)){
            for(int j=0;j<3;j++){var shield=new Vector2[7];for(int i=0;i<=6;i++){float a=i*Mathf.Tau/6-Mathf.Pi/6;shield[i]=origin+new Vector2(Mathf.Cos(a),Mathf.Sin(a))*(70+j*23)*(0.6f+grow*.4f);}Glow(shield,new Color(c,fade*(1-j*.22f)),2);}
            Glow([origin+new Vector2(-40,0),origin+new Vector2(-8,35),origin+new Vector2(50,-40)],new Color("fff3c4",fade),3);
        }else if(Kind is nameof(QuickDodge) or nameof(DesperateFlight) or nameof(GemWind)){
            for(int j=0;j<5;j++){var arc=new Vector2[36];for(int i=0;i<36;i++){float a=i/35f*4.7f+t*3+j*.6f;arc[i]=origin+new Vector2(Mathf.Cos(a)*(110+j*16),Mathf.Sin(a)*(38+j*10));}Glow(arc,new Color(c,fade*.75f),1.5f);}
        }else if(Kind is nameof(FateNight) or nameof(Coordination) or nameof(CounterfeitLife)){
            Ring(new(0,-10),130*grow,35*grow,c);Ring(origin,105*grow,105*grow,new Color("edc984",fade*.8f));
            for(int j=0;j<7;j++){float a=j*Mathf.Tau/7+t*1.1f;var p=origin+Vector2.FromAngle(a)*(90+grow*30);Glow([p,p+new Vector2(0,-85)*fade],new Color(j%2==0?c:new Color("ffe2a1"),fade*.8f),2);}
        }else{
            Ring(new(0,-6),120*grow,28*grow,c);
            for(int j=0;j<6;j++){float x=-88+j*31;float rise=Mathf.Clamp(t*2,0,1);Glow([new(x,0),new(x,-55*rise),new(x+16,-75*rise),new(x+16,-160*rise),new(x+30,-180*rise),new(x+30,-270*rise)],c,2);}
            if(Kind==nameof(StructuralAnalysis))Ring(origin,95,95,new Color("c4ffde",fade),t);
        }
        for(int i=0;i<18;i++){
            float a=i*2.39996f;var p=origin+new Vector2(Mathf.Cos(a),Mathf.Sin(a))*(24+grow*(65+i*5));
            DrawCircle(p,1.2f+i%3*.6f,new Color(i%3==0?new Color("fff2cc"):c,fade*.8f));
        }
    }
}
