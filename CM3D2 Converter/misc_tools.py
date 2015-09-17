import bpy, bmesh, mathutils

class vertex_group_transfer(bpy.types.Operator):
	bl_idname = 'object.vertex_group_transfer'
	bl_label = "クイック・ウェイト転送"
	bl_description = "アクティブなメッシュに他の選択メッシュの頂点グループを転送します"
	bl_options = {'REGISTER', 'UNDO'}
	
	vertex_group_remove_all = bpy.props.BoolProperty(name="最初に頂点グループ全削除", default=True)
	vertex_group_clean = bpy.props.BoolProperty(name="頂点グループのクリーン", default=True)
	vertex_group_delete = bpy.props.BoolProperty(name="割り当ての無い頂点グループ削除", default=True)
	
	@classmethod
	def poll(cls, context):
		if (len(context.selected_objects) <= 1):
			return False
		source_objs = []
		for obj in context.selected_objects:
			if (obj.type == 'MESH' and context.object.name != obj.name):
				source_objs.append(obj)
		if (len(source_objs) <= 0):
			return False
		for obj in source_objs:
			if (1 <= len(obj.vertex_groups)):
				return True
		return False
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.prop(self, 'vertex_group_remove_all')
		self.layout.prop(self, 'vertex_group_clean')
		self.layout.prop(self, 'vertex_group_delete')
	
	def execute(self, context):
		source_objs = []
		for obj in context.selected_objects:
			if (obj.type == 'MESH' and context.active_object.name != obj.name):
				source_objs.append(obj)
		if (0 < len(context.active_object.vertex_groups) and self.vertex_group_remove_all):
			bpy.ops.object.vertex_group_remove(all=True)
		me = context.active_object.data
		vert_mapping = 'NEAREST'
		for obj in source_objs:
			if (len(obj.data.polygons) <= 0):
				for obj2 in source_objs:
					if (len(obj.data.edges) <= 0):
						break
				else:
					vert_mapping = 'EDGEINTERP_NEAREST'
				break
		else:
			vert_mapping = 'POLYINTERP_NEAREST'
		bpy.ops.object.data_transfer(use_reverse_transfer=True, data_type='VGROUP_WEIGHTS', use_create=True, vert_mapping=vert_mapping, layers_select_src = 'ALL', layers_select_dst = 'NAME')
		if (self.vertex_group_clean):
			bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0, keep_single=False)
		if (self.vertex_group_delete):
			obj = context.active_object
			for vg in obj.vertex_groups:
				for vert in obj.data.vertices:
					try:
						if (vg.weight(vert.index) > 0.0):
							break
					except RuntimeError:
						pass
				else:
					obj.vertex_groups.remove(vg)
		return {'FINISHED'}

class blur_vertex_group(bpy.types.Operator):
	bl_idname = 'object.blur_vertex_group'
	bl_label = "頂点グループぼかし"
	bl_description = "アクティブ、もしくは全ての頂点グループをぼかします"
	bl_options = {'REGISTER', 'UNDO'}
	
	items = [
		('ACTIVE', "アクティブのみ", "", 1),
		('ALL', "全て", "", 2),
		]
	mode = bpy.props.EnumProperty(items=items, name="対象", default='ACTIVE')
	blur_count = bpy.props.IntProperty(name="繰り返し回数", default=10, min=1, max=100, soft_min=1, soft_max=100, step=1)
	use_clean = bpy.props.BoolProperty(name="ウェイト0.0は削除", default=True)
	
	@classmethod
	def poll(cls, context):
		ob = context.active_object
		if ob:
			if ob.type == 'MESH':
				if ob.vertex_groups.active:
					return True
		return False
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		activeObj = context.active_object
		pre_mode = activeObj.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		me = activeObj.data
		target_weights = []
		if (self.mode == 'ACTIVE'):
			target_weights.append(activeObj.vertex_groups.active)
		elif (self.mode == 'ALL'):
			for vg in activeObj.vertex_groups:
				target_weights.append(vg)
		bm = bmesh.new()
		bm.from_mesh(me)
		for count in range(self.blur_count):
			for vg in target_weights:
				vg_index = vg.index
				new_weights = []
				for vert in bm.verts:
					for group in me.vertices[vert.index].groups:
						if (group.group == vg_index):
							my_weight = group.weight
							break
					else:
						my_weight = 0.0
					near_weights = []
					for edge in vert.link_edges:
						for v in edge.verts:
							if (v.index != vert.index):
								edges_vert = v
								break
						for group in me.vertices[edges_vert.index].groups:
							if (group.group == vg_index):
								near_weights.append(group.weight)
								break
						else:
							near_weights.append(0.0)
					near_weight_average = 0
					for weight in near_weights:
						near_weight_average += weight
					try:
						near_weight_average /= len(near_weights)
					except ZeroDivisionError:
						near_weight_average = 0.0
					new_weights.append( (my_weight*2 + near_weight_average) / 3 )
				for vert, weight in zip(me.vertices, new_weights):
					if (self.use_clean and weight <= 0.000001):
						vg.remove([vert.index])
					else:
						vg.add([vert.index], weight, 'REPLACE')
		bm.free()
		bpy.ops.object.mode_set(mode=pre_mode)
		return {'FINISHED'}



