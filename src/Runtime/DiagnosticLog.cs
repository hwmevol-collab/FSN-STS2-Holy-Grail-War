using System.Threading.Channels;
using System.Text;
namespace RinArcherCore;

// Best-effort diagnostics only. Native saves and their readback stay synchronous and strict.
public static class DiagnosticLog
{
    const long MaxBytes=2*1024*1024;
    static readonly Channel<(string path,string line)> Queue=Channel.CreateBounded<(string,string)>(new BoundedChannelOptions(1024){SingleReader=true,FullMode=BoundedChannelFullMode.DropOldest});
    static readonly Task Worker=Task.Run(Drain);
    static string? directory;
    public static bool Verbose {get;}=System.Environment.GetEnvironmentVariable("FSN_VERBOSE_LOGS")=="1";
    public static void Write(string file,string line)
    {
        try{directory??=OS.GetUserDataDir();Queue.Writer.TryWrite((Path.Combine(directory,file),line));}
        catch(IOException){}catch(UnauthorizedAccessException){}
    }
    static async Task Drain()
    {
        while(await Queue.Reader.WaitToReadAsync())
        {
            await Task.Delay(250);
            var batch=new Dictionary<string,StringBuilder>();
            for(int i=0;i<1024&&Queue.Reader.TryRead(out var row);i++)
            {if(!batch.TryGetValue(row.path,out var text))batch[row.path]=text=new();text.AppendLine(row.line);}
            foreach(var (path,text) in batch)
            {
                try
                {
                    if(File.Exists(path)&&new FileInfo(path).Length>=MaxBytes)File.Move(path,path+".previous",overwrite:true);
                    File.AppendAllText(path,text.ToString());
                }
                catch(IOException){}catch(UnauthorizedAccessException){}
            }
        }
    }
}
