extends SceneTree
func _initialize():
	var pack:=PCKPacker.new()
	var path:=ProjectSettings.globalize_path("res://../build/FSNArtReboot.pck")
	assert(pack.pck_start(path)==OK)
	for folder in ["res://FSNReboot","res://actors","res://.godot/imported"]:add_folder(pack,folder)
	assert(pack.flush()==OK)
	print("Packed scene resources: ",path)
	quit()
func add_folder(pack:PCKPacker,path:String):
	for file in DirAccess.get_files_at(path):
		if file.get_extension() in ["png","glb","import","scn","ctex","tscn","tres","gdshader","gd"]:assert(pack.add_file(path.path_join(file),ProjectSettings.globalize_path(path.path_join(file)))==OK)
	for sub in DirAccess.get_directories_at(path):add_folder(pack,path.path_join(sub))
