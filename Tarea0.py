import pyglet
from OpenGL import GL
import numpy as np

WIDTH = 480
HEIGHT = 640
class Controller(pyglet.window.Window):
    def __init__(self, title,*args,**kargs):
        super().__init__(*args,**kargs)
        self.set_minimum_size(80,80)
        self.set_caption(title)
        

if __name__=="__main__":
    controller = Controller("Tarea 0 - Hexagono de Colores", width=WIDTH, height=HEIGHT, resizable=True)
    
    vertex_source_code = """
        #version 330
        
        in vec2 position;
        in vec3 color;
        in float intensity;

        out vec3 fragColor;
        out float fragIntensity;

        void main()
        {
            fragColor = color;
            fragIntensity = intensity;
            gl_Position = vec4(position, 0.0f, 1.0f);
        
        }
    """

    fragment_source_code = """
        #version 330
        
        in vec3 fragColor;
        in float fragIntensity;
        out vec4 outColor;
        
        void main()
        {
            outColor = fragIntensity * vec4(fragColor, 1.0f);
        }
    """

vert_shader = pyglet.graphics.shader.Shader(vertex_source_code, "vertex")
frag_shader =pyglet.graphics.shader.Shader(fragment_source_code,"fragment")

pipeline = pyglet.graphics.shader.ShaderProgram(vert_shader, frag_shader)

positions = np.array([
        -0.2, -0.2,
         0.2, -0.2, 
         0.4,  0.0,
         0.2,  0.2,
        -0.2,  0.2,
        -0.4,  0.0

    ], dtype=np.float32)

colors = np.array([
        1, 0, 0,
        0, 1, 0,
        0, 0, 1,
        1, 1, 1,
        0, 1, 1,
        1, 1, 0
    ], dtype=np.float32)

intensities = np.array([
        1, 1, 1, 1, 1, 1
    ], dtype=np.float32)

indices = np.array([
    0, 1, 2,
    0, 2, 5,
    5, 2, 3,
    5, 3, 4
    ], dtype=np.uint32)

gpu_hex = pipeline.vertex_list_indexed(6, GL.GL_TRIANGLES, indices)
gpu_hex.position = positions
gpu_hex.color = colors
gpu_hex.intensity = intensities

@controller.event
def on_draw():
    GL.glClearColor(0,0,0,1.0)
    controller.clear()
    pipeline.use()
    gpu_hex.draw(GL.GL_TRIANGLES)  

pyglet.app.run()