using System.Text.RegularExpressions;
using MegaCrit.Sts2.Core.MonsterMoves.Intents;
namespace FateStayNight;
public static class Rules
{
    public static int SumArabicNumbers(string text){
        // Remove markup including image paths before inspecting only the effect description.
        text=Regex.Replace(text,@"\[img[^\]]*\].*?\[/img\]","",RegexOptions.Singleline);
        text=Regex.Replace(text,@"\[[^\]]*\]","");
        return Regex.Matches(text,@"[0-9]+").Sum(m=>int.TryParse(m.Value,out int n)?n:0);
    }
    public static bool Linked(CardModel c)=>c is Coordination or FateNight;
    public static bool SaberCard(CardModel c)=>c is LuckyProtection or SwiftStrike or SwordGuard;
    public static bool Immortal(CardModel c)=>c is Coordination && c.IsUpgraded;
    public static bool IsAttacking(Creature c)=>c.Monster?.NextMove.Intents.Any(i=>i is AttackIntent)??false;
    public static int IntentDamage(Creature c)=>c.Monster?.NextMove.Intents.OfType<AttackIntent>().Sum(i=>i.GetTotalDamage(c.CombatState!.Allies,c))??0;
    public static (int hp,int temporary) ReceiveLife(int received,int maximum)=>(Math.Min(received,maximum),Math.Max(0,received-maximum));
}
