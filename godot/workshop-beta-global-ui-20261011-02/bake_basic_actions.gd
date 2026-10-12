extends SceneTree
func _initialize():call_deferred("bake")
func aim(a,bone:String,child:String,goal:Vector3):
	var i=a.skeleton.find_bone(bone)
	a.aim_bone(bone,child,goal-a.skeleton.get_bone_global_pose(i).origin,1.0)
	a.skeleton.force_update_all_bone_transforms()
func arm(a,side:String,goal:Vector3,pole:Vector3):
	var s=a.skeleton
	var shoulder=s.get_bone_global_pose(s.find_bone(side+"_harm")).origin
	var elbow=s.get_bone_global_pose(s.find_bone(side+"_larm")).origin
	var hand=s.get_bone_global_pose(s.find_bone(side+"_hand")).origin
	var l1=shoulder.distance_to(elbow);var l2=elbow.distance_to(hand)
	var direction=(goal-shoulder).normalized();var reach=clampf(shoulder.distance_to(goal),0.03,l1+l2-0.003)
	var along=(l1*l1-l2*l2+reach*reach)/(2*reach)
	var bend=sqrt(maxf(0,l1*l1-along*along))
	var normal=(pole-direction*pole.dot(direction)).normalized()
	aim(a,side+"_harm",side+"_larm",shoulder+direction*along+normal*bend)
	aim(a,side+"_larm",side+"_hand",goal)
func bake():
	var a=load("res://FSNReboot/actor.tscn").instantiate();a.is_rin=false;root.add_child(a);await process_frame
	a.animation.stop();var s=a.skeleton
	var lib=a.animation.get_animation_library("")
	var bones=["L_harm","L_larm","R_harm","R_larm","breast","head","waist"]
	var guard={}
	var idle=lib.get_animation("guard")
	a.animation.play("guard");a.animation.advance(0);a.animation.pause();s.force_update_all_bone_transforms()
	for b in bones:guard[b]=s.get_bone_pose_rotation(s.find_bone(b))
	var poses={}
	for kind in ["bow","deflect"]:
		for b in a.initial:s.set_bone_pose_rotation(s.find_bone(b),a.initial[b])
		s.force_update_all_bone_transforms()
		if kind=="bow":
			var forward=(s.global_transform.basis.inverse()*(-a.camera.global_transform.basis.x)).normalized()
			var shoulder=s.get_bone_global_pose(s.find_bone("L_harm")).origin
			arm(a,"L",shoulder+forward*0.50+Vector3(0,-0.025,0),Vector3(0,-1,0))
			arm(a,"R",Vector3(-0.035,1.46,0.10),Vector3(0,-0.25,-1))
		else:
			arm(a,"L",Vector3(-0.04,1.30,0.27),Vector3(0,-1,0))
			arm(a,"R",Vector3(0.04,1.34,0.27),Vector3(0,-1,0))
		var pose={}
		for b in bones:pose[b]=s.get_bone_pose_rotation(s.find_bone(b))
		poses[kind]=pose
		var anim=Animation.new();anim.length=.78 if kind=="bow" else .64
		var keys=[[0.0,guard],[.13,pose],[.285,pose],[.46,pose],[.78,guard]] if kind=="bow" else [[0.0,guard],[.12,pose],[.24,pose],[.38,pose],[.64,guard]]
		for b in bones:
			var track=anim.add_track(Animation.TYPE_ROTATION_3D);anim.track_set_path(track,NodePath(str(a.model.get_path_to(s))+":"+b))
			for key in keys:anim.rotation_track_insert_key(track,key[0],key[1][b])
		if kind=="bow":
			var index=bones.find("R_larm")
			anim.rotation_track_insert_key(index,.34,pose["R_larm"]*Quaternion(Vector3.UP,-.20))
			anim.rotation_track_insert_key(index,.46,pose["R_larm"]*Quaternion(Vector3.UP,-.13))
		lib.remove_animation(kind);lib.add_animation(kind,anim)
	ResourceSaver.save(lib,"res://FSNReboot/archer-beta-actions.tres")
	print("Baked two basic clips: camera-aligned bow arms and forward guard")
	quit()
