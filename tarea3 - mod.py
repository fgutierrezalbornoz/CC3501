import pyglet
from OpenGL import GL
import numpy as np
import sys
from Box2D import b2PolygonShape, b2World
import grafica.transformations as tr

if sys.path[0] != "":
    sys.path.insert(0, "")
sys.path.append('../../')

import auxiliares.utils.shapes as shapes
from auxiliares.utils.camera import FreeCamera
from auxiliares.utils.scene_graph import SceneGraph
from auxiliares.utils.drawables import Model, DirectionalLight, PointLight, SpotLight, Material
from auxiliares.utils.helpers import init_axis, init_pipeline, mesh_from_file, get_path

WIDTH = 720
HEIGHT = 720

#--------------------------------------------------------------------------------------
# Controller
#--------------------------------------------------------------------------------------
class Controller(pyglet.window.Window):
    def __init__(self, title, *args, **kargs):
        super().__init__(*args, **kargs)
        self.set_minimum_size(240, 240) # Evita error cuando se redimensiona a 0
        self.set_caption(title)
        # self.key_handler = pyglet.window.key.KeyStateHandler()
        # self.push_handlers(self.key_handler)
        self.keys_state = {}
        self.program_state = { 
            "total_time": 0.0, 
            "camera": None,
            "bodies": {},
            "world": None,
            "vel_iters": 6,
            "pos_iters": 2 }
        self.init()

    def init(self):
        GL.glClearColor(1, 1, 1, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CCW)

    def is_key_pressed(self, key):
        return self.keys_state.get(key, False)

    def on_key_press(self, symbol, modifiers):
        controller.keys_state[symbol] = True
        super().on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        controller.keys_state[symbol] = False

#--------------------------------------------------------------------------------------
# Definición clases para la escena
#--------------------------------------------------------------------------------------

class Car_info():
    def __init__(self, chassis, front_wheels, rear_wheels, spare_wheels=None, i=0):
        self.car_number = i
        self.chassis_mesh = mesh_from_file(chassis)[0]["mesh"]
        self.chassis_position = [0,0,0]
        self.chassis_scale = [1,1,1]
        self.chassis_material = None
        self.front_wheels_mesh = mesh_from_file(front_wheels)[0]["mesh"]
        self.front_wheels_position = [0,0,0]
        self.front_wheels_scale = [1,1,1]
        self.front_wheels_material = None
        self.rear_wheels_mesh = mesh_from_file(rear_wheels)[0]["mesh"]
        self.rear_wheels_position = [0,0,0]
        self.rear_wheels_scale = [1,1,1]
        self.rear_wheels_material = None
        self.spare_wheels_mesh=None
        if spare_wheels is not None:
            self.spare_wheels_mesh = mesh_from_file(spare_wheels)[0]["mesh"]
        self.spare_wheels_position = [0,0,0]
        self.spare_wheels_scale = [1,1,1]
        self.spare_wheels_material = None
        
            

class Platform_info():
    def __init__(self, platform):
        self.mesh = mesh_from_file(platform)[0]["mesh"]
        self.position = [0,0,0]
        self.scale = [1,1,1]
        self.material = None
        
