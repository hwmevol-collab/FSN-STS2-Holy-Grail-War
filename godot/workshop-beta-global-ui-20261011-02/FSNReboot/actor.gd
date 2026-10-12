extends Node2D
## Full-body FUC meshes in an isolated transparent 3D stage. No gameplay data.
@export var is_rin := true
var viewport: SubViewport
var model: Node3D
var skeleton: Skeleton3D
var animation: AnimationPlayer
var age := 0.0
var action := "idle"
var clock := 0.0
var initial := {}
var bow: Node3D
var sword_l: Node3D
var sword_r: Node3D
var gems: Array[Node3D] = []
var camera: Camera3D
var sprite: Sprite2D
var outline_material: ShaderMaterial
var phase := "idle"
var weapon_materials:Array[ShaderMaterial]=[]
var home_position:Vector2

func _ready():
	process_priority=1
	home_position=position
	viewport = SubViewport.new()
	viewport.size = Vector2i(640,640)
	viewport.transparent_bg = true
	viewport.own_world_3d = true
	viewport.msaa_3d = Viewport.MSAA_4X
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	var stage := Node3D.new()
	viewport.add_child(stage)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 2.6
	camera.position = Vector3(3.2,1.5,5.5)
	stage.add_child(camera)
	camera.look_at(Vector3(0,0.93,0))
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62,0.63,0.74)
	env.ambient_light_energy = 0.65
	environment.environment = env
	stage.add_child(environment)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-38,-35,0)
	light.light_color = Color(1,0.92,0.84)
	light.light_energy = 1.25
	stage.add_child(light)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-15,140,0)
	fill.light_color = Color(0.5,0.72,1)
	fill.light_energy = 0.65
	stage.add_child(fill)
	model = load("res://actors/rin_animated.glb" if is_rin else "res://actors/archer.glb").instantiate()
	stage.add_child(model)
	skeleton = find_type(model,"Skeleton3D") as Skeleton3D
	animation = find_type(model,"AnimationPlayer") as AnimationPlayer
	model.rotation_degrees.y = 42 if is_rin else -16
	for i in skeleton.get_bone_count():
		initial[skeleton.get_bone_name(i)] = skeleton.get_bone_pose_rotation(i)
	style_meshes(model)
	if is_rin:
		animation.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
		animation.play("idle")
		for i in 3:
			var gem := MeshInstance3D.new()
			var shape := SphereMesh.new()
			shape.radius=0.045
			shape.height=0.14
			shape.radial_segments=4
			shape.rings=1
			gem.mesh = shape
			var mat := StandardMaterial3D.new()
			mat.albedo_color = Color(0.7,0.015,0.1)
			mat.emission_enabled = true
			mat.emission = Color(1,0.06,0.23)
			mat.emission_energy_multiplier = 0.55
			mat.metallic=0.5
			mat.roughness=0.22
			gem.material_override = mat
			stage.add_child(gem)
			gem.visible = false
			gems.append(gem)
	else:
		sword_l = make_blade(false)
		sword_r = make_blade(true)
		stage.add_child(sword_l)
		stage.add_child(sword_r)
		build_archer_library()
		build_basic_actions()
		bow=make_bow()
		stage.add_child(bow)
		animation.play("guard")
	sprite = Sprite2D.new()
	sprite.texture = viewport.get_texture()
	sprite.position = Vector2(0,-160)
	sprite.scale = Vector2.ONE * 0.65
	sprite.flip_h = true
	add_child(sprite)

func find_type(n: Node, type: String) -> Node:
	if n.is_class(type): return n
	for c in n.get_children():
		var found := find_type(c,type)
		if found: return found
	return null

func style_meshes(n: Node):
	if "hand0" in n.name and not "hand00" in n.name:n.visible=false
	if n is MeshInstance3D:
		for s in n.mesh.get_surface_count():
			var m = n.mesh.surface_get_material(s)
			if m is StandardMaterial3D:
				m = m.duplicate()
				m.cull_mode = BaseMaterial3D.CULL_DISABLED
				m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
				m.specular_mode = BaseMaterial3D.SPECULAR_TOON
				m.roughness = 0.8
				m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
				if is_rin:
					var index=int(m.resource_name.substr(0,4))
					var part=["hair","face","body","eye","mouth"][index]
					m.albedo_texture=load("res://actors/rin_"+part+".png")
				elif "tex01" in m.resource_name:
					m.albedo_texture=load("res://actors/rin_body.png" if is_rin else "res://actors/archer_body.png")
				elif "tex02" in m.resource_name:
					m.albedo_texture=load("res://actors/rin_hair.png" if is_rin else "res://actors/archer_coat.png")
				n.set_surface_override_material(s,m)
	for c in n.get_children(): style_meshes(c)

