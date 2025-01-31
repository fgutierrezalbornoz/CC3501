import pyglet
from OpenGL import GL
import numpy as np
import sys
import os
import time
import trimesh as tm
import networkx as nx
sys.path.append(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
import grafica.transformations as tr

WIDTH = 640
HEIGHT = 640

print("comienza el co")
#------------------------------------------------------------
# Implementación de pyglet
#------------------------------------------------------------

class Pipeline(pyglet.graphics.shader.ShaderProgram):
    def __init__(self, vertex_source, fragment_source):
        vert_shader = pyglet.graphics.shader.Shader(vertex_source,"vertex")
        frag_shader = pyglet.graphics.shader.Shader(fragment_source,"fragment")
        super().__init__(vert_shader, frag_shader)

    def set_uniform(self, name, value, type):
        uniform = self[name]
        if uniform is None:
            print(f"Warning: Uniform {name} does not exist")
            return
        
        if type == "matrix":
            self[name] = np.reshape(value, (16, 1), order="F")
        elif type == "float":
            self[name] = value

class Model():
    def __init__(self, position_data, index_data=None):
        self.position_data = position_data

        self.index_data = index_data
        if index_data is not None:
            self.index_data = np.array(index_data, dtype=np.uint32)

        self.gpu_data = None

        self.position = np.array([0, 0, 0], dtype=np.float32)
        self.rotation = np.array([0, 0, 0], dtype=np.float32)
        self.scale = np.array([1, 1, 1], dtype=np.float32)

    def init_gpu_data(self, pipeline):
        self.pipeline = pipeline
        if self.index_data is not None:
            self.gpu_data = pipeline.vertex_list_indexed(len(self.position_data) // 3, GL.GL_TRIANGLES, self.index_data)
        else:
            self.gpu_data = pipeline.vertex_list(len(self.position_data) // 3, GL.GL_TRIANGLES)
        
        self.gpu_data.position[:] = self.position_data

    def draw(self, mode = GL.GL_TRIANGLES):
        self.gpu_data.draw(mode)

    def get_transform(self):
        translation_matrix = tr.translate(self.position[0], self.position[1], self.position[2])
        rotation_matrix = tr.rotationX(self.rotation[0]) @ tr.rotationY(self.rotation[1]) @ tr.rotationZ(self.rotation[2])
        scale_matrix = tr.scale(self.scale[0], self.scale[1], self.scale[2])
        transformation = translation_matrix @ rotation_matrix @ scale_matrix
        return np.reshape(transformation, (16, 1), order="F")
#------------------------------------------------------------
# Clase Controller
#------------------------------------------------------------

class Controller(pyglet.window.Window):
    def __init__(self, title, *args, **kargs):
        super().__init__(*args, **kargs)
        self.set_minimum_size(240, 240) # Evita error cuando se redimensiona a 0
        self.set_caption(title)
        self.key_handler = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.program_state = { "total_time": 0.0, "camera": None, "light": None }
        self.init()

    def init(self):
        GL.glClearColor(1, 1, 1, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CCW)

    def is_key_pressed(self, key):
        return self.key_handler[key]
    
class Mesh(Model):
    def __init__(self, asset_path, s=0):
        mesh_data = tm.load(asset_path)
        if s==0:
            mesh_scale = tr.uniformScale(2.0 / mesh_data.scale)
        else:
            mesh_scale = tr.uniformScale(2.0 / s)
        mesh_translate = tr.translate(*-mesh_data.centroid)
        mesh_data.apply_transform(mesh_scale @ mesh_translate)
        vertex_data = tm.rendering.mesh_to_vertexlist(mesh_data)
        indices = vertex_data[3]
        positions = vertex_data[4][1]

        super().__init__(positions, indices)

        # count = len(positions) // 3
        # colors = np.full((count * 3, 1), 1.0)
        # if base_color is None:
        #     colors = vertex_data[5][1]
        # else:
        #     for i in range(count):
        #         colors[i * 3] = base_color[0]
        #         colors[i * 3 + 1] = base_color[1]
        #         colors[i * 3 + 2] = base_color[2]

        # super().__init__(positions, colors, indices)

#------------------------------------------------------------
# Clase Cámara
#------------------------------------------------------------

class Camera():
    def __init__(self, camera_type = "perspective", pos=[1,0,0],foc=[0,0,0]):
        self.position = np.array(pos, dtype=np.float32)
        self.focus = np.array(foc, dtype=np.float32)
        self.type = camera_type
        self.width = WIDTH
        self.height = HEIGHT

    def update(self):
        pass

    def get_view(self):
        lookAt_matrix = tr.lookAt(self.position, self.focus, np.array([0, 1, 0], dtype=np.float32))
        return np.reshape(lookAt_matrix, (16, 1), order="F")

    def get_projection(self):
        if self.type == "perspective":
            projection_matrix = tr.perspective(90, self.width / self.height, 0.001, 1000)
        elif self.type == "orthographic":
            depth = self.position - self.focus
            depth = np.linalg.norm(depth)
            projection_matrix = tr.ortho(-(self.width / self.height) * depth, (self.width / self.height) * depth, -1 * depth, 1 * depth, 0.01, 100)
        return np.reshape(projection_matrix, (16, 1), order="F")
        
    def resize(self, width, height):
        self.width = width
        self.height = height

class OrbitCamera(Camera):
    def __init__(self, distance, camera_type = "perspective",pos=[1,0,0],foc=[0,0,0]):
        super().__init__(camera_type,pos,foc)
        self.distance = distance
        self.phi = 0
        self.theta = np.pi / 3
        self.update()

    def update(self):
        if self.theta > np.pi:
            self.theta = np.pi
        elif self.theta < 0:
            self.theta = 0.0001

        self.position[0] = self.distance * np.sin(self.theta) * np.sin(self.phi)
        self.position[1] = self.distance * np.cos(self.theta)
        self.position[2] = self.distance * np.sin(self.theta) * np.cos(self.phi)

class FreeCamera(Camera):
    def __init__(self, position = [0, 0, 0], camera_type = "perspective"):
        super().__init__(camera_type)
        self.position = np.array(position, dtype=np.float32)
        self.pitch = 0
        self.yaw = 0
        self.forward = np.array([0, 0, -1], dtype=np.float32)
        self.right = np.array([1, 0, 0], dtype=np.float32)
        self.up = np.array([0, 1, 0], dtype=np.float32)
        self.update()
    
    def update(self):
        self.forward[0] = np.cos(self.yaw) * np.cos(self.pitch)
        self.forward[1] = np.sin(self.pitch)
        self.forward[2] = np.sin(self.yaw) * np.cos(self.pitch)
        self.forward = self.forward / np.linalg.norm(self.forward)

        self.right = np.cross(self.forward, np.array([0, 1, 0], dtype=np.float32))
        self.right = self.right / np.linalg.norm(self.right)

        self.up = np.cross(self.right, self.forward)
        self.up = self.up / np.linalg.norm(self.up)

        self.focus = self.position + self.forward
#------------------------------------------------------------
# Clase Grafo de escena
#------------------------------------------------------------

class SceneGraph():
    def __init__(self, camera=None):
        self.graph=nx.DiGraph(root="root")
        self.add_node("root")
        self.camera=camera
    
    def add_node(self,
                 name,
                 attach_to=None,
                 mesh=None,
                 color=[1,1,1],
                 transform=tr.identity(),
                 position=[0,0,0],
                 rotation=[0,0,0],
                 scale=[1,1,1],
                 mode=GL.GL_TRIANGLES):
        self.graph.add_node(
            name,
            mesh=mesh,
            color=color,
            transform=transform,
            position=np.array(position, dtype=np.float32),
            rotation=np.array(rotation,dtype=np.float32),
            scale=np.array(scale, dtype=np.float32),
            mode=mode)
        if attach_to is None:
            attach_to = "root"

        self.graph.add_edge(attach_to, name)

    def __getitem__(self, name):
        if name not in self.graph.nodes:
            raise KeyError(f"Node {name} not in graph")
        
        return self.graph.nodes[name]
    
    def __setitem__(self, name, value):
        if name not in self.graph.nodes:
            raise KeyError(f"Node {name} not in graph")
        
        self.graph.nodes[name] = value

    def get_transform(self, node):
        node = self.graph.nodes[node]
        transform = node["transform"]
        translation_matrix = tr.translate(node["position"][0], node["position"][1], node["position"][2])
        rotation_matrix = tr.rotationX(node["rotation"][0]) @ tr.rotationY(node["rotation"][1]) @ tr.rotationZ(node["rotation"][2])
        scale_matrix = tr.scale(node["scale"][0], node["scale"][1], node["scale"][2])
        return transform @ translation_matrix @ rotation_matrix @ scale_matrix
    
    def draw(self):
        root_key = self.graph.graph["root"]
        edges = list(nx.edge_dfs(self.graph, source=root_key))
        transformations = {root_key: self.get_transform(root_key)}
        
        for src, dst in edges:
            current_node = self.graph.nodes[dst]

            if not dst in transformations:
                transformations[dst] = transformations[src] @ self.get_transform(dst)

            if current_node["mesh"] is not None:
                current_pipeline = current_node["mesh"].pipeline
                current_pipeline.use()

                if self.camera is not None:
                    if "u_view" in current_pipeline.uniforms:
                        current_pipeline["u_view"] = self.camera.get_view()

                    if "u_projection" in current_pipeline.uniforms:
                        current_pipeline["u_projection"] = self.camera.get_projection()
                    
                    current_pipeline["u_model"] = np.reshape(transformations[dst], (16,1), order="F")

                    if "u_color" in current_pipeline.uniforms:
                        current_pipeline["u_color"] = np.array(current_node["color"], dtype=np.float32)
                    current_node["mesh"].draw(current_node["mode"])

#------------------------------------------------------------
# Clase Auto
#------------------------------------------------------------

class Car():
    def __init__(self, chassis_mesh, wheel_mesh, platform_mesh, camera,pos=[0,0,0]):
        car_system = SceneGraph(camera)
        car_system.add_node("platform", mesh=platform_mesh, color=[0.5, 0.5, 0.5],position=pos)

        car_system.add_node("car", position=[0.2+pos[0],0.31+pos[1],0+pos[2]])
        car_system.add_node("chassis", attach_to="car", color=[138/255,43/255,226/255],mesh=chassis_mesh)
        car_system.add_node("lrw", attach_to="car", mesh=wheel_mesh, color=[0,0,0],position=[0.08,-0.19,0.16])
        car_system.add_node("rrw", attach_to="car", mesh=wheel_mesh, color=[0,0,0],position=[0.08,-0.19,-0.16])
        car_system.add_node("lfw", attach_to="car", mesh=wheel_mesh, color=[0,0,0],position=[-0.642,-0.19,0.08])
        car_system.add_node("rfw", attach_to="car", mesh=wheel_mesh, color=[0,0,0],position=[-0.642,-0.19,-0.08])
        

        self.graph = car_system

    def draw(self):
        self.graph.draw()

    # def rotation(self,dtheta):
    #     self.position@=tr.translate(-self["position"])
    #     self.rotation@=tr.rotationX(self["rotation"][0])
    #     self.position@=tr.translate(self["position"])

    def update(self,dt):
        pass

#------------------------------------------------------------
# Clase Hangar
#------------------------------------------------------------

class Hangar():
    def __init__(self, wall_mesh, camera,position=[0,0,0]):
        hangar_system = SceneGraph(camera)
        hangar_system.add_node("hangar_node", position=position)
        hangar_system.add_node("floor", attach_to="hangar_node", mesh=wall_mesh, color=[0, 1, 0], position=[0,-0.2,0], scale=[3,3,3])
        hangar_system.add_node("left_wall", attach_to="hangar_node", mesh=wall_mesh, color=[1, 1, 0], position=[-3,1.4,0],rotation=[0,0,np.pi/2], scale=[1.5,3,3])
        hangar_system.add_node("right_wall", attach_to="hangar_node", mesh=wall_mesh, color=[1, 1, 0], position=[3,1.4,0], rotation=[0,0,np.pi/2], scale=[1.5,3,3])
        hangar_system.add_node("back_wall", attach_to="hangar_node", mesh=wall_mesh, color=[1, 1, 0], position=[0,1.4,-1.3], rotation=[np.pi/2,0,0], scale=[3,3,3])


        self.graph = hangar_system

    def draw(self):
        self.graph.draw()

    def update(self,dt):
        pass

#------------------------------------------------------------
# shaders
#------------------------------------------------------------

vertex_source_code = """
    #version 330

    in vec3 position;
    
    uniform vec3 u_color = vec3(1.0);

    uniform mat4 u_model = mat4(1.0);
    uniform mat4 u_view = mat4(1.0);
    uniform mat4 u_projection = mat4(1.0);

    out vec3 fragColor;

    void main()
    {
        fragColor = u_color;
        gl_Position = u_projection * u_view * u_model * vec4(position, 1.0f);
    }
"""

fragment_source_code = """
    #version 330

    in vec3 fragColor;
    out vec4 outColor;

    void main()
    {
        outColor = vec4(fragColor, 1.0f);
    }
"""

#------------------------------------------------------------
# Tarea 1
#------------------------------------------------------------

if __name__=="__main__":
    pipeline = Pipeline(vertex_source_code, fragment_source_code)
    controller = Controller("Tarea 2", width=WIDTH, height=HEIGHT, resizable=True)
    chassis = Mesh("testeo/wacky_races/auto_completo.stl")
    chassis.init_gpu_data(pipeline)
    wheel = Mesh("testeo/wacky_races/right_front_wheel.stl",s=1000)
    wheel.init_gpu_data(pipeline)
    platform = Mesh("testeo/wacky_races/circular_platform.stl", s=10000)
    platform.init_gpu_data(pipeline)
    hangar_geometry = Mesh("testeo/wacky_races/platform.stl", s=1000)
    hangar_geometry.init_gpu_data(pipeline)

    

    camera = FreeCamera([-10.5,0,1],"perspective")

    auto= Car(chassis, wheel, platform, camera,[3.5,0,0])
    hangar = Hangar(hangar_geometry, camera,[3.5,0,0])

    auto2= Car(chassis, wheel, platform, camera,[-3.5,0,0])
    hangar2 = Hangar(hangar_geometry, camera,[-3.5,0,0])

    auto3= Car(chassis, wheel, platform, camera,[10.5,0,0])
    hangar3 = Hangar(hangar_geometry, camera,[10.5,0,0])

    auto4= Car(chassis, wheel, platform, camera,[-10.5,0,0])
    hangar4 = Hangar(hangar_geometry, camera,[-10.5,0,0])

    def update(dt):
        pass

    print("Controles Cámara:\n\tWASD: Rotar\n\t Q/E: Acercar/Alejar\n\t1/2: Cambiar tipo de cámara\n\t3/4: Rotación automática plataforma/Cámara" )
    rota="car"
    def update(dt):
        global rota
    #     if controller.is_key_pressed(pyglet.window.key.A):
    #         camera.phi -= dt
        if rota == "camera":
            camera.phi -= dt
        else:
            auto.graph["car"]["rotation"][1] += 2*dt
            auto.graph["platform"]["rotation"][1] += 2*dt
            #auto.graph["car"]["transform"] = tr.rotationZ(dt)
            #auto.graph["platform"]["transform"] = tr.rotationZ(dt)

            auto2.graph["car"]["rotation"][1] += 2*dt
            auto2.graph["platform"]["rotation"][1] += 2*dt
            #auto2.graph["car"]["transform"] = tr.rotationZ(dt)
            #auto2.graph["platform"]["transform"] = tr.rotationZ(dt)

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
        if rota == "camera" and controller.is_key_pressed(pyglet.window.key._3):
             rota = "car"
        if rota == "car" and controller.is_key_pressed(pyglet.window.key._4):
            rota = "camera"

        if controller.is_key_pressed(pyglet.window.key.O):
            camera.pos=[-7,0,0]


        camera.update()

    @controller.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & pyglet.window.mouse.RIGHT:
            controller.program_state["camera"].yaw += dx * 0.01
            controller.program_state["camera"].pitch += dy * 0.01
        

    #draw loop
    @controller.event
    def on_draw():
        controller.clear()
        hangar.draw()
        auto.draw()
        hangar2.draw()
        auto2.draw()
        hangar3.draw()
        auto3.draw()
        hangar4.draw()
        auto4.draw()


    pyglet.clock.schedule_interval(update, 1/60)
    pyglet.app.run()