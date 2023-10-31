import pyglet
from OpenGL import GL
import numpy as np
import sys

# No es necesario este bloque de código si se ejecuta desde la carpeta raíz del repositorio
# v
if sys.path[0] != "":
    sys.path.insert(0, "")
sys.path.append('../../')
# ^
# No es necesario este bloque de código si se ejecuta desde la carpeta raíz del repositorio

import auxiliares.utils.shapes as shapes
from auxiliares.utils.camera import FreeCamera
from auxiliares.utils.scene_graph import SceneGraph
from auxiliares.utils.drawables import Model, Texture, DirectionalLight, PointLight, SpotLight, Material
from auxiliares.utils.helpers import init_axis, init_pipeline, mesh_from_file, get_path

WIDTH = 720
HEIGHT = 720

class Controller(pyglet.window.Window):
    def __init__(self, title, *args, **kargs):
        super().__init__(*args, **kargs)
        self.set_minimum_size(240, 240) # Evita error cuando se redimensiona a 0
        self.set_caption(title)
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.program_state = { "total_time": 0.0, "camera": None }
        self.init()

    def init(self):
        GL.glClearColor(1, 1, 1, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CCW)

    def is_key_pressed(self, key):
        return self.key_handler[key]

class Car_info():
    def __init__(self, chassis, front_wheels, rear_wheels, i=0):
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

class Platform_info():
    def __init__(self, platform):
        self.mesh = mesh_from_file(platform)[0]["mesh"]
        self.position = [0,0,0]
        self.scale = [1,1,1]
        self.material = None

class Car():
    def __init__(self, chassis_mesh, wheel_mesh, platform_mesh, graph, material, i=0, pos=[0,0,0]):

        chassis_material, wheel_material, platform_material=material
        graph.add_node("car_system_"+str(i),position=pos)
        graph.add_node("platform_"+str(i), attach_to="car_system_"+str(i),mesh=platform_mesh, 
                       color=[0.5, 0.5, 0.5], pipeline=color_mesh_lit_pipeline, material=platform_material, 
                       scale=[2,2,2])
        graph.add_node("car_"+str(i), attach_to="car_system_"+str(i),position=[0.2,0.31,0])
        graph.add_node("chassis_"+str(i), attach_to="car_"+str(i),mesh=chassis_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=[1,1,1],material=chassis_material)
        graph.add_node("lrw_"+str(i), attach_to="car_"+str(i), mesh=wheel_mesh, position=[0.08,-0.19,0.16],
                       pipeline=color_mesh_lit_pipeline, scale=[1/10,1/10,1/10],material=wheel_material)
        graph.add_node("rrw_"+str(i), attach_to="car_"+str(i), mesh=wheel_mesh, position=[0.08,-0.19,-0.16],
                       pipeline=color_mesh_lit_pipeline, scale=[1/10,1/10,1/10],material=wheel_material)
        graph.add_node("lfw_"+str(i), attach_to="car_"+str(i), mesh=wheel_mesh, position=[-0.642,-0.19,0.08],
                       pipeline=color_mesh_lit_pipeline, scale=[1/10,1/10,1/10],material=wheel_material)
        graph.add_node("rfw_"+str(i), attach_to="car_"+str(i), mesh=wheel_mesh, position=[-0.642,-0.19,-0.08],
                       pipeline=color_mesh_lit_pipeline, scale=[1/10,1/10,1/10],material=wheel_material)
        
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
        

class Car2():
    def __init__(self, chassis_mesh, wheel_mesh, platform_mesh, graph, 
                 material, i=0, chassis_pos=[0,0,0], wheel_pos=[0,0,0], pos=[0,0,0]):

        chassis_material, wheel_material, platform_material=material
        graph.add_node("car_system_"+str(i),position=pos)
        graph.add_node("platform_"+str(i), attach_to="car_system_"+str(i),mesh=platform_mesh, 
                       color=[0.5, 0.5, 0.5], pipeline=color_mesh_lit_pipeline, material=platform_material, 
                       scale=[2,2,2])
        graph.add_node("car_"+str(i), attach_to="car_system_"+str(i),position=[0,0.24,0])
        # graph.add_node("car_"+str(i), attach_to="car_system_"+str(i),position=[0.2,0.31,0])
        graph.add_node("chassis_"+str(i), attach_to="car_"+str(i),mesh=chassis_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=[1,1,1],material=chassis_material, 
                       position = chassis_pos)
        graph.add_node("wheel_"+str(i), attach_to="car_"+str(i), mesh=wheel_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=[0.7,0.7,0.7], material=wheel_material, position = wheel_pos)

        
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
        

