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
    "version" : (1, 0),
    "blender" : (2, 83, 3),
    "location" : "View3D > Toolshelf > Item > Weight Multiple Vertices",
    "description" : "This add-on sets the weight to multiple vertices.",
    "warning" : "",
    "wiki_url" : "https://github.com/dskjal/Weight-Multiple-Vertices",
    "tracker_url" : "",
    "category" : "Mesh"
}

num_weight_array = 32

class DSKJAL_OT_SetWeight(bpy.types.Operator):
    bl_idname = 'dskjal.setweight'
    bl_label = 'Set Weight'
    vg_index : bpy.props.IntProperty(default=0)
    weight : bpy.props.FloatProperty(default=0.0, min=0.0, max=1.0)
    is_clear : bpy.props.BoolProperty(default=False)

    def execute(self, context):
        o = bpy.context.active_object
        old_mode = o.mode
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        vertices_indices = [v.index for v in o.data.vertices if v.select]
        o.vertex_groups[self.vg_index].add(vertices_indices, self.weight, 'REPLACE')

        if self.is_clear:
            old_vg_idx = o.vertex_groups.active_index
            o.vertex_groups.active_index = self.vg_index
            bpy.ops.object.vertex_group_clean()
            o.vertex_groups.active_index = old_vg_idx

        bpy.ops.object.mode_set(mode=old_mode)

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

        if obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
            deform_layer = bm.verts.layers.deform.active
            for v in [v for v in bm.verts if v.select]:
                for group, weight in v[deform_layer].items():
                    bone_flags[group] = True
        else:
            for v in [v for v in mesh.vertices if v.select]:
                for group in v.groups:
                    bone_flags[group.group] = True

        j = 0
        for i in [i for i in range(num_vertex_group) if bone_flags[i]]:
            row = col.row()
            # clear
            ot = row.operator('dskjal.setweight', text='', icon='CANCEL')
            ot.vg_index = i
            ot.weight = 0
            ot.is_clear = True

            row.label(text=obj.vertex_groups[i].name)

            # set
            row.prop(bpy.context.scene, 'dskjal_weight_array%s' % j, text='')
            ot = row.operator('dskjal.setweight', text='Set')
            ot.weight = eval("bpy.context.scene.dskjal_weight_array%s" % j)
            ot.vg_index = i
            ot.is_clear = False
            j += 1

            if j >= num_weight_array:
                break

def register():
    for i in range(num_weight_array):
        exec("bpy.types.Scene.dskjal_weight_array%s = bpy.props.FloatProperty(default=0, min=0, max=1.0)" % i)

    bpy.utils.register_class(DSKJAL_OT_SetWeight)
    bpy.utils.register_class(DSKJAL_PT_WeightMultipleVertices_UI)

def unregister():
    bpy.utils.unregister_class(DSKJAL_PT_WeightMultipleVertices_UI)
    bpy.utils.unregister_class(DSKJAL_OT_SetWeight)
    for i in range(num_weight_array):
        exec("del bpy.types.Scene.dskjal_weight_array%s" % i)

if __name__ == "__main__":
    register()