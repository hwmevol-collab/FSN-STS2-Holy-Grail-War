extends SceneTree
func _initialize():
	call_deferred("inspect")
func inspect():
	var a=load("res://FSNReboot/actor.tscn").instantiate()
	root.add_child(a)
	await process_frame
	var bone_id=a.skeleton.find_bone("R_harm")
	print("pose ",a.skeleton.get_bone_pose(bone_id)," rest ",a.skeleton.get_bone_rest(bone_id)," parent ",a.skeleton.get_bone_parent(bone_id))
	print(a.animation.get_animation_list())
	dump_meshes(a.model)
	var clip=a.animation.get_animation("gandr_source")
	for i in range(min(6,clip.get_track_count())):print(clip.track_get_path(i))
	for t in [0.0,0.1,0.2,0.35]:
		a.animation.play("gandr_source")
		a.animation.pause()
		a.animation.seek(t,true)
		await process_frame
		print(t," ",a.bone_position("R_hand")," ",a.skeleton.get_bone_pose_rotation(a.skeleton.find_bone("R_harm")))
	quit()
func dump_meshes(n:Node):
	if n is MeshInstance3D:
		for s in n.mesh.get_surface_count():
			var m=n.get_surface_override_material(s)
			print(n.name," ",s," ",m.resource_name," ",m.albedo_texture.resource_path)
	for c in n.get_children():dump_meshes(c)