class Car():
    def __init__(self, car, platform, graph, pos=[0,0,0],with_platform=True):
        i=car.car_number
        graph.add_node("car_system_"+str(i),position=pos)
        if with_platform:
            graph.add_node("platform_"+str(i), attach_to="car_system_"+str(i),mesh=platform.mesh, 
                        pipeline=color_mesh_lit_pipeline, material=platform.material, 
                        scale=platform.scale)
            graph.add_node("spotlight_"+str(i),
                       attach_to="platform_"+str(i),
                   pipeline=color_mesh_lit_pipeline,
                   position=[0, 0.8, 0],
                   rotation=[-np.pi/2, 0, 0],
                   light=SpotLight(
                          diffuse = [1, 1, 1],
                          specular = [1, 1, 1],
                          ambient = [0.15, 0.15, 0.15],
                          cutOff = 0.91, # siempre mayor a outerCutOff
                          outerCutOff = 0.82
                   )
            )
        # car.chassis_position=[car.chassis_position[0]+pos[0], car.chassis_position[1]+pos[1], car.chassis_position[2]+pos[2]]
        car.chassis_position=[car.chassis_position[0]+pos[0], car.chassis_position[1]+pos[1]+0.24, car.chassis_position[2]+pos[2]]
        car.front_wheels_position=[car.chassis_position[0]+car.front_wheels_position[0], car.chassis_position[1]+car.front_wheels_position[1], car.chassis_position[2]+car.front_wheels_position[2]]
        #car.front_wheels_position=[car.front_wheels_position[0], car.front_wheels_position[1], car.front_wheels_position[2]]
        car.rear_wheels_position=[car.chassis_position[0]+car.rear_wheels_position[0], car.chassis_position[1]+car.rear_wheels_position[1], car.chassis_position[2]+car.rear_wheels_position[2]]
        rotation=[0,0,0]
        graph.add_node("chassis_"+str(i),mesh=car.chassis_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.chassis_scale,material=car.chassis_material, 
                       position = car.chassis_position, rotation=rotation)
        graph.add_node("front_wheels_"+str(i), mesh=car.front_wheels_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.front_wheels_scale, material=car.front_wheels_material, 
                       position = car.front_wheels_position,rotation=rotation)
        
        graph.add_node("rear_wheels_"+str(i), mesh=car.rear_wheels_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.rear_wheels_scale, material=car.rear_wheels_material, 
                       position = car.rear_wheels_position, rotation=rotation)
        if car.spare_wheels_mesh is not None:
            car.spare_wheels_position=[car.chassis_position[0]+car.spare_wheels_position[0], car.chassis_position[1]+car.spare_wheels_position[1], car.chassis_position[2]+car.spare_wheels_position[2]]
            graph.add_node("spare_wheels_"+str(i), mesh=car.spare_wheels_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.spare_wheels_scale, material=car.spare_wheels_material, 
                       position = car.spare_wheels_position, rotation=rotation)
        

    def draw(self):
        self.graph.draw()

#--------------------------------------------------------------------------------------
# Configuración Previa
#--------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Instancia del controller
    controller = Controller("Tarea 3", width=WIDTH, height=HEIGHT, resizable=True)

    controller.program_state["camera"] = FreeCamera([2, 1.5, 2], "perspective")
    controller.program_state["camera"].yaw = -np.pi / 2#-3* np.pi/ 4
    controller.program_state["camera"].pitch = -np.pi / 4

    axis_scene = init_axis(controller)
    
    color_mesh_lit_pipeline = init_pipeline(
        get_path("auxiliares/shaders/color_mesh_lit.vert"),
        get_path("auxiliares/shaders/color_mesh_lit.frag"))

    cube = Model(shapes.Cube["position"], shapes.Cube["uv"], shapes.Cube["normal"], index_data=shapes.Cube["indices"])
    quad = Model(shapes.Square["position"], shapes.Square["uv"], shapes.Square["normal"], index_data=shapes.Square["indices"])
    graph = SceneGraph(controller)

#--------------------------------------------------------------------------------------
# Materiales
#--------------------------------------------------------------------------------------

