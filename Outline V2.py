import maya.cmds as cmds

# Version 2.0: Outline Tool with Enhanced UI

# Global variables
outline_group_name = "outline_group"
use_background_material_name = "useBackground_material"
color_shaders = {}

def set_double_sided(mesh_name):
    attr_name = mesh_name + ".doubleSided"
    try:
        cmds.setAttr(attr_name, 0)
    except Exception as e:
        cmds.warning("Error setting doubleSided attribute for {}: {}".format(mesh_name, str(e)))

def create_outline_mesh(original_mesh, outline_color, translate_z):
    outline_mesh = cmds.duplicate(original_mesh, name=original_mesh + "_outline")[0]
    set_double_sided(outline_mesh)
    
    # Connect output mesh of original mesh to input mesh of outline mesh
    original_shape = cmds.listRelatives(original_mesh, shapes=True)[0]
    outline_shape = cmds.listRelatives(outline_mesh, shapes=True)[0]
    cmds.connectAttr(original_shape + ".outMesh", outline_shape + ".inMesh", force=True)
    
    adjust_outline_mesh(outline_mesh, outline_color, translate_z)
    
    return outline_mesh

def adjust_outline_mesh(outline_mesh, outline_color, translate_z):
    # Set outline color
    outline_shader = create_color_surface_shader(outline_color)
    apply_color_to_group(outline_mesh, outline_shader)

    # Move facets along the local Z-axis with the specified value
    cmds.polyMoveFacet(outline_mesh + ".f[*]", localTranslateZ=translate_z)

    # Calculate normals
    cmds.polyNormal(outline_mesh, normalMode=0)

def create_use_background_material():
    if not cmds.objExists(use_background_material_name):
        shading_node = cmds.shadingNode('useBackground', asShader=True, name=use_background_material_name)
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
        cmds.connectAttr(shading_node + '.outColor', shading_group + '.surfaceShader', force=True)

def apply_use_background_material(mesh_name):
    create_use_background_material()
    try:
        cmds.select(mesh_name)
        cmds.hyperShade(assign=use_background_material_name)
    except Exception as e:
        cmds.warning("Error applying 'Use Background Material': {}".format(str(e)))

def apply_color_to_group(group_name, shader_name):
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
    cmds.connectAttr(shader_name + '.outColor', shading_group + '.surfaceShader', force=True)
    cmds.select(group_name)
    cmds.hyperShade(assign=shader_name)

def create_color_surface_shader(color):
    shader_name = "color_surface_shader_{}".format('_'.join(map(str, color)))
    if shader_name in color_shaders:
        return color_shaders[shader_name]
    
    if cmds.objExists(shader_name):
        shader = shader_name
    else:
        shader = cmds.shadingNode('surfaceShader', asShader=True, name=shader_name)
        cmds.setAttr(shader + ".outColor", color[0], color[1], color[2], type="double3")
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
        cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader", force=True)
        color_shaders[shader_name] = shader
    
    return shader

def create_outline(selected_meshes, translate_z):
    if not cmds.objExists(outline_group_name):
        cmds.group(name=outline_group_name, empty=True)

    outline_color = [1, 0, 0]  # Adjust the outline color here (R, G, B)

    for original_mesh in selected_meshes:
        outline_mesh = create_outline_mesh(original_mesh, outline_color, translate_z)
        cmds.parent(outline_mesh, outline_group_name)
        apply_use_background_material(original_mesh)

def delete_outlines():
    if cmds.objExists(outline_group_name):
        try:
            cmds.delete(outline_group_name)
            if cmds.objExists(use_background_material_name):
                cmds.delete(use_background_material_name)
        except Exception as e:
            cmds.warning("Error deleting outlines: {}".format(str(e)))

    for shader in color_shaders.values():
        if cmds.objExists(shader):
            try:
                cmds.delete(shader)
            except Exception as e:
                cmds.warning("Error deleting shader: {}".format(str(e)))

    global selected_meshes
    for mesh in selected_meshes:
        cmds.select(mesh)
        cmds.hyperShade(assign="lambert1")

    selected_meshes = []

def create_outline_window():
    if cmds.window("outlineWindow", exists=True):
        cmds.deleteUI("outlineWindow", window=True)

    window = cmds.window("outlineWindow", title="Outline Tool 2.0", widthHeight=(300, 260), sizeable=False)
    main_layout = cmds.columnLayout(adjustableColumn=True, parent=window)

    # UI components
    cmds.text(label="Outline Tool", align="center", font="boldLabelFont", parent=main_layout)
    cmds.separator(height=10, style="none", parent=main_layout)

    create_button = cmds.button(label="Create Outline", bgc=[0.2, 0.7, 0.4], command=lambda *args: create_outline(cmds.ls(selection=True), cmds.floatSliderGrp(translateZ_slider, query=True, value=True) * 0.01), parent=main_layout)
    delete_button = cmds.button(label="Delete Outlines", bgc=[0.7, 0.2, 0.4], command="delete_outlines()", parent=main_layout)

    cmds.separator(height=10, style="none", parent=main_layout)

    color_layout = cmds.rowLayout(numberOfColumns=4, columnWidth4=[75, 75, 75, 75], parent=main_layout)
    red_button = cmds.button(label="Red", bgc=[0.8, 0.2, 0.2], command=lambda *args: apply_color_to_group(outline_group_name, create_color_surface_shader([1, 0, 0])), parent=color_layout)
    blue_button = cmds.button(label="Blue", bgc=[0.2, 0.2, 0.8], command=lambda *args: apply_color_to_group(outline_group_name, create_color_surface_shader([0, 0, 1])), parent=color_layout)
    green_button = cmds.button(label="Green", bgc=[0.2, 0.8, 0.2], command=lambda *args: apply_color_to_group(outline_group_name, create_color_surface_shader([0, 1, 0])), parent=color_layout)
    cyan_button = cmds.button(label="Cyan", bgc=[0.2, 0.8, 0.8], command=lambda *args: apply_color_to_group(outline_group_name, create_color_surface_shader([0, 1, 1])), parent=color_layout)

    cmds.separator(height=10, style="none", parent=main_layout)

    cmds.text(label="Outline Thickness", align="center", font="boldLabelFont", parent=main_layout)
    cmds.separator(height=10, style="none", parent=main_layout)

    translateZ_slider = cmds.floatSliderGrp(label="Translate Z", field=True, minValue=1, maxValue=100, fieldMinValue=1, fieldMaxValue=100, value=50, columnWidth3=[100, 40, 160], parent=main_layout)

    # Show the window
    cmds.showWindow(window)

# Create the outline window
create_outline_window()