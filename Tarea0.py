import pyglet
from OpenGL import GL
import numpy as np

class Controller(pyglet.window.Window):
    def __init__(self, title,*args,**kargs):
        super().__init__(*args,**kargs)
        self.set_minimum_size(80,80)
        self.set_caption(title)
        


if __name__=="__main__":
    controller = Controller("Tarea 0", resizable=True)
    
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
        -0.5, -0.5,
         0.5, -0.5, 
         0.0,  0.5
    ], dtype=np.float32)

colors = np.array([
        1, 0, 0,
        0, 1, 0,
        0, 0, 1
    ], dtype=np.float32)

intensities = np.array([
        1, 0.5, 0
    ], dtype=np.float32)

gpu_triangle = pipeline.vertex_list(3, GL.GL_TRIANGLES)
gpu_triangle.position = positions
gpu_triangle.color = colors
gpu_triangle.intensity = intensities

@controller.event
def on_draw():
    GL.glClearColor(0,0,0,1.0)
    controller.clear()
    pipeline.use()
    gpu_triangle.draw(GL.GL_TRIANGLES)  
    
pyglet.app.run()