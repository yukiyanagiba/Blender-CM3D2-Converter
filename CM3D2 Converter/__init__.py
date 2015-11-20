﻿# アドオンを読み込む時に最初にこのファイルが読み込まれます

# アドオン情報
bl_info = {
	"name" : "CM3D2 Converter",
	"author" : "",
	"version" : (0, 1),
	"blender" : (2, 7),
	"location" : "ファイル > インポート/エクスポート > CM3D2 Model (.model)",
	"description" : "カスタムメイド3D2の専用ファイルのインポート/エクスポートを行います",
	"warning" : "",
	"wiki_url" : "https://github.com/CM3Duser/Blender-CM3D2-Converter",
	"tracker_url" : "http://jbbs.shitaraba.net/bbs/subject.cgi/game/55179/?q=%A1%D6%A5%AB%A5%B9%A5%BF%A5%E0%A5%E1%A5%A4%A5%C93D2%A1%D7%B2%FE%C2%A4%A5%B9%A5%EC%A5%C3%A5%C9",
	"category" : "Import-Export"
}

# サブスクリプト群をインポート
if "bpy" in locals():
	import imp
	imp.reload(model_import)
	imp.reload(model_export)
	
	imp.reload(tex_import)
	imp.reload(tex_export)
	
	imp.reload(mate_import)
	imp.reload(mate_export)
	
	imp.reload(misc_tools)
else:
	from . import model_import
	from . import model_export
	
	from . import tex_import
	from . import tex_export
	
	from . import mate_import
	from . import mate_export
	
	from . import misc_tools
import bpy, os.path, bpy.utils.previews

# アドオン設定
class AddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __name__
	
	scale = bpy.props.FloatProperty(name="倍率", description="Blenderでモデルを扱うときの拡大率", default=5, min=0.01, max=100, soft_min=0.01, soft_max=100, step=10, precision=2)
	
	model_import_path = bpy.props.StringProperty(name="modelインポート時のデフォルトパス", subtype='FILE_PATH', description="modelインポート時に最初はここが表示されます、インポート毎に保存されます")
	model_export_path = bpy.props.StringProperty(name="modelエクスポート時のデフォルトパス", subtype='FILE_PATH', description="modelエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")
	
	tex_import_path = bpy.props.StringProperty(name="texインポート時のデフォルトパス", subtype='FILE_PATH', description="texインポート時に最初はここが表示されます、インポート毎に保存されます")
	tex_export_path = bpy.props.StringProperty(name="texエクスポート時のデフォルトパス", subtype='FILE_PATH', description="texエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")
	
	mate_import_path = bpy.props.StringProperty(name="mateインポート時のデフォルトパス", subtype='FILE_PATH', description="mateインポート時に最初はここが表示されます、インポート毎に保存されます")
	mate_export_path = bpy.props.StringProperty(name="mateエクスポート時のデフォルトパス", subtype='FILE_PATH', description="mateエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")
	
	backup_ext = bpy.props.StringProperty(name="バックアップの拡張子 (空欄で無効)", description="エクスポート時にバックアップを作成時この拡張子で複製します、空欄でバックアップを無効", default='bak')
	
	kiss_icon_value = bpy.props.IntProperty()
	
	def draw(self, context):
		box = self.layout.box()
		box.label(text="modelファイル", icon_value=bpy.context.user_preferences.addons[__name__].preferences.kiss_icon_value)
		box.prop(self, 'scale', icon='MAN_SCALE')
		box.prop(self, 'model_import_path', icon='IMPORT', text="インポート時デフォルトパス")
		box.prop(self, 'model_export_path', icon='EXPORT', text="エクスポート時デフォルトパス")
		box = self.layout.box()
		box.label(text="texファイル", icon='FILE_IMAGE')
		box.prop(self, 'tex_import_path', icon='IMPORT', text="インポート時デフォルトパス")
		box.prop(self, 'tex_export_path', icon='EXPORT', text="エクスポート時デフォルトパス")
		box = self.layout.box()
		box.label(text="mateファイル", icon='MATERIAL')
		box.prop(self, 'mate_import_path', icon='IMPORT', text="インポート時デフォルトパス")
		box.prop(self, 'mate_export_path', icon='EXPORT', text="エクスポート時デフォルトパス")
		self.layout.prop(self, 'backup_ext', icon='FILE_BACKUP')
		row = self.layout.row()
		row.operator('script.update_cm3d2_converter', icon='FILE_REFRESH')
		row.menu('INFO_MT_help_CM3D2_Converter_RSS', icon='INFO')

