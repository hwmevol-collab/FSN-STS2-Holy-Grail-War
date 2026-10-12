extends Node2D
## Six authored action compositions; exported art is used by native cards.
var actor:Node2D
var theme:=0
var shots=["rin_gandr","rin_jewel","rin_power","archer_cut","archer_projection","archer_power"]
func _ready():
	for index in shots.size():
		theme=index
		actor=load("res://FSNReboot/actor.tscn").instantiate()
		actor.is_rin=index<3
		actor.position=Vector2(340 if index<3 else 345,830)
		actor.scale=Vector2.ONE*2.1
		add_child(actor)
		await get_tree().process_frame
		actor.perform("gandr" if index<3 else "weapon")
		actor.set_process(false)
		var moment=[1.05,0.42,0.7,1.36,0.82,1.03][index]
		actor._process(moment)
		if index>=3:
			actor.animation.seek(moment,true)
			actor._process(0.0)
		actor.animation.pause()
		if index==0:
			actor.model.rotation_degrees.y=8
			actor.position.x=315
		if index==1:actor.position.x=240
		if index==2:actor.position.x=125;actor.modulate=Color(0.75,0.63,0.67,0.85)
		if index==3:actor.position.x=480;actor.model.rotation_degrees.y=12
		if index>=4:
			actor.model.visible=false
			actor.camera.size=1.7
			actor.camera.look_at(Vector3(0,1.0,0))
			actor.position=Vector2(440,810)
			actor._process(0.0)
		queue_redraw()
		await get_tree().process_frame
		await get_tree().process_frame
		actor.animation.seek(clampf((moment-0.78)*0.85,0,0.383) if index<3 else moment,true)
		actor._process(0.0)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://../build/source/Presentation/Assets/"+shots[index]+".png")
		actor.queue_free()
		await get_tree().process_frame
	get_tree().quit()
func ring(center:Vector2,r:float,color:Color):
	draw_arc(center,r,0,TAU,128,color,2,true)
	draw_arc(center,r-12,0,TAU,128,color*Color(1,1,1,0.4),1,true)
	for i in 16:
		var a=i*TAU/16
		draw_line(center+Vector2.from_angle(a)*(r-8),center+Vector2.from_angle(a)*r,color,2,true)
func ruby(center:Vector2,r:float):
	var p=PackedVector2Array([center+Vector2(0,-r),center+Vector2(r*0.63,-r*0.3),center+Vector2(r*0.5,r*0.63),center+Vector2(0,r),center+Vector2(-r*0.63,r*0.24),center+Vector2(-r*0.5,-r*0.5)])
	draw_colored_polygon(p,Color("8e0929"))
	draw_colored_polygon(PackedVector2Array([p[0],p[1],center,p[5]]),Color("f25d76"))
	draw_colored_polygon(PackedVector2Array([p[1],p[2],p[3],center]),Color("c51d45"))
	draw_polyline(p+PackedVector2Array([p[0]]),Color("ffb5c5"),2,true)
	draw_line(p[0],center,Color("ffe0e5"),2,true)
func _draw():
	for y in range(600):
		var v=float(y)/600.0
		draw_line(Vector2(0,y),Vector2(960,y),Color("100e1a").lerp(Color("3c1021") if theme<3 else Color("192d40"),v),1)
	var accent=Color("d54365") if theme<3 else Color("88c3df")
	for i in 10:
		var x=130+i*96
		draw_line(Vector2(x,-100),Vector2(x-380,700),accent*Color(1,1,1,0.07),2,true)
	if theme==0:
		ring(Vector2(610,320),152,Color(0.9,0.18,0.36,0.35))
		for i in range(16,0,-1):draw_line(Vector2(400,330),Vector2(950,246),Color(1,0.05,0.16,0.018),i*7,true)
		draw_line(Vector2(400,330),Vector2(950,246),Color("ffc6da"),6,true)
	if theme==1:
		ring(Vector2(670,305),202,Color(0.9,0.4,0.48,0.55))
		for pair in [[Vector2(675,278),116],[Vector2(823,410),59],[Vector2(510,427),72]]:ruby(pair[0],pair[1])
	if theme==2:
		for r in [120,190,246]:ring(Vector2(647,313),r,Color(0.94,0.32,0.5,0.45))
		for i in 12:
			var p=Vector2(647,313)+Vector2.from_angle(i*TAU/12)*190
			ruby(p,13)
		draw_colored_polygon(PackedVector2Array([Vector2(647,90),Vector2(850,432),Vector2(444,432)]),Color(0.8,0.16,0.3,0.14))
	if theme==3:
		for r in range(258,271):draw_arc(Vector2(480,330),r,-1.9,1.2,80,Color(0.9,0.97,1,0.06),4,true)
		draw_arc(Vector2(480,330),261,-1.9,1.2,80,Color("ebf7ff"),3,true)
	if theme>=4:
		for x in range(0,961,48):draw_line(Vector2(x,0),Vector2(x,600),Color(0.3,0.65,0.84,0.1))
		for y in range(0,601,48):draw_line(Vector2(0,y),Vector2(960,y),Color(0.3,0.65,0.84,0.1))
		ring(Vector2(480,340),220,Color(0.5,0.77,0.92,0.37))
		if theme==5:
			for i in 28:
				var p=Vector2(100+(i*239)%780,90+(i*149)%420)
				draw_line(p,p+Vector2(18,-26),Color(1,0.6,0.22,0.75),2,true)