func make_blade(white: bool) -> Node3D:
	# FUC selected equipment 0001 kansyo / 0002 bakuya; visual form checked against CM II p126.
	var root:Node3D=load("res://actors/archer_equipment_2.glb" if white else "res://actors/archer_equipment_1.glb").instantiate()
	var material:=ShaderMaterial.new()
	material.shader=load("res://FSNReboot/projection.gdshader")
	material.set_shader_parameter("steel",Color(0.82,0.85,0.9) if white else Color(0.045,0.05,0.07))
	material.set_shader_parameter("black_blade",not white)
	apply_weapon_material(root,material)
	weapon_materials.append(material)
	root.visible=false
	return root

func apply_weapon_material(n:Node,material:ShaderMaterial):
	if n is MeshInstance3D:n.material_override=material
	for c in n.get_children():apply_weapon_material(c,material)

func build_archer_library():
	animation = AnimationPlayer.new()
	animation.name = "AuthoredActionPlayer"
	model.add_child(animation)
	if ResourceLoader.exists("res://FSNReboot/archer-authored.tres"):
		animation.add_animation_library("",load("res://FSNReboot/archer-beta-actions.tres" if ResourceLoader.exists("res://FSNReboot/archer-beta-actions.tres") else "res://FSNReboot/archer-authored.tres"))
		return
	var lib := AnimationLibrary.new()
	var guard := {"L_harm":Vector3(0,0,65),"R_harm":Vector3(0,0,-65),"L_larm":Vector3(0,-20,0),"R_larm":Vector3(0,20,0),"L_hleg":Vector3(0,0,-8),"R_hleg":Vector3(0,0,8)}
	var prepare := {"L_harm":Vector3(-35,-18,52),"R_harm":Vector3(-35,18,-52),"L_larm":Vector3(0,-64,0),"R_larm":Vector3(0,64,0),"breast":Vector3(0,-12,0),"head":Vector3(0,12,0)}
	var windup := {"L_harm":Vector3(-35,20,5),"R_harm":Vector3(-28,-48,-18),"L_larm":Vector3(0,-35,0),"R_larm":Vector3(0,80,0),"breast":Vector3(12,-46,-10),"waist":Vector3(0,-18,0),"L_hleg":Vector3(18,0,-16),"R_hleg":Vector3(-18,0,20),"R_lleg":Vector3(35,0,0)}
	var strike := {"L_harm":Vector3(28,-80,22),"R_harm":Vector3(42,65,-35),"L_larm":Vector3(0,-24,0),"R_larm":Vector3(0,18,0),"breast":Vector3(18,55,5),"waist":Vector3(0,22,0),"L_hleg":Vector3(-25,0,-18),"R_hleg":Vector3(28,0,18),"L_lleg":Vector3(25,0,0)}
	var follow := {"L_harm":Vector3(12,-35,55),"R_harm":Vector3(35,65,-68),"L_larm":Vector3(0,-30,0),"R_larm":Vector3(0,28,0),"breast":Vector3(8,38,0),"waist":Vector3(0,12,0),"L_hleg":Vector3(-12,0,-12),"R_hleg":Vector3(12,0,12)}
	var keys := [[0.0,guard],[0.42,prepare],[0.95,prepare],[1.27,windup],[1.44,strike],[1.7,follow],[2.35,guard]]
	for pair in [["guard",[[0.0,guard],[1.4,guard]]],["projection",keys]]:
		var anim := Animation.new()
		anim.length = 1.4 if pair[0]=="guard" else 2.35
		anim.loop_mode = Animation.LOOP_LINEAR if pair[0]=="guard" else Animation.LOOP_NONE
		var names := {}
		for key in pair[1]:
			for bone in key[1]: names[bone]=true
		for bone in names:
			var index := skeleton.find_bone(bone)
			if index<0: continue
			var track := anim.add_track(Animation.TYPE_ROTATION_3D)
			anim.track_set_path(track,NodePath(str(model.get_path_to(skeleton))+":"+bone))
			for key in pair[1]:
				var degrees: Vector3 = key[1].get(bone,Vector3.ZERO)
				var q: Quaternion = initial[bone] * Quaternion.from_euler(degrees*PI/180)
				anim.rotation_track_insert_key(track,key[0],q)
		lib.add_animation(pair[0],anim)
	animation.add_animation_library("",lib)
	if OS.has_feature("editor"):
		ResourceSaver.save(lib,"res://FSNReboot/archer-authored.tres")

func perform(kind: String):
	action = kind
	age = 0.0
	phase = "prepare"
	if is_rin:
		animation.pause()
		animation.play("gandr_source",0.1)
		animation.pause()
		animation.seek(0.0,true)
	else:
		animation.play(kind if kind in ["bow","deflect"] else "guard" if kind=="skill" else "projection",0.04)

