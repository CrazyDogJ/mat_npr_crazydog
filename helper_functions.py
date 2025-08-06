import bpy

def collect_materials_from_selected_meshes():
    mats = {slot.material for obj in bpy.context.selected_objects
            if obj.type == "MESH"
            for slot in obj.material_slots
            if slot.material is not None}

    material_list: list[bpy.types.Material] = list(mats)
    return material_list

def get_active_material_in_object_mode(context):
    obj = context.object
    if not obj or obj.type != "MESH":
        return None

    mat = None
    idx = getattr(obj, "active_material_index", 0)
    if obj.material_slots and 0 <= idx < len(obj.material_slots):
        mat = obj.material_slots[idx].material
        
    return mat

def get_view_layer():
    return bpy.context.view_layer  # 或者指定：bpy.context.scene.view_layers["View Layer"]

def has_aov(view_layer, aov_name: str) -> bool:
    for aov in view_layer.aovs:
        if aov.name == aov_name:
            return True
    return False

def ensure_aov(view_layer, aov_name: str, aov_type: str):
    for aov in view_layer.aovs:
        if aov.name == aov_name:
            return aov  # 已存在

    new_aov = view_layer.aovs.add()
    new_aov.name = aov_name
    new_aov.type = aov_type

    return new_aov

def get_surface_shader_socket(material):
    if not material.use_nodes:
        return None

    nt = material.node_tree
    output_node = None
    for node in nt.nodes:
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
            break
    if not output_node:
        return None

    surface_input = output_node.inputs.get("Surface")
    if not surface_input or not surface_input.is_linked:
        return None

    link = surface_input.links[0]  # 取第一个连接
    return link.from_socket  # 就是接到 Surface 的输出 socket

def connect_shader_to_aov(material, aov_name):
    nt = material.node_tree
    nodes = nt.nodes
    links = nt.links

    source_socket = get_surface_shader_socket(material)
    if not source_socket:
        print("没有连接到 Material Output 的 Shader，无法继续")
        return

    # 确保 Shader to RGB 节点
    shader_to_rgb = None
    for n in nodes:
        if n.type == "SHADER_TO_RGB":
            shader_to_rgb = n
            break
    if not shader_to_rgb:
        shader_to_rgb = nodes.new("ShaderNodeShaderToRGB")
        shader_to_rgb.location = (source_socket.node.location.x + 200, source_socket.node.location.y)

    # 确保 AOV 输出节点
    aov_node = None
    for n in nodes:
        if n.type == "AOV_OUTPUT" and n.aov_name == aov_name:
            aov_node = n
            break
    if not aov_node:
        aov_node = nodes.new("ShaderNodeOutputAOV")
        aov_node.location = (shader_to_rgb.location.x + 200, shader_to_rgb.location.y - 200)
        aov_node.aov_name = aov_name

    # 建立连接
    links.new(source_socket, shader_to_rgb.inputs["Shader"])
    links.new(shader_to_rgb.outputs["Color"], aov_node.inputs["Color"])

    print(f"✔ 材质 {material.name} 的输出已连接 ShaderToRGB → AOV '{aov_name}'")

def new_aov(material, aov_name):
    nt = material.node_tree
    nodes = nt.nodes

    source_socket = get_surface_shader_socket(material)
    if not source_socket:
        print("没有连接到 Material Output 的 Shader，无法继续")
        return

    # 确保 AOV 输出节点
    aov_node = None
    for n in nodes:
        if n.type == "AOV_OUTPUT" and n.aov_name == aov_name:
            aov_node = n
            break
    if not aov_node:
        aov_node = nodes.new("ShaderNodeOutputAOV")
        aov_node.location = (source_socket.node.location.x + 200, source_socket.node.location.y - 400)
        aov_node.aov_name = aov_name
        aov_node.inputs["Value"].default_value = 1.0

def hair_transmission(material):
    nt = material.node_tree
    nodes = nt.nodes
    links = nt.links

    source_socket = get_surface_shader_socket(material)
    if not source_socket:
        print("没有连接到 Material Output 的 Shader，无法继续")
        return

    refrac_node = None
    for n in nodes:
        if n.type == "BSDF_REFRACTION":
            refrac_node = n
            break
    if not refrac_node:
        refrac_node = nodes.new("ShaderNodeBsdfRefraction")
        refrac_node.location = (source_socket.node.location.x + 200, source_socket.node.location.y + 200)
        refrac_node.inputs["IOR"].default_value = 1.0

    mix_shader_node = None
    for n in nodes:
        if n.type == "MIX_SHADER":
            mix_shader_node = n
            break
    if not mix_shader_node:
        mix_shader_node = nodes.new("ShaderNodeMixShader")
        mix_shader_node.location = (source_socket.node.location.x + 200, source_socket.node.location.y)
        mix_shader_node.inputs["Fac"].default_value = 0.99999

    mat_output = None
    for n in nodes:
        if n.type == "OUTPUT_MATERIAL":
            mat_output = n
            break
    # 建立连接
    links.new(source_socket, mix_shader_node.inputs[2])
    links.new(refrac_node.outputs["BSDF"], mix_shader_node.inputs[1])
    links.new(mix_shader_node.outputs["Shader"], mat_output.inputs["Surface"])