class Car3():
    def __init__(self, car, platform, graph, pos=[0,0,0]):
        i=car.car_number
        graph.add_node("car_system_"+str(i),position=pos)
        graph.add_node("platform_"+str(i), attach_to="car_system_"+str(i),mesh=platform.mesh, 
                       color=[0.5, 0.5, 0.5], pipeline=color_mesh_lit_pipeline, material=platform.material, 
                       scale=platform.scale)
        graph.add_node("car_"+str(i), attach_to="car_system_"+str(i),position=[0,0.24,0])

        graph.add_node("chassis_"+str(i), attach_to="car_"+str(i),mesh=car.chassis_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.chassis_scale,material=car.chassis_material, 
                       position = car.chassis_position)
        graph.add_node("front_wheel_"+str(i), attach_to="car_"+str(i), mesh=car.front_wheels_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.front_wheels_scale, material=car.front_wheels_material, position = car.front_wheels_position)
        
        graph.add_node("rear_wheel_"+str(i), attach_to="car_"+str(i), mesh=car.rear_wheels_mesh,
                       pipeline=color_mesh_lit_pipeline, scale=car.rear_wheels_scale, material=car.rear_wheels_material, position = car.rear_wheels_position)

        
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
        

        

    def draw(self):
        self.graph.draw()

if __name__ == "__main__":
    # Instancia del controller
    controller = Controller("Tarea 2", width=WIDTH, height=HEIGHT, resizable=True)

    # controller.program_state["camera"] = FreeCamera([2, 1.5, 2], "perspective")
    controller.program_state["camera"] = FreeCamera([6, 1.5, 2], "perspective")
    controller.program_state["camera"].yaw = -np.pi / 2#-3* np.pi/ 4
    controller.program_state["camera"].pitch = -np.pi / 4

    
    textured_mesh_lit_pipeline = init_pipeline(
        get_path("auxiliares/shaders/textured_mesh_lit.vert"),
        get_path("auxiliares/shaders/textured_mesh_lit.frag"))
    
    color_mesh_lit_pipeline = init_pipeline(
        get_path("auxiliares/shaders/color_mesh_lit.vert"),
        get_path("auxiliares/shaders/color_mesh_lit.frag"))

    cube = Model(shapes.Cube["position"], shapes.Cube["uv"], shapes.Cube["normal"], index_data=shapes.Cube["indices"])
    quad = Model(shapes.Square["position"], shapes.Square["uv"], shapes.Square["normal"], index_data=shapes.Square["indices"])
    arrow = mesh_from_file("assets/arrow.off")[0]["mesh"]

    

    # chassis_mesh = mesh_from_file("testeo/wacky_races/auto_completo.stl")[0]["mesh"]
    # wheel_mesh = mesh_from_file("testeo/wacky_races/right_front_wheel.stl")[0]["mesh"]
    platform_mesh = mesh_from_file("testeo/wacky_races/circular_platform.stl")[0]["mesh"]

    # chassis0_mesh = mesh_from_file("testeo/wacky_races/mean_machine_chassis.stl")[0]["mesh"]
    # wheel0_mesh = mesh_from_file("testeo/wacky_races/mean_machine_wheels.stl")[0]["mesh"]

    # chassis1_mesh = mesh_from_file("testeo/wacky_races/army_surplus_special_chassis.stl")[0]["mesh"]
    # wheel1_mesh = mesh_from_file("testeo/wacky_races/army_surplus_special_wheels.stl")[0]["mesh"]

    # chassis2_mesh = mesh_from_file("testeo/wacky_races/turbo_terrific_chassis.stl")[0]["mesh"]
    # wheel2_mesh = mesh_from_file("testeo/wacky_races/turbo_terrific_wheels.stl")[0]["mesh"]

    # chassis3_mesh = mesh_from_file("testeo/wacky_races/bulletproof_bomb_chassis.stl")[0]["mesh"]
    # wheel3_mesh = mesh_from_file("testeo/wacky_races/bulletproof_bomb_wheels.stl")[0]["mesh"]

    # chassis0_mesh = mesh_from_file("testeo/wacky_races/mean_machine_chassis.stl")[0]["mesh"]
    # front_wheel0_mesh = mesh_from_file("testeo/wacky_races/mean_machine_front_wheels.stl")[0]["mesh"]
    # rear_wheel0_mesh = mesh_from_file("testeo/wacky_races/mean_machine_rear_wheels.stl")[0]["mesh"]

    # chassis1_mesh = mesh_from_file("testeo/wacky_races/army_surplus_special_chassis.stl")[0]["mesh"]
    # front_wheel1_mesh = mesh_from_file("testeo/wacky_races/army_surplus_special_front_wheels.stl")[0]["mesh"]
    # rear_wheel1_mesh = mesh_from_file("testeo/wacky_races/army_surplus_special_rear_wheels.stl")[0]["mesh"]

    # chassis2_mesh = mesh_from_file("testeo/wacky_races/turbo_terrific_chassis.stl")[0]["mesh"]
    # front_wheel2_mesh = mesh_from_file("testeo/wacky_races/turbo_terrific_front_wheels.stl")[0]["mesh"]
    # rear_wheel2_mesh = mesh_from_file("testeo/wacky_races/turbo_terrific_rear_wheels.stl")[0]["mesh"]

    # chassis3_mesh = mesh_from_file("testeo/wacky_races/bulletproof_bomb_chassis.stl")[0]["mesh"]
    # front_wheel3_mesh = mesh_from_file("testeo/wacky_races/bulletproof_bomb_front_wheels.stl")[0]["mesh"]
    # rear_wheel3_mesh = mesh_from_file("testeo/wacky_races/bulletproof_bomb_rear_wheels.stl")[0]["mesh"]


    graph = SceneGraph(controller)

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



    # Car(chassis_mesh, wheel_mesh, platform_mesh, graph, [material, rubber, silver], pos=[0,0,0])
    
    # Car(chassis_mesh, wheel_mesh, platform_mesh, graph, [emerald, rubber,  silver], i=1,pos=[-5,0,0])
    # Car(chassis_mesh, wheel_mesh, platform_mesh, graph, [gold, rubber, silver], i=2,pos=[5,0,0])


    # Car2(chassis0_mesh, wheel0_mesh, platform_mesh, graph, [material, rubber, silver], i=0,pos=[2,0,0], chassis_pos=[0.2,0.1,0],wheel_pos=[0,-0.07,0])
    # Car2(chassis1_mesh, wheel1_mesh, platform_mesh, graph, [emerald, rubber,  silver], i=1,pos=[-2,0,0], chassis_pos=[-0.125,0.355,0])
    # Car2(chassis2_mesh, wheel2_mesh, platform_mesh, graph, [gold, rubber, silver], i=2,pos=[6,0,0], chassis_pos=[-0.025,-0.045,0],wheel_pos=[-0.4,0,0])
    # Car2(chassis3_mesh, wheel3_mesh, platform_mesh, graph, [chrome, rubber, silver], i=3,pos=[-6,0,0], chassis_pos=[0,0.15,0],wheel_pos=[0,-0.04,0])


    
    platform = Platform_info("testeo/wacky_races/circular_platform.stl")

    platform.material=silver
    platform.position=[0,0,0]
    platform.scale=[2,2,2]


