import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
from PIL import Image

from object3d import Coord3d, Object3d

"""
    SETUP DO PROGRAMA
"""

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
width = 1280
height = 720
window = glfw.create_window(width, height, "Iluminação", None, None)
glfw.make_context_current(window)

# GLSL vertex shader
vertex_code = """
        attribute vec3 position;
        attribute vec2 texture_coord;
        attribute vec3 normals;
        
        varying vec2 out_texture;
        varying vec3 out_fragPos;
        varying vec3 out_normal;
                
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;        
        
        void main(){
            gl_Position = projection * view * model * vec4(position,1.0);
            out_texture = vec2(texture_coord);
            out_fragPos = vec3(  model * vec4(position, 1.0));
            out_normal = vec3( model *vec4(normals, 1.0));            
        }
        """

# Glsl fragment shader
fragment_code = """
        uniform vec3 lightPos; // define coordenadas de posicao da luz
        vec3 lightColor = vec3(1.0, 1.0, 1.0);
        
        uniform float ka; // coeficiente de reflexao ambiente
        uniform float kd; // coeficiente de reflexao difusa
        
        uniform vec3 viewPos; // define coordenadas com a posicao da camera/observador
        uniform float ks; // coeficiente de reflexao especular
        uniform float ns; // expoente de reflexao especular

        varying vec2 out_texture; // recebido do vertex shader
        varying vec3 out_normal; // recebido do vertex shader
        varying vec3 out_fragPos; // recebido do vertex shader
        uniform sampler2D samplerTexture;
        
        void main(){
        
            vec3 ambient = ka * lightColor; // reflexão ambiente     
        
            vec3 norm = normalize(out_normal); // normaliza vetores perpendiculares
            vec3 lightDir = normalize(lightPos - out_fragPos); // direcao da luz
            float diff = max(dot(norm, lightDir), 0.0); // verifica limite angular (entre 0 e 90)
            vec3 diffuse = kd * diff * lightColor; // iluminacao difusa
            
            vec3 viewDir = normalize(viewPos - out_fragPos); // direcao do observador/camera
            vec3 reflectDir = normalize(reflect(-lightDir, norm)); // direcao da reflexao
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), ns);
            vec3 specular = ks * spec * lightColor; // reflexão especular    
            
            vec4 texture = texture2D(samplerTexture, out_texture);
            vec4 result = vec4((ambient + diffuse + specular),1.0) * texture; // aplica iluminacao
            gl_FragColor = result; // modelo de iluminação
        }
        """

# Requisita slots da GPU
program  = glCreateProgram()
vertex   = glCreateShader(GL_VERTEX_SHADER)
fragment = glCreateShader(GL_FRAGMENT_SHADER)

# Associa o código-fonte aos slots solicitados
glShaderSource(vertex, vertex_code)
glShaderSource(fragment, fragment_code)

# Compila os shaders
glCompileShader(vertex)
if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
    error = glGetShaderInfoLog(vertex).decode()
    print(error)
    raise RuntimeError("Erro de compilacao do Vertex Shader")
glCompileShader(fragment)
if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
    error = glGetShaderInfoLog(fragment).decode()
    print(error)
    raise RuntimeError("Erro de compilacao do Fragment Shader")

# Conecta os shaders com o programa
glAttachShader(program, vertex)
glAttachShader(program, fragment)

# Constrói o programa
glLinkProgram(program)
if not glGetProgramiv(program, GL_LINK_STATUS):
    print(glGetProgramInfoLog(program))
    raise RuntimeError('Linking error')
    
# Faz com que o programa seja o programa padrão
glUseProgram(program)

# Ativa texturas
glEnable(GL_TEXTURE_2D)
qtd_texturas = 10
glGenTextures(qtd_texturas)

"""
    FUNCOES DE CARREGAMENTO
"""

object3d_list = {
    'caixa': Object3d('caixa2.obj', ['caixa_madeira.jpg'], r=Coord3d(0.0, 1.0, 0.0)),
    'luz': Object3d('luz.obj', ['luz.png'], r=Coord3d(0.0, 0.0, 1.0), s=Coord3d(0.1, 0.1, 0.1)),
}

# Gera listas com todas as coordenadas
vertices_list = []
texture_coords_list = []
normals_list = []
for key, object3d in object3d_list.items():
    vertices_list += object3d.vertices_list
    texture_coords_list += object3d.texture_coords_list
    normals_list += object3d.normals_list

"""
    ENVIO DE DADOS PARA A GPU
"""

# Requisitar três slots para a GPU:
#   Um para enviar coordenadas dos vértices.
#   Um para enviar coordenadas de texturas.
#   Um para enviar coordenadas de normals para iluminação.
buffer = glGenBuffers(3)