# シェイプキー強制転送
class shape_key_transfer_ex(bpy.types.Operator):
	bl_idname = 'object.shape_key_transfer_ex'
	bl_label = "シェイプキー強制転送"
	bl_description = "頂点数の違うメッシュ同士でも一番近い頂点からシェイプキーを強制転送します"
	bl_options = {'REGISTER', 'UNDO'}
	
	items = [
		('VERT', "頂点", "", 1),
		('FACE', "面", "", 2),
		]
	mode = bpy.props.EnumProperty(items=items, name="参照先", default='VERT')
	remove_empty_shape = bpy.props.BoolProperty(name="変形のないシェイプを削除", default=True)
	
	@classmethod
	def poll(cls, context):
		if len(context.selected_objects) != 2:
			return False
		for ob in context.selected_objects:
			if ob.type != 'MESH':
				return False
			if ob.name != context.active_object.name:
				if not ob.data.shape_keys:
					return False
		if context.active_object.mode != 'OBJECT':
			return False
		return True
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def draw(self, context):
		self.layout.prop(self, 'mode')
		self.layout.prop(self, 'remove_empty_shape')
	
	def execute(self, context):
		target_ob = context.active_object
		for ob in context.selected_objects:
			if ob.name != target_ob.name:
				source_ob = ob
		bm = bmesh.new()
		bm.from_mesh(source_ob.data)
		bm.faces.ensure_lookup_table()
		if self.mode == 'FACE':
			kd = mathutils.kdtree.KDTree(len(bm.faces))
			for i, face in enumerate(bm.faces):
				kd.insert(face.calc_center_median(), i)
		elif self.mode == 'VERT':
			kd = mathutils.kdtree.KDTree(len(bm.verts))
			for i, vert in enumerate(bm.verts):
				kd.insert(vert.co.copy(), i)
		kd.balance()
		is_first = True
		for key_block in source_ob.data.shape_keys.key_blocks:
			if is_first:
				is_first = False
				if not target_ob.data.shape_keys:
					target_shape = target_ob.shape_key_add(name=key_block.name, from_mix=False)
				continue
			if key_block.name not in target_ob.data.shape_keys.key_blocks.keys():
				target_shape = target_ob.shape_key_add(name=key_block.name, from_mix=False)
			else:
				target_shape = target_ob.data.shape_keys.key_blocks[key_block.name]
			is_shaped = False
			for target_vert in target_ob.data.vertices:
				if self.mode == 'FACE':
					co, index, dist = kd.find(target_vert.co)
					face = bm.faces[index]
					total_len = 0
					for vert in face.verts:
						vec = target_vert.co - vert.co
						total_len += vec.length
					total_diff = mathutils.Vector((0, 0, 0))
					total_multi = 0
					for vert in face.verts:
						diff = key_block.data[vert.index].co - source_ob.data.vertices[vert.index].co
						multi = total_len - vec.length
						total_diff += diff * multi
						total_multi += multi
					total_diff /= total_multi
				elif self.mode == 'VERT':
					co, index, dist = kd.find(target_vert.co)
					total_diff = key_block.data[index].co - source_ob.data.vertices[index].co
				target_shape.data[target_vert.index].co = target_ob.data.vertices[target_vert.index].co + total_diff
				if not is_shaped and 0.001 <= total_diff.length:
					is_shaped = True
			if not is_shaped and self.remove_empty_shape:
				target_ob.shape_key_remove(target_shape)
		return {'FINISHED'}

