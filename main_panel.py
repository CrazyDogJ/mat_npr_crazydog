import bpy
import os
from . import helper_functions

class CDNPR_MaterialItem(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material,
    ) # type: ignore

def is_npr_nodetree(nt: bpy.types.ShaderNodeTree) -> bool:
    if nt.type == "SHADER":
        for node in nt.nodes:
            if node.type == "NPR_OUTPUT":
                return True

class CDNPR_NprTreeItem(bpy.types.PropertyGroup):
    npr_tree: bpy.props.PointerProperty(
        name="NPR Node Tree",
        type=bpy.types.ShaderNodeTree,
        poll=lambda self, nt: is_npr_nodetree(nt)
    ) # type: ignore

class CDNPR_UL_MaterialListItem(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ma = item.material

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="")

class CDNPR_PT_MaterialList(bpy.types.Panel):
    bl_label = "Material List"
    bl_idname = "VIEW3D_PT_cdnpr_material_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cd NPR"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        main_col = layout.column(align=True)
        
        box = main_col.box()
        box.label(text="Material List", icon="MATERIAL")
        box = main_col.box()
        box.operator("cdnpr.import_npr_data_chunk", text="Load NPR Trees")
        box_row = box.row(align=True)
        box_main_col = box_row.column(align=True)
        box_main_col.template_list("CDNPR_UL_MaterialListItem", "applying_mats", scene, "cdnpr_mat_items", scene, "cdnpr_mat_index")

        op_col = box_row.column(align=True)
        add_op = op_col.operator("cdnpr.change_selected_material", text="", icon="ADD")
        remove_op = op_col.operator("cdnpr.change_selected_material", text="", icon="REMOVE")

        add_op.add_remove = True
        add_op.target_var = "cdnpr_mat_items"
        add_op.target_index = "cdnpr_mat_index"

        remove_op.add_remove = False
        remove_op.target_var = "cdnpr_mat_items"
        remove_op.target_index = "cdnpr_mat_index"

        row = box_main_col.row(align=True)
        row.operator("cdnpr.collect_mats_from_selected", icon="MATERIAL", text="Collect Materials")

        box = main_col.box()
        box.label(text="Apply NPR Tree", icon="NODE_MATERIAL")
        box = main_col.box()
        prop_item = context.scene.cdnpr_apply_npr
        box.template_ID(prop_item, "npr_tree", new="node.new_node_tree")
        box.operator("cdnpr.apply_npr_tree")

class CDNPR_PT_TransHair(bpy.types.Panel):
    bl_label = "Trans Hair"
    bl_idname = "VIEW3D_PT_cdnpr_trans_hair_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Cd NPR"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        main_col = layout.column(align=True)

        box = main_col.box()
        box.label(text="Transparent Front Hair", icon="MATERIAL")
        box = main_col.box()
        box.operator("cdnpr.setup_scene_hairfront", text="Setup Scene Settings for Trans Hair")

        box.label(text="Under Materials", icon="MATERIAL")
        row = box.row(align=True)
        row.template_list("CDNPR_UL_MaterialListItem", "eyes_mats", scene, "cdnpr_eyes_mat_items", scene, "cdnpr_eyes_mat_index")
        op_col = row.column(align=True)
        add_op = op_col.operator("cdnpr.change_selected_material", text="", icon="ADD")
        remove_op = op_col.operator("cdnpr.change_selected_material", text="", icon="REMOVE")
        op_col.operator("cdnpr.setup_under_mats_hairfront", text="", icon="NODE_MATERIAL")

        add_op.add_remove = True
        add_op.target_var = "cdnpr_eyes_mat_items"
        add_op.target_index = "cdnpr_eyes_mat_index"

        remove_op.add_remove = False
        remove_op.target_var = "cdnpr_eyes_mat_items"
        remove_op.target_index = "cdnpr_eyes_mat_index"

        box.label(text="Hair Material", icon="MATERIAL")
        row = box.row(align=True)
        row.template_list("CDNPR_UL_MaterialListItem", "fronthair_mats", scene, "cdnpr_hair_mat_items", scene, "cdnpr_hair_mat_index")
        op_col = row.column(align=True)
        add_op = op_col.operator("cdnpr.change_selected_material", text="", icon="ADD")
        remove_op = op_col.operator("cdnpr.change_selected_material", text="", icon="REMOVE")
        op_col.operator("cdnpr.setup_hair_mats_hairfront", text="", icon="NODE_MATERIAL")

        add_op.add_remove = True
        add_op.target_var = "cdnpr_hair_mat_items"
        add_op.target_index = "cdnpr_hair_mat_index"

        remove_op.add_remove = False
        remove_op.target_var = "cdnpr_hair_mat_items"
        remove_op.target_index = "cdnpr_hair_mat_index"
        
