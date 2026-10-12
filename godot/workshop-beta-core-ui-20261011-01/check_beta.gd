extends SceneTree
func _initialize():call_deferred("check")
func check():
	var a=load("res://FSNReboot/actor.tscn").instantiate();a.is_rin=false;root.add_child(a)
	var r=load("res://Rin2D/scenes/rin_a.tscn").instantiate();root.add_child(r)
	await process_frame
	for kind in ["bow","deflect"]:
		a.perform(kind)
		await process_frame
		assert(a.animation.has_animation(kind))
		print(kind," clip ",a.animation.get_animation(kind).length)
	r.perform("reinforce");await process_frame;assert(r.player.has_animation("reinforce"))
	print("reinforce clip ",r.player.get_animation("reinforce").length)
	ResourceSaver.save(a.animation.get_animation_library(""),"res://FSNReboot/archer-beta-actions.tres")
	quit()
