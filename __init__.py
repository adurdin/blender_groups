bl_info = {
    'name': 'FnGroups',
    'author': 'vfig',
    'version': (0, 0, 1),
    'blender': (2, 80, 0),
    'category': '(Development)',
    'description': '(in development)'
}

import bpy
from mathutils import Vector

# Bug: my keybind isn't working. Figure out why later.
# 'Enter group' operator: create (if not exist) a new Scene; put the group contents into it; activate it.
#                         PROBLEM: adding new objects into that group MUST go into the group. Can we make
#                                  the master collection for that scene the instanced collection? Or do we
#                                  need to do shenanigans like changing the instanced collection, or always
#                                  creating the scene (and having the enter op just activate it)?
# 'Exit group' operator: remove (if exist) the scene for the group.

class GroupOperator(bpy.types.Operator):
    """Group selected objects."""
    bl_idname = "object.group"
    bl_label = "Group Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        group_selected_objects(context)
        return {'FINISHED'}

    # TODO: have a property for the group name
    # TODO: a dialog for the group name, maybe? No: just let it be post-edited or renamed

class UngroupOperator(bpy.types.Operator):
    """Ungroup selected group."""
    bl_idname = "object.ungroup"
    bl_label = "Ungroup Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        o = context.active_object
        return (o is not None and o.get('is_fngroup', False))

    def execute(self, context):
        ungroup_active_object(context)
        return {'FINISHED'}

def group_selected_objects(context):
    """To make a group, we must:
    - Derive a group name from the active object
    - Note the world-space location of the active object; this is the group origin
    - Make a new Collection, named 'Group: group name'
    - Add all the objects to that collection
    - Remove all the objects from context.collection
    - (if necessary) adjust all object locations to account for group origin
    - Create a new Empty that is a instanced collection for the group collection
    - Position the empty at the group origin.
    - Name the empty for the group name
    - Add the empty to context.collection
    - Deselect everything, select and make active the empty
    - ... profit?
    """
    # TODO: make sure this works for subgroups?
    o = context.active_object
    name_base = o.name
    group_origin = Vector(o.location)
    inst_name = f"{name_base} and friends"
    coll_name = f"Group: {inst_name}"
    selected_objects = list(context.selected_objects)
    active_collection = context.view_layer.active_layer_collection.collection
    # Create the group empty and its collection.
    print(f"Grouping {selected_objects} into {inst_name}...")
    coll = bpy.data.collections.new(coll_name)
    inst = bpy.data.objects.new(inst_name, None)
    inst.instance_collection = coll
    inst.instance_type = 'COLLECTION'
    inst.location = group_origin
    inst['is_fngroup'] = True
    active_collection.objects.link(inst)
    # Move the selected objects into the group.
    for o in selected_objects:
        # FIXME: should this use the active object's transform?
        o.location = Vector(o.location) - group_origin
        coll.objects.link(o)
        active_collection.objects.unlink(o)
    # Select only the group.
    for o in selected_objects:
        o.select_set(False)
    inst.select_set(True)
    bpy.context.view_layer.objects.active = inst

def ungroup_active_object(context):
    # TODO: should work on multiple groups if multiple groups are selected, right?
    inst = context.active_object
    coll = inst.instance_collection
    group_origin = Vector(inst.location)
    active_collection = context.view_layer.active_layer_collection.collection
    contained_objects = list(coll.objects)
    # Move the contents out of the group.
    for o in contained_objects:
        # FIXME: this should almost certainly use the empty's transform!
        o.location = Vector(o.location) + group_origin
        active_collection.objects.link(o)
        coll.objects.unlink(o)
    # Remove the group empty.
    active_collection.objects.unlink(inst)
    # Select the ungrouped objects.
    for o in contained_objects:
        o.select_set(True)
    inst.select_set(False)
    bpy.context.view_layer.objects.active = contained_objects[0]

def register():
    bpy.utils.register_class(GroupOperator)
    bpy.utils.register_class(UngroupOperator)

def unregister():
    bpy.utils.unregister_class(GroupOperator)
    bpy.utils.unregister_class(UngroupOperator)