# シェイプキーの変形を拡大/縮小
class scale_shape_key(bpy.types.Operator):
	bl_idname = 'object.scale_shape_key'
	bl_label = "シェイプキーの変形を拡大/縮小"
	bl_description = "シェイプキーの変形を強力にしたり、もしくは弱くできます"
	bl_options = {'REGISTER', 'UNDO'}
	
	multi = bpy.props.FloatProperty(name="倍率", description="シェイプキーの拡大率です", default=1.1, min=-10, max=10, soft_min=-10, soft_max=10, step=10, precision=2)
	items = [
		('ACTIVE', "アクティブのみ", "", 1),
		('ALL', "全て", "", 2),
		]
	mode = bpy.props.EnumProperty(items=items, name="対象", default='ACTIVE')
	
	@classmethod
	def poll(cls, context):
		if context.active_object:
			ob = context.active_object
			if ob.type == 'MESH':
				if ob.active_shape_key:
					return True
		return False
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		ob = context.active_object
		me = ob.data
		shape_keys = me.shape_keys
		pre_mode = ob.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		if self.mode == 'ACTIVE':
			target_shapes = [ob.active_shape_key]
		elif self.mode == 'ALL':
			target_shapes = []
			for key_block in shape_keys.key_blocks:
				target_shapes.append(key_block)
		for shape in target_shapes:
			data = shape.data
			for i, vert in enumerate(me.vertices):
				diff = data[i].co - vert.co
				diff *= self.multi
				data[i].co = vert.co + diff
		bpy.ops.object.mode_set(mode=pre_mode)
		return {'FINISHED'}

# シェイプキーをぼかす
class blur_shape_key(bpy.types.Operator):
	bl_idname = 'object.blur_shape_key'
	bl_label = "シェイプキーをぼかす"
	bl_description = "シェイプキーの変形をぼかしてなめらかにします"
	bl_options = {'REGISTER', 'UNDO'}
	
	strength = bpy.props.IntProperty(name="ぼかし強度", description="ぼかしの強度(回数)を設定します", default=10, min=1, max=100, soft_min=1, soft_max=100, step=1)
	items = [
		('ACTIVE', "アクティブのみ", "", 1),
		('ALL', "全て", "", 2),
		]
	mode = bpy.props.EnumProperty(items=items, name="対象", default='ACTIVE')
	
	@classmethod
	def poll(cls, context):
		if context.active_object:
			ob = context.active_object
			if ob.type == 'MESH':
				if ob.active_shape_key:
					return True
		return False
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		ob = context.active_object
		me = ob.data
		shape_keys = me.shape_keys
		bm = bmesh.new()
		bm.from_mesh(me)
		pre_mode = ob.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		if self.mode == 'ACTIVE':
			target_shapes = [ob.active_shape_key]
		elif self.mode == 'ALL':
			target_shapes = []
			for key_block in shape_keys.key_blocks:
				target_shapes.append(key_block)
		for i, vert in enumerate(bm.verts):
			near_verts = []
			for edge in vert.link_edges:
				for v in edge.verts:
					if vert.index != v.index:
						near_verts.append(v)
						break
			for shape in target_shapes:
				for s in range(self.strength):
					data = shape.data
					average = mathutils.Vector((0, 0, 0))
					for v in near_verts:
						average += data[v.index].co - me.vertices[v.index].co
					average /= len(near_verts)
					co = data[i].co - vert.co
					data[i].co = ((co * 2) + average) / 3 + vert.co
		bpy.ops.object.mode_set(mode=pre_mode)
		return {'FINISHED'}