# プラグインをインストールしたときの処理
def register():
	bpy.utils.register_module(__name__)
	
	bpy.types.INFO_MT_file_import.append(model_import.menu_func)
	bpy.types.INFO_MT_file_export.append(model_export.menu_func)
	
	bpy.types.IMAGE_MT_image.append(tex_import.menu_func)
	bpy.types.IMAGE_MT_image.append(tex_export.menu_func)
	
	bpy.types.TEXT_MT_text.append(mate_import.TEXT_MT_text)
	bpy.types.TEXT_MT_text.append(mate_export.TEXT_MT_text)
	
	bpy.types.INFO_MT_help.append(misc_tools.INFO_MT_help)
	bpy.types.MESH_MT_vertex_group_specials.append(misc_tools.MESH_MT_vertex_group_specials)
	bpy.types.MESH_MT_shape_key_specials.append(misc_tools.MESH_MT_shape_key_specials)
	bpy.types.MATERIAL_PT_context_material.append(misc_tools.MATERIAL_PT_context_material)
	bpy.types.DATA_PT_context_arm.append(misc_tools.DATA_PT_context_arm)
	bpy.types.TEXTURE_PT_context_texture.append(misc_tools.TEXTURE_PT_context_texture)
	bpy.types.OBJECT_PT_context_object.append(misc_tools.OBJECT_PT_context_object)
	bpy.types.DATA_PT_modifiers.append(misc_tools.DATA_PT_modifiers)
	bpy.types.TEXT_HT_header.append(misc_tools.TEXT_HT_header)
	
	pcoll = bpy.utils.previews.new()
	dir = os.path.dirname(__file__)
	pcoll.load('KISS', os.path.join(dir, "kiss.png"), 'IMAGE')
	bpy.context.user_preferences.addons[__name__].preferences.kiss_icon_value = pcoll['KISS'].icon_id

# プラグインをアンインストールしたときの処理
def unregister():
	bpy.utils.unregister_module(__name__)
	
	bpy.types.INFO_MT_file_import.remove(model_import.menu_func)
	bpy.types.INFO_MT_file_export.remove(model_export.menu_func)
	
	bpy.types.IMAGE_MT_image.remove(tex_import.menu_func)
	bpy.types.IMAGE_MT_image.remove(tex_export.menu_func)
	
	bpy.types.TEXT_MT_text.remove(mate_import.TEXT_MT_text)
	bpy.types.TEXT_MT_text.remove(mate_export.TEXT_MT_text)
	
	bpy.types.INFO_MT_help.remove(misc_tools.INFO_MT_help)
	bpy.types.MESH_MT_shape_key_specials.remove(misc_tools.MESH_MT_shape_key_specials)
	bpy.types.MESH_MT_vertex_group_specials.remove(misc_tools.MESH_MT_vertex_group_specials)
	bpy.types.MATERIAL_PT_context_material.remove(misc_tools.MATERIAL_PT_context_material)
	bpy.types.DATA_PT_context_arm.remove(misc_tools.DATA_PT_context_arm)
	bpy.types.TEXTURE_PT_context_texture.remove(misc_tools.TEXTURE_PT_context_texture)
	bpy.types.OBJECT_PT_context_object.remove(misc_tools.OBJECT_PT_context_object)
	bpy.types.DATA_PT_modifiers.remove(misc_tools.DATA_PT_modifiers)
	bpy.types.TEXT_HT_header.remove(misc_tools.TEXT_HT_header)

# メイン関数
if __name__ == "__main__":
	register()