class CDNPR_OT_ImportDataChunk(bpy.types.Operator):
    bl_idname = "cdnpr.import_npr_data_chunk"
    bl_label = "Import Npr Tree Data Chunk"
    bl_options = {'REGISTER', 'UNDO'}

    current_file = os.path.realpath(__file__)
    addon_root = os.path.dirname(current_file)
    blend_path = os.path.join(addon_root, "Blender_NPR_Lite.blend")
    tree_list = {
        "NPR Tree",
        "NPR Tree_NoLight"
    }

    def execute(self, context):
        for item in self.tree_list:
            if item in bpy.data.node_groups:
                continue
            else:
                with bpy.data.libraries.load(self.blend_path, link=False) as (data_from, data_to):
                    if item in data_from.node_groups and item not in data_to.node_groups:
                        data_to.node_groups = [item]
        return {'FINISHED'}

class CDNPR_OT_CollectMaterialsFromSelected(bpy.types.Operator):
    bl_idname = "cdnpr.collect_mats_from_selected"
    bl_label = "Collect Materials From Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material_list = helper_functions.collect_materials_from_selected_meshes()
        context.scene.cdnpr_mat_items.clear()
        for mat in material_list:
            new_item = context.scene.cdnpr_mat_items.add()
            new_item.material = mat
        return {'FINISHED'}
    
class CDNPR_OT_ApplySelectedNprTree(bpy.types.Operator):
    bl_idname = "cdnpr.apply_npr_tree"
    bl_label = "Apply Selected Npr Tree"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mat_item in context.scene.cdnpr_mat_items:
            for node in mat_item.material.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    node.nprtree = context.scene.cdnpr_apply_npr.npr_tree

        return {'FINISHED'}

class CDNPR_OT_ChangeSelectedMaterial(bpy.types.Operator):
    bl_idname = "cdnpr.change_selected_material"
    bl_label = "Add Selected Material"
    bl_options = {'REGISTER', 'UNDO'}

    target_var: bpy.props.StringProperty() # type: ignore
    target_index: bpy.props.StringProperty() # type: ignore
    add_remove: bpy.props.BoolProperty() # type: ignore

    def execute(self, context):
        scene = context.scene
        target = getattr(scene, self.target_var, None)

        if target is not None and isinstance(target, bpy.types.bpy_prop_collection):
            if self.add_remove:
                active_mat_slot = helper_functions.get_active_material_in_object_mode(context)
                if active_mat_slot:
                    new_item = target.add()
                    new_item.material = active_mat_slot
                    if hasattr(scene, self.target_index):
                        setattr(scene, self.target_index, len(target) - 1)
            else:
                if hasattr(scene, self.target_index):
                    index = getattr(scene, self.target_index)
                    target.remove(index)
                    setattr(scene, self.target_index, max(0, index - 1))

        return {'FINISHED'}

class CDNPR_OT_SetupScene(bpy.types.Operator):
    bl_idname = "cdnpr.setup_scene_hairfront"
    bl_label = "Setup Scene Settings"
    bl_options = {'REGISTER', 'UNDO'}

    hair_front_aov_list = {
        ("Eyes Infront Pass", "COLOR"),
        ("Eyes Pass Enabled", "VALUE"),
        ("Eyes Trans Alpha", "VALUE"),
    }

    current_file = os.path.realpath(__file__)
    addon_root = os.path.dirname(current_file)
    blend_path = os.path.join(addon_root, "Blender_NPR_Lite.blend")
    tree_list = {
        "Hair Pass Group",
        "Under Pass Group"
    }
    
    def execute(self, context):
        props = context.scene.eevee
        props.use_fast_gi = False
        props.use_raytracing = True
        props.ray_tracing_method = "PROBE"

        for item in self.tree_list:
            if item in bpy.data.node_groups:
                continue
            else:
                with bpy.data.libraries.load(self.blend_path, link=False) as (data_from, data_to):
                    if item in data_from.node_groups and item not in data_to.node_groups:
                        data_to.node_groups = [item]

        # 用法例子
        vl = helper_functions.get_view_layer()
        
        for aov_name in self.hair_front_aov_list:
            helper_functions.ensure_aov(vl, aov_name = aov_name[0], aov_type = aov_name[1])
        return {'FINISHED'}
    
