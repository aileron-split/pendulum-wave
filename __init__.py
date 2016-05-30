bl_info = {
    "name": "Pendulum Wave Calculator",
    "author": "Davor Bokun, Josip Bokun",
    "version": (0, 2),
    "blender": (2, 74, 0),
    "support": "TESTING",
    "category": "Object",
}

import bpy
from mathutils import *
from math import pi, pow, radians

_GROUP_NAME = 'PendulumWave'
_PIVOT_NAME = _GROUP_NAME + '.Pivot.%03d'
_KUGLA_NAME = _GROUP_NAME + '.Kugla.%03d'
_SPAGA_NAME = _GROUP_NAME + '.Spaga-%d.%03d'
_ALL_PIVOT = _GROUP_NAME + '.Pivot.*'
_ALL_KUGLA = _GROUP_NAME + '.Kugla.*'
_ALL_SPAGA = _GROUP_NAME + '.Spaga-*'

class ObjectPendulumWaveCreate(bpy.types.Operator):
    """Create Pendulum Wave System"""         # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.pendulum_wave_create" # unique identifier for buttons and menu items to reference.
    bl_label = "Create Pendulum Wave System"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}         # enable undo for the operator.

    N = bpy.props.IntProperty(name="Pendulum count", default=16, min=2, max=100)
    ball_size = bpy.props.FloatProperty(name="Ball size", default=0.2, min=0.0)
    spacing = bpy.props.FloatProperty(name="Ball spacing", default=0.3, min=0.0)
    rope_width = bpy.props.FloatProperty(name="Rope width", default=0.003, min=0.0)
    rope_spacing = bpy.props.FloatProperty(name="Rope spacing", default=0.3, min=0.0)

    def execute(self, context):        # execute() is called by blender when running the operator.
        step = self.ball_size + self.spacing
        height = 5.0 * step
        cursor = context.scene.cursor_location
        
        if _GROUP_NAME in bpy.data.groups:
            bpy.ops.object.select_same_group(group=_GROUP_NAME)
            bpy.ops.object.delete()
        else:
            bpy.ops.group.create(name=_GROUP_NAME)
            
        pivot_mesh_transform = Matrix.Translation(Vector((0, self.ball_size / 2.0, 0))) * \
                               Matrix.Scale(self.rope_width * 10.0, 4, Vector((1, 0, 0))) * \
                               Matrix.Scale(self.ball_size, 4, Vector((0, 1, 0))) * \
                               Matrix.Scale(self.rope_spacing, 4, Vector((0, 0, 1)))
                               
        rope_mesh_transform =  Matrix.Rotation(pi/2, 4, 'X') * \
                               Matrix.Translation(Vector((0, 0, -1)))

        
        for i in range(self.N):
            # Kugla
            bpy.ops.mesh.primitive_uv_sphere_add(
                size=self.ball_size / 2.0,
                view_align=False, 
                enter_editmode=False, 
                location=cursor + Vector((0.0, step * i, -height)),
                )
            context.object.name = _KUGLA_NAME % i
            bpy.ops.object.group_link(group=_GROUP_NAME)
            bpy.ops.rigidbody.object_add()
            context.object.rigid_body.linear_damping = 0
            context.object.rigid_body.angular_damping = 0
            
            # Pivot
            bpy.ops.mesh.primitive_cube_add(
                radius=0.5, 
                view_align=False, 
                enter_editmode=False, 
                location=cursor + Vector((0.0, step * i, 0.0)), 
                )
            context.object.name = _PIVOT_NAME % i
            bpy.ops.object.group_link(group=_GROUP_NAME)
            context.object.data.transform(pivot_mesh_transform)
            bpy.ops.rigidbody.object_add()
            context.object.rigid_body.type = 'PASSIVE'
            context.object.rotation_euler = Euler((pi/2.0, 0.0, 0.0), 'XYZ')

            bpy.ops.rigidbody.constraint_add()
            context.object.rigid_body_constraint.type = 'HINGE'
            context.object.rigid_body_constraint.object1 = bpy.data.objects[_PIVOT_NAME % i]
            context.object.rigid_body_constraint.object2 = bpy.data.objects[_KUGLA_NAME % i]
            
            # Spage
            rope_offset = self.rope_spacing / 2.0
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6, 
                radius=self.rope_width, 
                depth=2,
                location=Vector((0, 0, -rope_offset)), 
                )
            context.object.name = _SPAGA_NAME % (1, i)
            context.object.parent = bpy.data.objects[_PIVOT_NAME % i]
            bpy.ops.object.group_link(group=_GROUP_NAME)
            context.object.data.transform(rope_mesh_transform)
            bpy.ops.object.constraint_add(type='STRETCH_TO')
            context.object.constraints["Stretch To"].target = bpy.data.objects[_KUGLA_NAME % i]
            context.object.constraints["Stretch To"].rest_length = 2

            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6, 
                radius=self.rope_width, 
                depth=2,
                location=Vector((0, 0, +rope_offset)), 
                )
            context.object.name = _SPAGA_NAME % (2, i)
            context.object.parent = bpy.data.objects[_PIVOT_NAME % i]
            bpy.ops.object.group_link(group=_GROUP_NAME)
            context.object.data.transform(rope_mesh_transform)
            bpy.ops.object.constraint_add(type='STRETCH_TO')
            context.object.constraints["Stretch To"].target = bpy.data.objects[_KUGLA_NAME % i]
            context.object.constraints["Stretch To"].rest_length = 2

                        
        bpy.ops.object.select_pattern(pattern=_PIVOT_NAME % 0, extend=False)
        context.scene.objects.active = bpy.data.objects[_PIVOT_NAME % 0]

        return {'FINISHED'}            # this lets blender know the operator finished successfully.