func bone_position(name: String) -> Vector3:
	var i := skeleton.find_bone(name)
	return skeleton.global_transform * skeleton.get_bone_global_pose(i).origin if i>=0 else Vector3.ZERO

func emitter_position() -> Vector2:
	var p=camera.unproject_position(bone_position("L_hand" if action=="bow" else "R_hand"))-Vector2(viewport.size)/2.0
	p.x=-p.x
	return sprite.position+p*sprite.scale

func aim_bone(bone:String,child:String,direction:Vector3,weight:float):
	# Authored staging layer: aim the real weighted upper/lower arm, rather than moving the portrait.
	var index=skeleton.find_bone(bone)
	var next=skeleton.find_bone(child)
	var global_pose=skeleton.get_bone_global_pose(index)
	var current=(skeleton.get_bone_global_pose(next).origin-global_pose.origin).normalized()
	var rotation=Quaternion(current,direction.normalized())
	var parent=skeleton.get_bone_parent(index)
	var parent_basis=skeleton.get_bone_global_pose(parent).basis if parent>=0 else Basis.IDENTITY
	var local=(parent_basis.inverse()*Basis(rotation)*global_pose.basis).orthonormalized().get_rotation_quaternion()
	skeleton.set_bone_pose_rotation(index,skeleton.get_bone_pose_rotation(index).slerp(local,weight))

func _process(delta):
	clock += delta
	if not skeleton: return
	if action != "idle":
		age += delta
		if is_rin:
			# Separate anticipation from the authentic 0.383 s finger-shot motion.
			var clip_time := clampf((age-0.78)*0.85,0.0,0.383) if action!="jewel" else 0.0
			animation.seek(clip_time,true)
			if age<0.78 or action=="jewel":
				var anticipation=sin(clampf(age/0.78,0,1)*PI)
				for pair in [["R_harm",Vector3(0,-24,-35)],["R_larm",Vector3(0,0,-50)],["L_harm",Vector3(0,15,25)],["L_larm",Vector3(0,0,55)]]:
					var i=skeleton.find_bone(pair[0])
					if i>=0:skeleton.set_bone_pose_rotation(i,skeleton.get_bone_pose_rotation(i)*Quaternion.from_euler(pair[1]*PI/180*anticipation))
			var extension=smoothstep(0.72,1.02,age)*(1.0-smoothstep(1.45,2.12,age)) if action!="jewel" else 0.0
			var preparation=(1.0-smoothstep(0.72,1.02,age))*smoothstep(0.0,0.3,age)
			aim_bone("R_harm","R_larm",Vector3(-0.35,-0.23,0.1),preparation)
			aim_bone("R_larm","R_hand",Vector3(-0.1,0.65,-0.2),preparation)
			aim_bone("R_harm","R_larm",Vector3(-1,0.12,-0.22),extension)
			aim_bone("R_larm","R_hand",Vector3(-1,0.06,-0.2),extension)
			phase = "jewel" if age<0.45 else "circuit" if age<0.94 else "shot" if age<1.23 else "recover"
			for i in gems.size():
				gems[i].visible = age<1.15
				gems[i].position = bone_position("L_hand" if action=="bow" else "R_hand")+Vector3(0.16*cos(clock*3+i*TAU/3),0.11+0.1*sin(clock*3+i*TAU/3),0.12)
				gems[i].rotation_degrees = Vector3(clock*90,i*120,clock*55)
			if age>2.15:
				action = "idle"
				animation.play("idle",0.22)
		else:
			if action=="trace":animation.seek(minf(age,0.95),true)
			phase = "construct" if age<0.7 else "armed" if age<1.2 else "cut" if age<1.65 else "recover"
			if age>(0.78 if action=="bow" else 0.64 if action in ["deflect","skill"] else 1.35 if action=="trace" else 2.4):
				action = "idle"
				animation.play("guard",0.18)
			position.x=home_position.x+(sin(clampf((age-1.15)/1.2,0,1)*PI)*100 if action in ["weapon","projection"] else 0.0)
	if not is_rin:
		for pair in [[sword_l,"L_hand"],[sword_r,"R_hand"]]:
			var index := skeleton.find_bone(pair[1])
			pair[0].transform = skeleton.global_transform * skeleton.get_bone_global_pose(index)
			pair[0].rotate_object_local(Vector3.RIGHT,-PI/2 if action=="deflect" else PI/2)
			pair[0].visible = action=="deflect" or (action in ["trace","weapon","projection"] and age>0.4)
			pair[0].scale *= 1.0 if action=="deflect" else smoothstep(0.4,0.85,age) if age<0.85 else 1.0
			var mat:ShaderMaterial=weapon_materials[0 if pair[0]==sword_l else 1]
			mat.set_shader_parameter("reveal",1.0 if action=="deflect" else smoothstep(0.4,0.9,age))
			mat.set_shader_parameter("construction",0.0 if action=="deflect" else 1.0-smoothstep(0.9,1.2,age))
	if bow:
		bow.visible=action=="bow"
		var pose=skeleton.global_transform*skeleton.get_bone_global_pose(skeleton.find_bone("L_hand"))
		var forward=-camera.global_transform.basis.x
		var depth=Vector3(camera.global_transform.basis.z.x,0,camera.global_transform.basis.z.z).normalized()
		bow.global_transform=Transform3D(Basis(depth,Vector3.UP,forward),pose.origin)
	if is_rin:set_hand_variant(model,action=="gandr" and age>0.78 and age<1.55)
	queue_redraw()