class CDNPR_OT_SetupUnderMaterials(bpy.types.Operator):
    bl_idname = "cdnpr.setup_under_mats_hairfront"
    bl_label = "Setup Under Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        group_tree = bpy.data.node_groups.get("Under Pass Group")

        for mat in context.scene.cdnpr_eyes_mat_items:
            source_socket = helper_functions.get_surface_shader_socket(mat.material)
            if not source_socket:
                print("没有连接到 Material Output 的 Shader，无法继续")
                continue

            under_node_group = None
            for n in mat.material.node_tree.nodes:
                if n.type == "GROUP" and n.node_tree == group_tree:
                    under_node_group = n
                    break
                
            if not under_node_group and group_tree:
                under_node_group = mat.material.node_tree.nodes.new("ShaderNodeGroup")
                under_node_group.node_tree = group_tree
                under_node_group.location = (source_socket.node.location.x + 200, source_socket.node.location.y + 200)

            links = mat.material.node_tree.links
            links.new(source_socket, under_node_group.inputs["Shader"])

        return {'FINISHED'}
    
class CDNPR_OT_SetupHairMaterials(bpy.types.Operator):
    bl_idname = "cdnpr.setup_hair_mats_hairfront"
    bl_label = "Setup Hair Materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for mat in context.scene.cdnpr_hair_mat_items:
            mat.material.use_raytrace_refraction = True
            helper_functions.hair_transmission(mat.material)
        return {'FINISHED'}

class_list = {
    CDNPR_MaterialItem,
    CDNPR_NprTreeItem,
    CDNPR_UL_MaterialListItem,
    CDNPR_PT_MaterialList,
    CDNPR_PT_TransHair,
    CDNPR_OT_ImportDataChunk,
    CDNPR_OT_CollectMaterialsFromSelected,
    CDNPR_OT_ApplySelectedNprTree,
    CDNPR_OT_ChangeSelectedMaterial,
    CDNPR_OT_SetupScene,
    CDNPR_OT_SetupUnderMaterials,
    CDNPR_OT_SetupHairMaterials,

}

def register():
    for class_single in class_list:
        bpy.utils.register_class(class_single)

    bpy.types.Scene.cdnpr_mat_items = bpy.props.CollectionProperty(type=CDNPR_MaterialItem)
    bpy.types.Scene.cdnpr_mat_index = bpy.props.IntProperty(default=0)

    bpy.types.Scene.cdnpr_eyes_mat_items = bpy.props.CollectionProperty(type=CDNPR_MaterialItem)
    bpy.types.Scene.cdnpr_eyes_mat_index = bpy.props.IntProperty(default=0)

    bpy.types.Scene.cdnpr_hair_mat_items = bpy.props.CollectionProperty(type=CDNPR_MaterialItem)
    bpy.types.Scene.cdnpr_hair_mat_index = bpy.props.IntProperty(default=0)

    bpy.types.Scene.cdnpr_apply_npr = bpy.props.PointerProperty(type=CDNPR_NprTreeItem)

def unregister():
    for class_single in class_list:
        bpy.utils.unregister_class(class_single)

    del bpy.types.Scene.cdnpr_mat_items
    del bpy.types.Scene.cdnpr_mat_index

    del bpy.types.Scene.cdnpr_eyes_mat_items
    del bpy.types.Scene.cdnpr_eyes_mat_index

    del bpy.types.Scene.cdnpr_hair_mat_items
    del bpy.types.Scene.cdnpr_hair_mat_index

    del bpy.types.Scene.cdnpr_apply_npr