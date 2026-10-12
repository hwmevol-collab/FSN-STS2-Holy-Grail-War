extends SceneTree
func _initialize():call_deferred("inspect")
func inspect():
	var a=load("res://FSNReboot/actor.tscn").instantiate();a.is_rin=false;root.add_child(a);await process_frame
	for side in ["L","R"]:
		for part in ["harm","larm","hand"]:
			var n=side+"_"+part
			print(n," local ",a.skeleton.get_bone_global_pose(a.skeleton.find_bone(n)).origin," world ",a.bone_position(n))
	print("skeleton ",a.skeleton.global_transform," camera ",a.camera.global_transform)
	quit()