class ObjectPendulumWaveCalculate(bpy.types.Operator):
    """Calculate Pendulum Configuration"""        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.pendulum_wave_calculate"  # unique identifier for buttons and menu items to reference.
    bl_label = "Calculate Pendulum Configuration" # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}             # enable undo for the operator.

    T0 = bpy.props.IntProperty(name="Full cycle period", default=16, min=2, max=100)
    scale = bpy.props.FloatProperty(name="Scale", default=2.5)
    bias = bpy.props.FloatProperty(name="Position bias", default=0.0, min=0.0, max=1.0)

    def execute(self, context):        # execute() is called by blender when running the operator.
        if _GROUP_NAME not in bpy.data.groups:
            return {'CANCELLED'}

        N = len([n for n in bpy.data.objects.keys() if n.startswith(_ALL_PIVOT[:-1])])
        
        pivot = bpy.data.objects[_PIVOT_NAME % 0]
        kugla = bpy.data.objects[_KUGLA_NAME % 0]
        distance = (pivot.location - kugla.location).length
     
        origin = pivot.location + Vector((0.0, 0.0, -distance)) * self.bias
        
        for i in range(N):
            pivot = bpy.data.objects[_PIVOT_NAME % i]
            kugla = bpy.data.objects[_KUGLA_NAME % i]
            
            length = self.scale * pow(float(self.T0)/(self.T0+i), 2.0)
            
            pivot.location.z = origin.z + length * self.bias

            kugla.rotation_euler = Euler()
            kugla.location.x = origin.x
            kugla.location.z = origin.z - length * (1.0 - self.bias)

        return {'FINISHED'}            # this lets blender know the operator finished successfully.



class ObjectPendulumWaveInitialize(bpy.types.Operator):
    """Initialize Pendulum Wave System"""         # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.pendulum_wave_initialize" # unique identifier for buttons and menu items to reference.
    bl_label = "Initialize Pendulum Wave System"  # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}             # enable undo for the operator.

    angle = bpy.props.FloatProperty(name="Angle", default=-30.0, min=-90.0, max=90.0)

    def execute(self, context):        # execute() is called by blender when running the operator.
        if _GROUP_NAME not in bpy.data.groups:
            return {'CANCELLED'}

        N = len([n for n in bpy.data.objects.keys() if n.startswith(_ALL_PIVOT[:-1])])
        
        for i in range(N):
            pivot = bpy.data.objects[_PIVOT_NAME % i]
            kugla = bpy.data.objects[_KUGLA_NAME % i]

            distance = (pivot.location - kugla.location).length
            euler = Euler((0.0, radians(self.angle), 0.0), 'XYZ')
            vec = Vector((0.0, 0.0, -distance))
            vec.rotate(euler)
            
            kugla.location = pivot.location + vec
            kugla.rotation_euler = euler

        return {'FINISHED'}            # this lets blender know the operator finished successfully.



def register():
    bpy.utils.register_class(ObjectPendulumWaveCreate)
    bpy.utils.register_class(ObjectPendulumWaveCalculate)
    bpy.utils.register_class(ObjectPendulumWaveInitialize)


def unregister():
    bpy.utils.unregister_class(ObjectPendulumWaveCreate)
    bpy.utils.unregister_class(ObjectPendulumWaveCalculate)
    bpy.utils.unregister_class(ObjectPendulumWaveInitialize)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