# Enviando coordenadas de vértices para a GPU
vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
vertices['position'] = vertices_list
glBindBuffer(GL_ARRAY_BUFFER, buffer[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
stride = vertices.strides[0]
offset = ctypes.c_void_p(0)
loc_vertices = glGetAttribLocation(program, "position")
glEnableVertexAttribArray(loc_vertices)
glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

# Enviando coordenadas de textura para a GPU
textures = np.zeros(len(texture_coords_list), [("position", np.float32, 2)])
textures['position'] = texture_coords_list
glBindBuffer(GL_ARRAY_BUFFER, buffer[1])
glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
stride = textures.strides[0]
offset = ctypes.c_void_p(0)
loc_texture_coord = glGetAttribLocation(program, "texture_coord")
glEnableVertexAttribArray(loc_texture_coord)
glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)

# Enviando dados de Iluminação a GPU
normals = np.zeros(len(normals_list), [("position", np.float32, 3)])
normals['position'] = normals_list
glBindBuffer(GL_ARRAY_BUFFER, buffer[2])
glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
stride = normals.strides[0]
offset = ctypes.c_void_p(0)
loc_normals_coord = glGetAttribLocation(program, "normals")
glEnableVertexAttribArray(loc_normals_coord)
glVertexAttribPointer(loc_normals_coord, 3, GL_FLOAT, False, stride, offset)

# Desenha os modelos
def draw_object3d(object3d: Object3d, light=False):

    mat_model = object3d.model()
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
    
    ka = 0.1 # Coeficiente de reflexao ambiente do modelo
    kd = 0.1 # Coeficiente de reflexao difusa do modelo
    ks = 0.9 # Coeficiente de reflexao especular do modelo
    ns = ns_inc # Expoente de reflexao especular
    
    # Recupera localização das variáveis na GPU
    loc_ka = glGetUniformLocation(program, "ka")
    loc_kd = glGetUniformLocation(program, "kd")
    loc_ks = glGetUniformLocation(program, "ks")
    loc_ns = glGetUniformLocation(program, "ns")
    
    # Insere o valor das variáveis
    glUniform1f(loc_ka, ka)
    glUniform1f(loc_kd, kd)
    glUniform1f(loc_ks, ks)
    glUniform1f(loc_ns, ns)

    # Se objeto produzir luz, inserir luz
    if light:
        loc_light_pos = glGetUniformLocation(program, "lightPos") # Localizacao da variavel lightPos na GPU
        glUniform3f(loc_light_pos, object3d.t.x, object3d.t.y, object3d.t.z) # Define a posição da luz
    
    for texture in object3d.texture_list:
        glBindTexture(GL_TEXTURE_2D, texture) # Define id da textura do modelo
    glDrawArrays(GL_TRIANGLES, object3d.start_vertex, object3d.vertex_count) # Renderiza

"""
    CAMERA E MOUSE
"""

camera_pos   = glm.vec3(0.0,  0.0,  15.0)
camera_front = glm.vec3(0.0,  0.0, -1.0)
camera_up    = glm.vec3(0.0,  1.0,  0.0)
polygonal_mode = False

def key_event(window,key,scancode,action,mods):

    global camera_pos, camera_front, camera_up, polygonal_mode
    global ns_inc
    
    camera_speed = 0.1
    if key == glfw.KEY_W and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos += camera_speed * camera_front
    if key == glfw.KEY_S and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos -= camera_speed * camera_front
    if key == glfw.KEY_A and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos -= glm.normalize(glm.cross(camera_front, camera_up)) * camera_speed
    if key == glfw.KEY_D and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos += glm.normalize(glm.cross(camera_front, camera_up)) * camera_speed
    if key == glfw.KEY_SPACE and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos += camera_speed * camera_up
    if key == glfw.KEY_LEFT_SHIFT and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos -= camera_speed * camera_up
    if key == glfw.KEY_P and action==glfw.PRESS:
        polygonal_mode = not polygonal_mode
    if key == glfw.KEY_UP and (action==glfw.PRESS or glfw.REPEAT):
        ns_inc = ns_inc * 2
    if key == glfw.KEY_DOWN and (action==glfw.PRESS or glfw.REPEAT):
        ns_inc = ns_inc / 2
        
firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  width/2
lastY =  height/2

def mouse_event(window, xpos, ypos):
    global firstMouse, camera_front, yaw, pitch, lastX, lastY
    if firstMouse:
        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset
    
    if pitch >= 90.0:
        pitch = 90.0
    if pitch <= -90.0:
        pitch = -90.0

    front = glm.vec3()
    front.x = math.cos(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    front.y = math.sin(glm.radians(pitch))
    front.z = math.sin(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    camera_front = glm.normalize(front)
    
glfw.set_key_callback(window,key_event)
glfw.set_cursor_pos_callback(window, mouse_event)

# Matriz view
def view():
    global camera_pos, camera_front, camera_up
    mat_view = glm.lookAt(camera_pos, camera_pos + camera_front, camera_up)
    mat_view = np.array(mat_view)
    return mat_view

# Matriz projection
def projection():
    # perspective parameters: fovy, aspect, near, far
    mat_projection = glm.perspective(glm.radians(45.0), width/height, 0.1, 1000.0)
    mat_projection = np.array(mat_projection)    
    return mat_projection

"""
    EXECUCAO DO PROGRAMA
"""

# Exibir a janela
glfw.show_window(window)
glfw.set_cursor_pos(window, lastX, lastY)
glEnable(GL_DEPTH_TEST) # importante para 3D

ang = 0.1
ns_inc = 32
    
while not glfw.window_should_close(window):

    glfw.poll_events() 
    ang += 0.001
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(0.2, 0.2, 0.2, 1.0)
    
    if polygonal_mode==True:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    if polygonal_mode==False:
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    
    draw_object3d(object3d_list['caixa'])
    
    ang += 0.05
    object3d_list['luz'].transform(Coord3d(math.cos(ang)*0.5, math.sin(ang)*0.5, 3.0))
    draw_object3d(object3d_list['luz'], light=True)
    
    mat_view = view()
    loc_view = glGetUniformLocation(program, "view")
    glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

    mat_projection = projection()
    loc_projection = glGetUniformLocation(program, "projection")
    glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    
    
    # atualizando a posicao da camera/observador na GPU para calculo da reflexao especular
    loc_view_pos = glGetUniformLocation(program, "viewPos") # recuperando localizacao da variavel viewPos na GPU
    glUniform3f(loc_view_pos, camera_pos[0], camera_pos[1], camera_pos[2]) # posicao da camera/observador (x,y,z)
    
    glfw.swap_buffers(window)

glfw.terminate()