# CM3D2用マテリアルを新規作成
class new_cm3d2(bpy.types.Operator):
	bl_idname = 'material.new_cm3d2'
	bl_label = "CM3D2用マテリアルを新規作成"
	bl_description = "Blender-CM3D2-Converterで使用できるマテリアルを新規で作成します"
	bl_options = {'REGISTER', 'UNDO'}
	
	items = [
		('COMMON', "汎用", "", 1),
		]
	type = bpy.props.EnumProperty(items=items, name="タイプ", default='COMMON')
	
	@classmethod
	def poll(cls, context):
		if not context.material:
			return True
		return False
	
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)
	
	def execute(self, context):
		ob = context.active_object
		ob_names = ob.name.split('.')
		if not context.material_slot:
			bpy.ops.object.material_slot_add()
		mate = context.blend_data.materials.new(ob_names[0])
		context.material_slot.material = mate
		if self.type == 'COMMON':
			mate['shader1'] = 'CM3D2/Toony_Lighted_Outline'
			mate['shader2'] = 'CM3D2__Toony_Lighted_Outline'
			tex_list = [("_MainTex", ob_names[0], r"Assets\texture\texture\***.png")]
			tex_list.append(("_ToonRamp", "toonGrayA1", r"Assets\texture\texture\toon\toonGrayA1.png"))
			tex_list.append(("_ShadowTex", ob_names[0] + "_shadow", r"Assets\texture\texture\***.png"))
			tex_list.append(("_ShadowRateToon", "toonDress_shadow", r"Assets\texture\texture\toon\toonDress_shadow.png"))
			col_list = [("_Color", (1, 1, 1, 1))]
			col_list.append(("_ShadowColor", (0.5, 0.5, 0.5, 1)))
			col_list.append(("_RimColor", (0.5, 0.5, 0.5, 1)))
			col_list.append(("_OutlineColor", (1, 1, 1, 1)))
			col_list.append(("_ShadowColor", (0.5, 0.5, 0.5, 1)))
			f_list = [("_Shininess", 0)]
			f_list.append(("_OutlineWidth", 0.002))
			f_list.append(("_RimPower", 25))
			f_list.append(("_RimShift", 0))
		slot_count = 0
		for data in tex_list:
			slot = mate.texture_slots.create(slot_count)
			tex = context.blend_data.textures.new(data[0], 'IMAGE')
			slot.texture = tex
			slot.color = [0, 0, 1]
			img = context.blend_data.images.new(data[1], 128, 128)
			img.filepath = data[2]
			img.source = 'FILE'
			tex.image = img
			slot_count += 1
		for data in col_list:
			slot = mate.texture_slots.create(slot_count)
			mate.use_textures[slot_count] = False
			slot.color = data[1][:3]
			slot.diffuse_color_factor = data[1][3]
			slot.use_rgb_to_intensity = True
			tex = context.blend_data.textures.new(data[0], 'IMAGE')
			slot.texture = tex
			slot_count += 1
		for data in f_list:
			slot = mate.texture_slots.create(slot_count)
			mate.use_textures[slot_count] = False
			slot.diffuse_color_factor = data[1]
			tex = context.blend_data.textures.new(data[0], 'IMAGE')
			slot.texture = tex
			slot_count += 1
		return {'FINISHED'}

# 頂点グループメニューに項目追加
def MESH_MT_vertex_group_specials(self, context):
	self.layout.separator()
	self.layout.operator(vertex_group_transfer.bl_idname, icon='SPACE2')
	self.layout.operator(blur_vertex_group.bl_idname, icon='SPACE2')

# シェイプメニューに項目追加
def MESH_MT_shape_key_specials(self, context):
	self.layout.separator()
	self.layout.operator(shape_key_transfer_ex.bl_idname, icon='SPACE2')
	self.layout.operator(scale_shape_key.bl_idname, icon='SPACE2')
	self.layout.operator(blur_shape_key.bl_idname, icon='SPACE2')

# マテリアルタブに項目追加
def MATERIAL_PT_context_material(self, context):
	if not context.material:
		self.layout.operator(new_cm3d2.bl_idname, icon='SPACE2')