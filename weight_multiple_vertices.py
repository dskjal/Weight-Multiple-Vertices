# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import bpy
import bmesh

bl_info = {
    "name" : "Weight Multiple Vertices",
    "author" : "dskjal",
    "version" : (2, 1),
    "blender" : (2, 83, 5),
    "location" : "View3D > Toolshelf > Item > Weight Multiple Vertices",
    "description" : "This add-on sets the weight to multiple vertices.",
    "warning" : "",
    "wiki_url" : "https://github.com/dskjal/Weight-Multiple-Vertices",
    "tracker_url" : "",
    "category" : "Mesh"
}

num_weight_array = 16
weights = [0.0]*num_weight_array
to_vg_index = [0]*num_weight_array

def set_weight_or_clear(o, weight, vg_index, is_clear=False):
    old_mode = o.mode
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

    vertices_indices = [v.index for v in o.data.vertices if v.select]
    o.vertex_groups[vg_index].add(vertices_indices, weight, 'REPLACE')

    if is_clear:
        old_vg_idx = o.vertex_groups.active_index
        o.vertex_groups.active_index = vg_index
        bpy.ops.object.vertex_group_clean()
        o.vertex_groups.active_index = old_vg_idx

    bpy.ops.object.mode_set(mode=old_mode)

def normalize_weight(o):
    old_mode = o.mode
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    for v in [v for v in o.data.vertices if v.select]:
        sum = 0
        for group in v.groups:
            sum += group.weight
        coeff = 1/sum

        for group in v.groups:
            group.weight *= coeff

    bpy.ops.object.mode_set(mode=old_mode)

class DSKJAL_OT_ClearWeight(bpy.types.Operator):
    bl_idname = 'dskjal.clearweight'
    bl_label = 'Set Weight'
    vg_index : bpy.props.IntProperty(default=0)

    def execute(self, context):
        set_weight_or_clear(bpy.context.active_object, 0, self.vg_index, is_clear=True)
        return {'FINISHED'}

class DSKJAL_PT_WeightMultipleVertices_UI(bpy.types.Panel):
    bl_label = 'Weight Multiple Vertices'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Item'

    @classmethod
    def poll(self, context):
        o = context.object
        return o and o.type == 'MESH' and o.mode in ['EDIT', 'WEIGHT_PAINT']

    def draw(self, context):
        col = self.layout.column()
        obj = bpy.context.active_object
        mesh = obj.data

        num_vertex_group = len(obj.vertex_groups)
        bone_flags = [False] * num_vertex_group
        mean_weights = [[0.0, 0] for i in range(num_vertex_group)]

        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
            deform_layer = bm.verts.layers.deform.active
            for v in [v for v in bm.verts if v.select]:
                for group, weight in v[deform_layer].items():
                    bone_flags[group] = True
                    mean_weights[group][0] += weight
                    mean_weights[group][1] += 1
        else:
            for v in [v for v in mesh.vertices if v.select]:
                for group in v.groups:
                    bone_flags[group.group] = True
                    mean_weights[group.group][0] += group.weight
                    mean_weights[group.group][1] += 1

        # auto normalize
        col.prop(bpy.context.scene, 'dskjal_wmv_auto_normalize', text='Auto Nomalize')
        col.separator()
        col.separator()
        
        global to_vg_index
        global weights
        j = 0
        for i in [i for i in range(num_vertex_group) if bone_flags[i]]:
            row = col.row()
            # clear operator
            ot = row.operator('dskjal.clearweight', text='', icon='CANCEL')
            ot.vg_index = i
            to_vg_index[j] = i

            # vertex group label
            row.label(text=obj.vertex_groups[i].name)

            # weight
            mw = mean_weights[i]
            if mw[1] != 0:
                weights[j] = mw[0]/mw[1]
            row.prop(bpy.context.scene, 'dskjal_weight_array%s' % j, text='')
            j += 1

            if j >= num_weight_array:
                break

for i in range(num_weight_array):
    exec('''
def weight_array_get%s(self):
    global weights
    return weights[%s]

def weight_array_set%s(self, value):
    set_weight_or_clear(bpy.context.active_object, value, to_vg_index[%s], is_clear=False)

    global weights
    weights[%s] = value

    if bpy.context.scene.dskjal_wmv_auto_normalize:
        normalize_weight(bpy.context.active_object)
    return None
    ''' % (i, i, i, i, i))

def register():
    for i in range(num_weight_array):
        exec("bpy.types.Scene.dskjal_weight_array%s = bpy.props.FloatProperty(default=0, min=0, max=1.0, step=5, precision=3, get=weight_array_get%s, set=weight_array_set%s)" % (i, i, i))

    bpy.types.Scene.dskjal_wmv_auto_normalize = bpy.props.BoolProperty(default=False)
    bpy.utils.register_class(DSKJAL_OT_ClearWeight)
    bpy.utils.register_class(DSKJAL_PT_WeightMultipleVertices_UI)

def unregister():
    bpy.utils.unregister_class(DSKJAL_PT_WeightMultipleVertices_UI)
    bpy.utils.unregister_class(DSKJAL_OT_ClearWeight)
    del bpy.types.Scene.dskjal_wmv_auto_normalize
    for i in range(num_weight_array):
        exec("del bpy.types.Scene.dskjal_weight_array%s" % i)

if __name__ == "__main__":
    register()