from functools import total_ordering
import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
from PIL import Image

from collections import namedtuple

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

"""
    FUNCOES DE CARREGAMENTO
"""

# Carrega os dados de um arquivo .obj
def load_obj(filename):

    vertices = []
    normals = []
    texture_coords = []
    faces = []
    material = None

    for line in open(filename, "r"): # para cada linha do arquivo .obj
        if line.startswith('#'): # Comentários
            continue
        values = line.split() # quebra a linha por espaço
        if not values:
            continue
        if values[0] == 'v': # Vertices
            vertices.append(values[1:4])
        if values[0] == 'vn': # Normais
            normals.append(values[1:4])
        elif values[0] == 'vt': # Vertices das texturas
            texture_coords.append(values[1:3])
        elif values[0] in ('usemtl', 'usemat'): # Materiais
            material = values[1]
        elif values[0] == 'f': # Faces
            face = []
            face_texture = []
            face_normals = []
            for v in values[1:]:
                w = v.split('/')
                face.append(int(w[0]))
                face_normals.append(int(w[2]))
                if len(w) >= 2 and len(w[1]) > 0:
                    face_texture.append(int(w[1]))
                else:
                    face_texture.append(0)
            faces.append((face, face_texture, face_normals, material))

    obj = {}
    obj['vertices'] = vertices
    obj['normals'] = normals
    obj['texture_coords'] = texture_coords
    obj['faces'] = faces

    return obj

glEnable(GL_TEXTURE_2D)
qtd_texturas = 10
glGenTextures(qtd_texturas)

def load_texture(texture_id, img_filepath):
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    img = Image.open(img_filepath)
    img_width = img.size[0]
    img_height = img.size[1]
    image_data = img.tobytes("raw", "RGB", 0, -1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)

"""
    CARREGAMENTO DE OBJETOS
"""

Coord3d = namedtuple('Coord3d', 'x y z') # ? Talvez substituir por glm.vec3

class Object3d:

    vertex_total = 0
    texture_count = 0

    def __init__(self, obj_filepath, texture_filepath_list=[], angle=0, r=Coord3d(0.0,0.0,0.0), t=Coord3d(0.0,0.0,0.0), s=Coord3d(1.0,1.0,1.0)):

        print(f'Loading {obj_filepath}')
        obj = load_obj(obj_filepath)
        self.vertices_list = []
        self.texture_coords_list = []
        self.normals_list = []
        for face in obj['faces']:
            for vertex_index in face[0]:
                self.vertices_list.append( obj['vertices'][vertex_index-1] )
            for texture_coord_index in face[1]:
                self.texture_coords_list.append( obj['texture_coords'][texture_coord_index-1] )
            for normal_index in face[2]:
                self.normals_list.append( obj['normals'][normal_index-1] )
        self.start_vertex = Object3d.vertex_total
        self.vertex_count = len(self.vertices_list)
        Object3d.vertex_total += self.vertex_count

        self.texture_list = []
        for texture_filepath in texture_filepath_list: # Load textures
            print(f'Loading {texture_filepath}')
            load_texture(Object3d.texture_count, texture_filepath)
            self.texture_list.append(Object3d.texture_count)
            Object3d.texture_count += 1
        
        self.angle = angle
        self.r = r
        self.t = t
        self.s = s

    def model(self):
        angle_rad = math.radians(self.angle)
        matrix_transform = glm.mat4(1.0) # Matriz identidade
        matrix_transform = glm.rotate(matrix_transform, angle_rad, glm.vec3(self.r.x, self.r.y, self.r.z)) # Rotação
        matrix_transform = glm.translate(matrix_transform, glm.vec3(self.t.x, self.t.y, self.t.z)) # Translação
        matrix_transform = glm.scale(matrix_transform, glm.vec3(self.s.x, self.s.y, self.s.z)) # Escala
        matrix_transform = np.array(matrix_transform)
        return matrix_transform
    
    def transform(self, t: Coord3d):
        self.t = t

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
    
    cameraSpeed = 0.05
    if key == glfw.KEY_W and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos += cameraSpeed * camera_front
    if key == glfw.KEY_S and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos -= cameraSpeed * camera_front
    if key == glfw.KEY_A and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos -= glm.normalize(glm.cross(camera_front, camera_up)) * cameraSpeed
    if key == glfw.KEY_D and action in (glfw.PRESS, glfw.REPEAT):
        camera_pos += glm.normalize(glm.cross(camera_front, camera_up)) * cameraSpeed
    if key == glfw.KEY_P and action==glfw.PRESS and polygonal_mode==True:
        polygonal_mode=False
    else:
        polygonal_mode=True
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

    sensitivity = 0.3 
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    
    if pitch >= 90.0: pitch = 90.0
    if pitch <= -90.0: pitch = -90.0

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
    mat_view = glm.lookAt(camera_pos, camera_pos + camera_front, camera_up);
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