#http://devernay.free.fr/cours/opengl/materials.html

    sh = 128
    material = Material(
        diffuse = [138/255,43/255,226/255],
        specular = [1, 1, 1],
        ambient = [138/255,43/255,226/255],
        shininess = sh * 1)
    
    silver = Material(
        diffuse = [0.50754, 0.50754, 0.50754],
        specular = [0.508273, 0.508273, 0.508273],
        ambient = [0.19225, 0.19225, 0.19225],
        shininess = sh*0.4)
    
    rubber = Material(
        diffuse = [0.01, 0.01, 0.01],
        specular = [0.4, 0.4, 0.4],
        ambient = [0.02, 0.02, 0.02],
        shininess = sh*0.078125)
    
    gold = Material(
        diffuse = [0.75164, 0.60648, 0.22648],
        specular = [0.628281, 0.555802, 0.366065],
        ambient = [0.24725, 0.1995, 0.0745],
        shininess = sh*0.4)
    
    pearl = Material(
        diffuse = [1, 0.829, 0.829],
        specular = [0.296648, 0.296648, 0.296648],
        ambient = [0.25, 0.20725, 0.20725], 
        shininess = sh* 0.088)
    
    emerald = Material(
        diffuse = [0.07568, 0.61424, 0.07568],
        specular =	[0.633, 0.727811, 0.633],
        ambient	= [0.0215, 0.1745, 0.0215],
        shininess = sh *0.6)
    
    obsidian = Material(
        diffuse = [0.18275, 0.17, 0.22525],
        specular =	[0.332741, 0.328634, 0.346435],
        ambient	= [	0.05375, 0.05, 0.06625],
        shininess = sh *0.3)
    
    chrome = Material(
        diffuse = [0.4, 0.4, 0.4],
        specular =	[0.774597, 0.774597, 0.774597],
        ambient	= [0.25, 0.25, 0.25],
        shininess = sh *0.6)
    
    cooper = Material(
        diffuse = [0.7038, 0.27048, 0.0828],
        specular =	[0.256777, 0.137622, 0.086014],
        ambient	= [0.19125, 0.0735, 0.0225],
        shininess = sh *0.1)
    
    ruby = Material(
        diffuse = [0.61424, 0.04136, 0.04136],
        specular =	[0.727811, 0.626959, 0.626959],
        ambient	= [0.1745, 0.01175, 0.01175],
        shininess = sh *0.6)


#--------------------------------------------------------------------------------------
# Configuración de la geometría de la escena
#--------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------
# Plataforma
#--------------------------------------------------------------------------------------

    platform = Platform_info("tareas/Tarea 2 entregada/circular_platform.stl")

    platform.material=obsidian
    platform.position=[0,0,0]
    platform.scale=[2,2,2]

#--------------------------------------------------------------------------------------
# Autos
#--------------------------------------------------------------------------------------

#Seteo mean machine

    car_0=Car_info("tareas/Tarea 2 entregada/mean_machine_chassis.stl", 
             "tareas/Tarea 2 entregada/mean_machine_front_wheels.stl", 
             "tareas/Tarea 2 entregada/mean_machine_rear_wheels.stl", i=0)
    
    car_0.rear_wheels_material=rubber
    car_0.front_wheels_material=rubber
    car_0.chassis_material=material
    car_0.chassis_position=[0.2,0.09,0]
    car_0.front_wheels_position=[-0.635,-0.19,0]
    car_0.front_wheels_scale=[0.2,0.2,0.2]
    car_0.rear_wheels_position=[0.075,-0.19,0]
    car_0.rear_wheels_scale=[0.3,0.3,0.3]

    Car(car_0, platform, graph, pos=[0,0,0], with_platform=False)

# Seteo army surplus special


    car_1=Car_info("tareas/Tarea 2 entregada/army_surplus_special_chassis.stl", 
             "tareas/Tarea 2 entregada/army_surplus_special_front_wheels.stl", 
             "tareas/Tarea 2 entregada/army_surplus_special_rear_wheels.stl", i=1)
    
    car_1.rear_wheels_material=rubber
    car_1.front_wheels_material=rubber
    car_1.chassis_material=emerald
    car_1.chassis_position=[-0.125,0.335,0]
    car_1.front_wheels_position=[-0.673,-0.423,0]
    car_1.front_wheels_scale=[0.2,0.2,0.2]
    car_1.rear_wheels_position=[-0.08,-0.37,0]
    car_1.rear_wheels_scale=[0.5,0.5,0.5]

    # Car(car_1, platform, graph, pos=[-2,0,0])
    # Car(car_1, platform, graph, pos=[-2,0,0], with_platform=False)
    
    
    
    # Car(car_1, platform, graph, pos=[0,0,0], with_platform=False)