#Seteo mean machine listo

    # car_0=Car_info("testeo/wacky_races/mean_machine_chassis.stl", 
    #          "testeo/wacky_races/mean_machine_front_wheels.stl", 
    #          "testeo/wacky_races/mean_machine_rear_wheels.stl", 0)
    
    # car_0.rear_wheels_material=rubber
    # car_0.front_wheels_material=rubber
    # car_0.chassis_material=material
    # car_0.chassis_position=[0.2,0.1,0]
    # car_0.front_wheels_position=[-0.435,-0.1,0]
    # car_0.front_wheels_scale=[0.2,0.2,0.2]
    # car_0.rear_wheels_position=[0.28,-0.1,0]#[0.25,-0.07,0]
    # car_0.rear_wheels_scale=[0.3,0.3,0.3]

    # Car3(car_0, platform, graph, pos=[2,0,0])

#Seteo army surplus special listo


    # car_1=Car_info("testeo/wacky_races/army_surplus_special_chassis.stl", 
    #          "testeo/wacky_races/army_surplus_special_front_wheels.stl", 
    #          "testeo/wacky_races/army_surplus_special_rear_wheels.stl", 1)
    
    # car_1.rear_wheels_material=rubber
    # car_1.front_wheels_material=rubber
    # car_1.chassis_material=emerald
    # car_1.chassis_position=[-0.125,0.335,0]
    # car_1.front_wheels_position=[0.55,-0.09,0]
    # car_1.front_wheels_scale=[0.2,0.2,0.2]
    # car_1.rear_wheels_position=[0,-0.03,0]
    # car_1.rear_wheels_scale=[0.5,0.5,0.5]

    # Car3(car_1, platform, graph, pos=[-2,0,0])


    car_2=Car_info("testeo/wacky_races/turbo_terrific_chassis.stl", 
             "testeo/wacky_races/turbo_terrific_front_wheels.stl", 
             "testeo/wacky_races/turbo_terrific_rear_wheels.stl", 2)
    
    car_2.rear_wheels_material=rubber
    car_2.front_wheels_material=rubber
    car_2.chassis_material=gold
    car_2.chassis_position=[-0.025,-0.045,0]
    car_2.front_wheels_position=[-0.4,0,0]
    car_2.rear_wheels_position=[-0.4,0,0]

    Car3(car_2, platform, graph, pos=[6,0,0])

    # car_3=Car_info("testeo/wacky_races/bulletproof_bomb_chassis.stl", 
    #          "testeo/wacky_races/bulletproof_bomb_front_wheels.stl", 
    #          "testeo/wacky_races/bulletproof_bomb_rear_wheels.stl", 3)
    
    # car_3.rear_wheels_material=rubber
    # car_3.front_wheels_material=rubber
    # car_3.chassis_material=chrome
    # car_3.chassis_position=[0,0.15,0]
    # car_3.front_wheels_position=[0,-0.04,0]
    # car_3.rear_wheels_position=[0,-0.04,0]
    
    # Car3(car_3, platform, graph ,pos=[-6,0,0])


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

    graph.add_node("hangar",position=[0,0,0])

    graph.add_node("floor",
                   attach_to="hangar",
                   mesh = cube,
                   pipeline = color_mesh_lit_pipeline,
                   rotation = [-np.pi/2, 0, 0],
                   scale = [16, 4, 1],
                   position = [0,-0.5,0],
                   material = obsidian)
    
    graph.add_node("wall",
                   attach_to="hangar",
                   mesh = cube,
                   pipeline = color_mesh_lit_pipeline,
                   rotation = [0, 0, 0],
                   scale = [16, 4, 0.25],
                   position = [0,1.5,-2],
                   material = emerald)
    
    graph.add_node("right_wall",
                   attach_to="hangar",
                   mesh = cube,
                   pipeline = color_mesh_lit_pipeline,
                   rotation = [0, -np.pi/2, 0],
                   scale = [4, 4, 0.25],
                   position = [8,1.5,0],
                   material = emerald)
    
    graph.add_node("left_wall",
                   attach_to="hangar",
                   mesh = cube,
                   pipeline = color_mesh_lit_pipeline,
                   rotation = [0, -np.pi/2, 0],
                   scale = [4, 4, 0.25],
                   position = [-8,1.5,0],
                   material = emerald)


    # graph.add_node("arrow",
    #                attach_to="spotlight",
    #                mesh=arrow,
    #                position=[0, 0, 0],
    #                rotation=[-np.pi, 0, 0],
    #                scale=[0.5, 0.5, 0.5],
    #                color=[1, 1, 0],
    #                pipeline=color_mesh_pipeline)
    

    # diffuse: Color difuso del material
    # specular: Color especular del material
    # ambient: Color ambiental del material
    # shininess: Exponente especular del material

    posiciones = [[-2,1.5,2], [2,1.5,2], [6,1.5,2]]
    k=2
    def update(dt):
        global k
        global posiciones
        controller.program_state["total_time"] += dt
        camera = controller.program_state["camera"]

        # graph["car_"+str(k)]["rotation"][1] += 2*dt
        # graph["platform_"+str(k)]["rotation"][1] += 2*dt

        
        if controller.is_key_pressed(pyglet.window.key.A):
            camera.position -= camera.right * dt
        if controller.is_key_pressed(pyglet.window.key.D):
            camera.position += camera.right * dt
        if controller.is_key_pressed(pyglet.window.key.W):
            camera.position += camera.forward * dt
        if controller.is_key_pressed(pyglet.window.key.S):
            camera.position -= camera.forward * dt
        if controller.is_key_pressed(pyglet.window.key.Q):
            camera.position[1] -= dt
        if controller.is_key_pressed(pyglet.window.key.E):
            camera.position[1] += dt
        if controller.is_key_pressed(pyglet.window.key._1):
            camera.type = "perspective"
        if controller.is_key_pressed(pyglet.window.key._2):
            camera.type = "orthographic"
        if controller.is_key_pressed(pyglet.window.key.O):
            k+=1
            k=k%3
            camera.position = posiciones[k]
        camera.update()

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
        graph.draw()

    pyglet.clock.schedule_interval(update, 1/60)
    pyglet.app.run()
