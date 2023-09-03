import pyglet
from OpenGL import GL
import numpy as np
import sys
import os
#sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__))))))
import grafica.transformations as tr

WIDTH = 480
HEIGHT = 640

class Controller(pyglet.window.Window):
    def __init__(self, title,*args,**kargs):
        super().__init__(*args,**kargs)
        self.set_minimum_size(80,80)
        self.set_caption(title)

    def init(self):
        GL.glClearColor(0, 0, 0, 1.0) #no sé qué hace

class ModelController():
    def __init__(self):
        self.intensity = 1.0
        self.position = np.array([0, 0, 0], dtype=np.float32)
        self.rotation = np.array([0, 0, 0], dtype=np.float32)
        self.scale = np.array([1, 1, 1], dtype=np.float32)

    def get_intensity(self):
        return self.intensity
    
    def get_transform(self):
        translation_matrix = tr.translate(self.position[0], self.position[1], self.position[2])
        rotation_matrix = tr.rotationX(self.rotation[0]) @ tr.rotationY(self.rotation[1]) @ tr.rotationZ(self.rotation[2])
        scale_matrix = tr.scale(self.scale[0], self.scale[1], self.scale[2])
        return translation_matrix @ rotation_matrix @ scale_matrix
    
#------------------------------------------------------------
# Implementación de pyglet
#------------------------------------------------------------
class Pipeline(pyglet.graphics.shader.ShaderPogram):
    def __init__(self, vertex_source, fragment_source):
        vert_shader = pyglet.graphics.shader.Shader(vertex_source,"vertex")
        frag_shader = pyglet.graphics.shader.Shader(fragment_source,"fragment")
        super().__init__(vert_shader, frag_shader)

    def set_uniform(self, name, value, type):
        uniform = self[name]
        if uniform is None:
            print(f"Warning: uniform {name} does not exist")
            return
        if type == "matrix":
            self[name] == np.reshape(value, (16, 1), order="F")
        elif type == "float":
            self[name] = value


class Model():
    def __init__(self, vertex_data, index_data=None):
        count = len(vertex_data) // 6
        vertex_data = np.array(vertex_data, dtype=np.float32)
        vertex_data.shape = (count, 6)
        self.position_data = vertex_data[:, 0:3].flatten()
        self.color_data = vertex_data[:, 3:6].flatten()

        self.index_data = index_data
        if index_data is not None:
            self.index_data = np.array(index_data, dtype=np.uint32)

        self.gpu_data = None

    def init_gpu_data(self, pipeline):
        if self.index_data is not None:
            self.gpu_data = pipeline.vertex_list_indexed(len(self.position_data) // 3, GL.GL_TRIANGLES, self.index_data)
        else:
            self.gpu_data = pipeline.vertex_list(len(self.position_data) // 3, GL.GL_TRIANGLES)

        self.gpu_data.position[:] = self.position_data
        self.gpu_data.color[:] = self.color_data
    
    def draw(self, mode = GL.GL_TRIANGLES):
        self.gpu_data.draw(mode)

#------------------------------------------------------------
#------------------------------------------------------------        

vertex_source_code = """
#version 330

in vec3 position;
in vec3 color;

uniform float u_intensity = 1.0f;
uniform mat4 u_transform = mat4(1.0);

out vec3 fragColor;

void main()
{
    fragColor = color * u_intensity;
    gl_Position = u_transform * vec4(position, 1.0f);
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

if __name__=="__main__":
    controller = Controller("Tarea 0 - Hexagono de Colores", width=WIDTH, height=HEIGHT, resizable=True)
    
    pipeline = Pipeline(vertex_source_code, fragment_source_code)


    Hex = Model([-0.2, -0.2, -0.1,      1, 1, 1,
                0.2, -0.2, -0.1,      1, 0, 0,
                0.4,  0.0, -0.1,      0, 1, 0,
                0.2,  0.2, -0.1,      0, 0, 1,
                -0.2,  0.2, -0.1,      1, 0, 1,
                -0.4,  0.0, -0.1,      1, 1, 0,
                -0.2, -0.2,  0.1,      0, 1, 1,
                0.2, -0.2,  0.1,      0, 0, 0,
                0.4,  0.0,  0.1,      0.5, 0.5, 0.5,
                0.2,  0.2,  0.1,      0.5, 0, 0,
                -0.2,  0.2,  0.1,      0, 0.5, 0.5,
                -0.4,  0.0,  0.1,      0, 0, 0.5], [
    0, 1, 2,
    0, 2, 3,
    0, 3, 4,
    0, 4, 5,
    6, 7, 8,
    6, 8, 9,
    6, 9, 10,
    6, 10, 11

    ])

    Hex.init_gpu_data(pipeline)
    Hex_controller = ModelController()

indices = np.array([
    0, 1, 2,
    0, 2, 3,
    0, 3, 4,
    0, 4, 5,
    6, 7, 8,
    6, 8, 9,
    6, 9, 10,
    6, 10, 11

    ], dtype=np.uint32)

@controller.event
def on_draw():
    controller.clear()
    pipeline.use()
    pipeline.set_uniform("u_intensity", Hex_controller.get_intensity(), "float")
    pipeline.set_uniform("u_transform", Hex_controller.get_transform(), "matrix")
    Hex.draw()
pyglet.app.run()