#Seteo turbo terrific

    car_2=Car_info("tareas/Tarea 2 entregada/turbo_terrific_chassis.stl", 
             "tareas/Tarea 2 entregada/turbo_terrific_front_wheels.stl", 
             "tareas/Tarea 2 entregada/turbo_terrific_rear_wheels.stl", i=2)
    
    car_2.rear_wheels_material=rubber
    car_2.front_wheels_material=rubber
    car_2.chassis_material=ruby
    car_2.chassis_position=[0.025,-0.045,0]
    car_2.front_wheels_position=[-0.4,-0.062,0]
    car_2.front_wheels_scale=[0.225,0.225,0.225]
    car_2.rear_wheels_position=[0.462,0.052,0]
    car_2.rear_wheels_scale=[0.42,0.42,0.42]

    # Car(car_2, platform, graph, pos=[0,0,0], with_platform=False)


    # Car(car_2, platform, graph, pos=[6,0,0], with_platform=False)
    #Car(car_2, platform, graph, pos=[6,0,0])

#Seteo bulletproof bomb

    car_3=Car_info("tareas/Tarea 2 entregada/bulletproof_bomb_chassis.stl", 
             "tareas/Tarea 2 entregada/bulletproof_bomb_front_wheels.stl", 
             "tareas/Tarea 2 entregada/bulletproof_bomb_rear_wheels.stl", 
             "tareas/Tarea 2 entregada/bulletproof_bomb_spare_wheels.stl", i=3)
    
    car_3.rear_wheels_material=rubber
    car_3.front_wheels_material=rubber
    car_3.spare_wheels_material=rubber
    car_3.chassis_material=cooper
    car_3.chassis_position=[0,0.14,0]
    car_3.front_wheels_position=[-0.78,-0.188,0.008]
    car_3.front_wheels_scale=[0.36,0.36,0.36]
    car_3.rear_wheels_position=[0.47,-0.188,-0.016]
    car_3.rear_wheels_scale=[0.38,0.38,0.38]
    car_3.spare_wheels_position=[0.159,-0.037,0.115]
    car_3.spare_wheels_scale=[0.615,0.615,0.615]
    
    
    # Car(car_3, platform, graph ,pos=[0,0,0], with_platform=False)


    # Car(car_3, platform, graph ,pos=[-6,0,0], with_platform=False)
    #Car(car_3, platform, graph ,pos=[-6,0,0])

#--------------------------------------------------------------------------------------
# Hangar
#--------------------------------------------------------------------------------------

    graph.add_node("light",
                   pipeline=color_mesh_lit_pipeline,
                   position=[1, 1, 1],
                   light=PointLight(
                       diffuse = [1, 1, 1], # rojo
                       specular = [0.8, 0.8, 0.8], # azul
                       ambient = [0, 0.15, 0], # verde
                       #constant = 1.0,
                       #linear = 0.7,
                       #quadratic = 1.8
                       )
                    )


    graph.add_node("sun",
                    pipeline=color_mesh_lit_pipeline,
                    position=[0, 2, 0],
                    rotation=[-np.pi/4, 0, 0],
                    light=DirectionalLight(diffuse = [1, 1, 1], specular = [0.25, 0.25, 0.25], ambient = [0.15, 0.15, 0.15]))
        
        
    # graph.add_node("hangar",position=[0,0,0])
    # hangar_floor_material = gold
    # hangar_wall_material = gold

    # graph.add_node("floor",
    #                attach_to="hangar",
    #                mesh = cube,
    #                pipeline = color_mesh_lit_pipeline,
    #                rotation = [-np.pi/2, 0, 0],
    #                scale = [16, 4, 1],
    #                position = [0,-0.5,0],
    #                material = hangar_floor_material)
    
    # graph.add_node("wall",
    #                attach_to="hangar",
    #                mesh = cube,
    #                pipeline = color_mesh_lit_pipeline,
    #                rotation = [0, 0, 0],
    #                scale = [16, 4, 0.25],
    #                position = [0,1.5,-2],
    #                material = hangar_wall_material)
    
    # graph.add_node("right_wall",
    #                attach_to="hangar",
    #                mesh = cube,
    #                pipeline = color_mesh_lit_pipeline,
    #                rotation = [0, -np.pi/2, 0],
    #                scale = [4, 4, 0.25],
    #                position = [8,1.5,0],
    #                material = hangar_wall_material)
    
    # graph.add_node("left_wall",
    #                attach_to="hangar",
    #                mesh = cube,
    #                pipeline = color_mesh_lit_pipeline,
    #                rotation = [0, -np.pi/2, 0],
    #                scale = [4, 4, 0.25],
    #                position = [-8,1.5,0],
    #                material = hangar_wall_material)
    
    graph.add_node("floor_2",
                    mesh = quad,
                    pipeline = color_mesh_lit_pipeline,
                    position = [0, -1, 0],
                    rotation = [-np.pi/2, 0, 0],
                    scale = [40, 40, 40],
                    material = Material(
                          diffuse = [1, 1, 1],
                          specular = [0.5, 0.5, 0.5],
                          ambient = [0.1, 0.1, 0.1],
                          shininess = 256
                     ))