func set_hand_variant(n:Node,pointing:bool):
	if n.name.begins_with("Rhand"):
		n.visible=("Rhand03" in n.name) if pointing else ("Rhand00" in n.name)
	for c in n.get_children():set_hand_variant(c,pointing)

func _draw():
	# Ground contact belongs behind the full-body actor; scene has genuine bone motion.
	draw_set_transform(Vector2(0,-6),0,Vector2(1,0.14))
	draw_circle(Vector2.ZERO,85,Color(0.01,0.0,0.02,0.26))
	draw_set_transform(Vector2.ZERO)

func build_basic_actions():
	var lib=animation.get_animation_library("")
	if lib.has_animation("bow") and lib.has_animation("deflect"):return
	var guard={"L_harm":Vector3(0,0,65),"R_harm":Vector3(0,0,-65),"L_larm":Vector3(0,-20,0),"R_larm":Vector3(0,20,0)}
	var draw={"L_harm":Vector3(-12,-30,12),"R_harm":Vector3(-25,5,-38),"L_larm":Vector3(0,-10,0),"R_larm":Vector3(0,100,0),"breast":Vector3(0,-18,0),"waist":Vector3(0,-8,0),"head":Vector3(0,20,0)}
	var release=draw.duplicate();release["R_larm"]=Vector3(0,128,0);release["breast"]=Vector3(0,-23,0)
	var defend={"L_harm":Vector3(-35,-25,50),"R_harm":Vector3(-35,25,-50),"L_larm":Vector3(0,-70,0),"R_larm":Vector3(0,70,0),"breast":Vector3(-6,-8,0),"L_hleg":Vector3(8,0,-10),"R_hleg":Vector3(-8,0,10)}
	for pair in [["bow",[[0.0,guard],[0.13,draw],[0.285,draw],[0.34,release],[0.46,release],[0.78,guard]]],["deflect",[[0.0,guard],[0.12,defend],[0.26,defend],[0.4,defend],[0.64,guard]]]]:
		var anim=Animation.new();anim.length=0.78 if pair[0]=="bow" else 0.64
		var names={}
		for key in pair[1]:
			for bone in key[1]:names[bone]=true
		for bone in names:
			if skeleton.find_bone(bone)<0:continue
			var track=anim.add_track(Animation.TYPE_ROTATION_3D)
			anim.track_set_path(track,NodePath(str(model.get_path_to(skeleton))+":"+bone))
			for key in pair[1]:
				var degrees:Vector3=key[1].get(bone,Vector3.ZERO)
				anim.rotation_track_insert_key(track,key[0],initial[bone]*Quaternion.from_euler(degrees*PI/180))
		lib.add_animation(pair[0],anim)

func make_bow() -> Node3D:
	# Original simple black bow geometry; no additional extracted asset.
	var root=Node3D.new();root.name="AuthoredBlackBow"
	var material=StandardMaterial3D.new();material.albedo_color=Color(0.07,0.08,0.1);material.metallic=0.75;material.roughness=0.35
	var points:Array[Vector3]=[]
	for i in 13:
		var f=float(i)/12;points.append(Vector3(0,lerpf(-0.64,0.64,f),sin(f*PI)*0.2))
	for i in 12:add_rod(root,points[i],points[i+1],0.014,material)
	var string_mat=StandardMaterial3D.new();string_mat.albedo_color=Color(0.9,0.85,0.78)
	add_rod(root,points[0],points[12],0.0025,string_mat)
	return root

func add_rod(root:Node3D,a:Vector3,b:Vector3,radius:float,mat:Material):
	var n=MeshInstance3D.new();var mesh=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=a.distance_to(b);mesh.radial_segments=8
	n.mesh=mesh;n.material_override=mat;n.position=(a+b)/2;n.quaternion=Quaternion(Vector3.UP,(b-a).normalized());root.add_child(n)
