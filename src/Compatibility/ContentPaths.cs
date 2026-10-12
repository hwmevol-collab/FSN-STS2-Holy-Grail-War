namespace RinArcherCore;
public static class ContentPaths
{
    public static string Root
    {
        get
        {
            var directory=new DirectoryInfo(Path.GetDirectoryName(typeof(ContentPaths).Assembly.Location)??throw new InvalidDataException("FSN_CONTENT_PATH_UNCONFIRMED"));
            if(directory.Parent?.Name=="lib"&&directory.Parent.Parent is {} root&&File.Exists(Path.Combine(root.FullName,"mod-variants.manifest")))return root.FullName;
            return directory.FullName;
        }
    }
}