#--------------------------------------------------------------------
# Simulación Física
#--------------------------------------------------------------------

    world = b2World(gravity=(0, 0))

    # Objetos estáticos
    wall1_body = world.CreateStaticBody(position=(-20, 0))
    wall1_body.CreatePolygonFixture(box=(0.5, 20), density=1, friction=1)

    wall2_body = world.CreateStaticBody(position=(20, 0))
    wall2_body.CreatePolygonFixture(box=(0.5, 20), density=1, friction=1)

    wall3_body = world.CreateStaticBody(position=(0, -20))
    wall3_body.CreatePolygonFixture(box=(20, 0.5), density=1, friction=1)

    wall4_body = world.CreateStaticBody(position=(0, 20))
    wall4_body.CreatePolygonFixture(box=(20, 0.5), density=1, friction=1)

    # Objetos dinámicos
    car_0_body = world.CreateDynamicBody(position=(2, 0), angle=0, linearDamping=0.75, angularDamping=0.5)
    car_0_body.CreatePolygonFixture(box=(0.5, 0.5), density=1, friction=1)

    front_wheels_0_body = world.CreateDynamicBody(position=(2, 0), angle=0, linearDamping=0.75, angularDamping=0.5)
    # front_wheels_0_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)
    front_wheels_0_body.CreateCircleFixture(radius=1, density=1, friction=0.3)
    rear_wheels_0_body = world.CreateDynamicBody(position=(2, 0), angle=0, linearDamping=0.75, angularDamping=0.5)
    # rear_wheels_0_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)
    rear_wheels_0_body.CreateCircleFixture(radius=0.01, density=1, friction=1)

    world.CreateWheelJoint(bodyA=car_0_body, bodyB=front_wheels_0_body, localAnchorB=(0,0), anchor=(0, 0), collideConnected=False)
    #world.CreateRevoluteJoint(bodyA=car_0_body, bodyB=rear_wheels_0_body, anchor=(0, 0), collideConnected=False)

    # DEscomentar -------------------------------
    # car_1_body = world.CreateDynamicBody(position=(-2,0), angle=0, linearDamping=0.75, angularDamping=0.5)
    # car_1_body.CreatePolygonFixture(box=(0.5, 0.5), density=4, friction=1)

    # front_wheels_1_body = world.CreateDynamicBody(position=(-2, 0), angle=0, linearDamping=0.75, angularDamping=0.5)
    # front_wheels_1_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)

    # rear_wheels_1_body = world.CreateDynamicBody(position=(-2, 0), angle=0, linearDamping=0.75, angularDamping=0.5)
    # rear_wheels_1_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)

    # car_2_body = world.CreateDynamicBody(position=(0,-2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # car_2_body.CreatePolygonFixture(box=(0.5, 0.8), density=1, friction=1)

    # front_wheels_2_body = world.CreateDynamicBody(position=(0,-2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # front_wheels_2_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)

    # rear_wheels_2_body = world.CreateDynamicBody(position=(0,-2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # rear_wheels_2_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)


    # car_3_body = world.CreateDynamicBody(position=(0,2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # car_3_body.CreatePolygonFixture(box=(0.5, 0.5), density=1, friction=1)

    # front_wheels_3_body = world.CreateDynamicBody(position=(0,2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # front_wheels_3_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)

    # rear_wheels_3_body = world.CreateDynamicBody(position=(0,2), angle=0, linearDamping=0.75, angularDamping=0.5)
    # rear_wheels_3_body.CreatePolygonFixture(box=(0.01, 0.01), density=1, friction=1)

    # Se guardan los cuerpos en el controller para poder acceder a ellos desde el loop de simulación
    controller.program_state["world"] = world
    controller.program_state["bodies"]["car_0"] = car_0_body
    # Descomentar ------------------------------
    # controller.program_state["bodies"]["car_1"] = car_1_body
    # controller.program_state["bodies"]["car_2"] = car_2_body
    # controller.program_state["bodies"]["car_3"] = car_3_body

    controller.program_state["bodies"]["front_wheels_0"] = front_wheels_0_body
    controller.program_state["bodies"]["rear_wheels_0"] = rear_wheels_0_body
    # DEscomentar ---------------------------
    # controller.program_state["bodies"]["front_wheels_1"] = front_wheels_1_body
    # controller.program_state["bodies"]["rear_wheels_1"] = rear_wheels_1_body
    # controller.program_state["bodies"]["front_wheels_2"] = front_wheels_2_body
    # controller.program_state["bodies"]["rear_wheels_2"] = rear_wheels_2_body
    # controller.program_state["bodies"]["front_wheels_3"] = front_wheels_3_body
    # controller.program_state["bodies"]["rear_wheels_3"] = rear_wheels_3_body


    #######################################

    def update_world(dt):
        world = controller.program_state["world"]
        world.Step(
            dt, controller.program_state["vel_iters"], controller.program_state["pos_iters"]
        )
        world.ClearForces()

    car_control_body = car_0_body
    front_wheels_control_body = front_wheels_0_body
    rear_wheels_control_body = rear_wheels_0_body
    k=0
    def update(dt):
        global car_control_body
        global front_wheels_control_body
        global rear_wheels_control_body
        global car_control_body
        global k
        controller.program_state["total_time"] += dt
        camera = controller.program_state["camera"]

        # Actualización física del car 0
        car_0_body = controller.program_state["bodies"]["car_0"]
        front_wheels_0_body = controller.program_state["bodies"]["front_wheels_0"]
        rear_wheels_0_body = controller.program_state["bodies"]["rear_wheels_0"]
        if graph["front_wheels_"+str(k)]["rotation"][2]!= front_wheels_0_body.angle:
            graph["front_wheels_"+str(k)]["rotation"][2] += front_wheels_0_body.angle
        graph["chassis_0"]["transform"] = tr.translate(car_0_body.position[0], 0, car_0_body.position[1]) @ tr.rotationY(-car_0_body.angle+np.pi/2)
        graph["front_wheels_0"]["transform"] = tr.translate(car_0_body.position[0], 0, car_0_body.position[1]) @ tr.rotationY(-car_0_body.angle+np.pi/2)
        # graph["front_wheels_0"]["rotation"][2] += -front_wheels_0_body.angle # gira bien
        # graph["front_wheels_0"]["rotation"][2] += -front_wheels_0_body.angle
        graph["rear_wheels_0"]["transform"] = tr.translate(car_0_body.position[0], 0, car_0_body.position[1]) @ tr.rotationY(-car_0_body.angle+np.pi/2)
        # graph["front_wheels_0"]["transform"] = tr.rotationY(-np.pi/2) @ tr.rotationZ(-front_wheels_0_body.angle) @ tr.rotationY(np.pi/2)
        # graph["rear_wheels_0"]["transform"] = tr.rotationY(-np.pi/2) @ tr.rotationZ(-front_wheels_0_body.angle) @ tr.rotationY(-np.pi/2)
        
        # --------- Descomentar
        # # Actualización física del car 1
        # car_1_body = controller.program_state["bodies"]["car_1"]
        # front_wheels_1_body = controller.program_state["bodies"]["front_wheels_1"]
        # rear_wheels_1_body = controller.program_state["bodies"]["rear_wheels_1"]
        # graph["chassis_1"]["transform"] = tr.translate(car_1_body.position[0], 0, car_1_body.position[1]) @ tr.rotationY(-car_1_body.angle+np.pi/2)
        # graph["front_wheels_1"]["transform"] = tr.translate(car_1_body.position[0], 0, car_1_body.position[1]) @ tr.rotationY(-car_1_body.angle+np.pi/2)
        # graph["rear_wheels_1"]["transform"] = tr.translate(car_1_body.position[0], 0, car_1_body.position[1]) @ tr.rotationY(-car_1_body.angle+np.pi/2)
        

        # # Actualización física del car 2
        # car_2_body = controller.program_state["bodies"]["car_2"]
        # front_wheels_2_body = controller.program_state["bodies"]["front_wheels_2"]
        # rear_wheels_2_body = controller.program_state["bodies"]["rear_wheels_2"]
        # graph["chassis_2"]["transform"] = tr.translate(car_2_body.position[0], 0, car_2_body.position[1]) @ tr.rotationY(-car_2_body.angle+np.pi/2)
        # graph["front_wheels_2"]["transform"] = tr.translate(car_2_body.position[0], 0, car_2_body.position[1]) @ tr.rotationY(-car_2_body.angle+np.pi/2)
        # graph["rear_wheels_2"]["transform"] = tr.translate(car_2_body.position[0], 0, car_2_body.position[1]) @ tr.rotationY(-car_2_body.angle+np.pi/2)
        

        # # Actualización física del car 3
        # car_3_body = controller.program_state["bodies"]["car_3"]
        # front_wheels_3_body = controller.program_state["bodies"]["front_wheels_3"]
        # rear_wheels_3_body = controller.program_state["bodies"]["rear_wheels_3"]
        # graph["chassis_3"]["transform"] = tr.translate(car_3_body.position[0], 0, car_3_body.position[1]) @ tr.rotationY(-car_3_body.angle+np.pi/2)
        # graph["front_wheels_3"]["transform"] = tr.translate(car_3_body.position[0], 0, car_3_body.position[1]) @ tr.rotationY(-car_3_body.angle+np.pi/2)
        # graph["rear_wheels_3"]["transform"] = tr.translate(car_3_body.position[0], 0, car_3_body.position[1]) @ tr.rotationY(-car_3_body.angle+np.pi/2)
        # graph["spare_wheels_3"]["transform"] = tr.translate(car_3_body.position[0], 0, car_3_body.position[1]) @ tr.rotationY(-car_3_body.angle+np.pi/2)

        # if controller.is_key_pressed(pyglet.window.key._0):
        #     k=0
        #     car_control_body = car_0_body
        # if controller.is_key_pressed(pyglet.window.key._1):
        #     k=1
        #     car_control_body = car_1_body
        # if controller.is_key_pressed(pyglet.window.key._2):
        #     k=2
        #     car_control_body = car_2_body
        # if controller.is_key_pressed(pyglet.window.key._3):
        #     k=3
        #     car_control_body = car_3_body
        

        # Modificar la fuerza y el torque del car con las teclas

        
        car_control_forward = np.array([np.sin(-car_control_body.angle), 0, np.cos(-car_control_body.angle)])
        if controller.is_key_pressed(pyglet.window.key.A):
            car_control_body.ApplyTorque(-0.5, True)
        if controller.is_key_pressed(pyglet.window.key.D):
            car_control_body.ApplyTorque(0.5, True)
        if controller.is_key_pressed(pyglet.window.key.W):
            #radius=0.01
            front_wheels_control_body.ApplyTorque(10, True)
            
            #car_control_body.ApplyForce((car_control_forward[0], car_control_forward[2]), car_control_body.worldCenter, True)
        if controller.is_key_pressed(pyglet.window.key.S):
            car_control_body.ApplyForce((-car_control_forward[0], -car_control_forward[2]), car_control_body.worldCenter, True)
        camera.position[0] = car_control_body.position[0] + 2 * np.sin(car_control_body.angle)
        camera.position[1] = 2
        camera.position[2] = car_control_body.position[1] - 2 * np.cos(car_control_body.angle)
        camera.yaw = car_control_body.angle + np.pi / 2
        # if controller.is_key_pressed(pyglet.window.key.LEFT):
        #     camera.position -= camera.right * dt
        # if controller.is_key_pressed(pyglet.window.key.RIGHT):
        #     camera.position += camera.right * dt
        # if controller.is_key_pressed(pyglet.window.key.UP):
        #     camera.position += camera.forward * dt
        # if controller.is_key_pressed(pyglet.window.key.DOWN):
        #     camera.position -= camera.forward * dt
        camera.update()
        update_world(dt)

    posiciones = [[2,1.5,2], [-2,1.5,2] , [6,1.5,2], [-6,1.5,2]]
    k=0
    print("\tW: Cambio auto\n\t Q/E: Baja/Sube Cámara \n\t1/2: Vista perspectiva/ortográfica \n\tUP/DOWN/LEFT/RIGHT: Cámara Libre" )
    
    
    
    # def update(dt):
    #     global k
    #     global posiciones
    #     controller.program_state["total_time"] += dt
    #     camera = controller.program_state["camera"]

    #     # graph["chassis_"+str(k)]["rotation"][1] += 2*dt
    #     # graph["front_wheels_"+str(k)]["rotation"][1] += 2*dt
    #     # graph["rear_wheels_"+str(k)]["rotation"][1] += 2*dt
    #     #graph["platform_"+str(k)]["rotation"][1] += 2*dt

        
    #     if controller.is_key_pressed(pyglet.window.key.LEFT):
    #         camera.position -= camera.right * dt
    #     if controller.is_key_pressed(pyglet.window.key.RIGHT):
    #         camera.position += camera.right * dt
    #     if controller.is_key_pressed(pyglet.window.key.UP):
    #         camera.position += camera.forward * dt
    #     if controller.is_key_pressed(pyglet.window.key.DOWN):
    #         camera.position -= camera.forward * dt
    #     if controller.is_key_pressed(pyglet.window.key.Q):
    #         camera.position[1] -= dt
    #     if controller.is_key_pressed(pyglet.window.key.E):
    #         camera.position[1] += dt
    #     if controller.is_key_pressed(pyglet.window.key._1):
    #         camera.type = "perspective"
    #     if controller.is_key_pressed(pyglet.window.key._2):
    #         camera.type = "orthographic"
    #     if controller.is_key_pressed(pyglet.window.key.W):
    #         k+=1
    #         k=k%4
    #         camera.position = posiciones[k]
    #     camera.update()

    @controller.event
    def on_key_press(symbol, modifiers):
        car_control_body = controller.program_state["bodies"]["car_"+str(k)]
        # Reset car_control
        if symbol == pyglet.window.key.SPACE:
            car_control_body.position = (0, -5)
            car_control_body.angle = 0
            car_control_body.linearVelocity = (0, 0)
            car_control_body.angularVelocity = 0
    @controller.event
    def on_resize(width, height):
        controller.program_state["camera"].resize(width, height)

    @controller.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.RIGHT:
            controller.program_state["camera"].yaw += dx * 0.01
            controller.program_state["camera"].pitch += dy * 0.01


    

    # draw loop
    @controller.event
    def on_draw():
        controller.clear()
        axis_scene.draw()
        graph.draw()

    pyglet.clock.schedule_interval(update, 1/60)
    pyglet.app.run()

