import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
from PIL import Image

from program import Program

program = Program()

def load_model_from_file(filename):
    """Loads a Wavefront OBJ file. """
    objects = {}
    vertices = []
    normals = []
    texture_coords = []
    faces = []

    material = None

    # abre o arquivo obj para leitura
    for line in open(filename, "r"): ## para cada linha do arquivo .obj
        if line.startswith('#'): continue ## ignora comentarios
        values = line.split() # quebra a linha por espaço
        if not values: continue


        ### recuperando vertices
        if values[0] == 'v':
            vertices.append(values[1:4])

        ### recuperando vertices
        if values[0] == 'vn':
            normals.append(values[1:4])

        ### recuperando coordenadas de textura
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])

        ### recuperando faces 
        elif values[0] in ('usemtl', 'usemat'):
            material = values[1]
        elif values[0] == 'f':
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

    model = {}
    model['vertices'] = vertices
    model['texture'] = texture_coords
    model['faces'] = faces
    model['normals'] = normals

    return model

glEnable(GL_TEXTURE_2D)
qtd_texturas = 10
textures = glGenTextures(qtd_texturas)

def load_texture_from_file(texture_id, img_textura):
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    img = Image.open(img_textura)
    img_width = img.size[0]
    img_height = img.size[1]
    image_data = img.tobytes("raw", "RGB", 0, -1)
    #image_data = np.array(list(img.getdata()), np.uint8)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
# ### A lista abaixo armazena todos os vertices carregados dos arquivos

vertices_list = []    
normals_list = []    
textures_coord_list = []
# ### Vamos carregar cada modelo e definir funções para desenhá-los

modelo = load_model_from_file('caixa2.obj')

### inserindo vertices do modelo no vetor de vertices
print('Processando modelo cube.obj. Vertice inicial:',len(vertices_list))
for face in modelo['faces']:
    for vertice_id in face[0]:
        vertices_list.append( modelo['vertices'][vertice_id-1] )
    for texture_id in face[1]:
        textures_coord_list.append( modelo['texture'][texture_id-1] )
    for normal_id in face[2]:
        normals_list.append( modelo['normals'][normal_id-1] )
print('Processando modelo cube.obj. Vertice final:',len(vertices_list))

### inserindo coordenadas de textura do modelo no vetor de texturas


### carregando textura equivalente e definindo um id (buffer): use um id por textura!
load_texture_from_file(0,'caixa_madeira.jpg')

modelo = load_model_from_file('luz.obj')

### inserindo vertices do modelo no vetor de vertices
print('Processando modelo luz.obj. Vertice inicial:',len(vertices_list))
for face in modelo['faces']:
    for vertice_id in face[0]:
        vertices_list.append( modelo['vertices'][vertice_id-1] )
    for texture_id in face[1]:
        textures_coord_list.append( modelo['texture'][texture_id-1] )
    for normal_id in face[2]:
        normals_list.append( modelo['normals'][normal_id-1] )
print('Processando modelo luz.obj. Vertice final:',len(vertices_list))

### inserindo coordenadas de textura do modelo no vetor de texturas


### carregando textura equivalente e definindo um id (buffer): use um id por textura!
load_texture_from_file(1,'luz.png')
# ### Para enviar nossos dados da CPU para a GPU, precisamos requisitar slots.
# 
# Agora requisitaremos três slots.
# * Um para enviar coordenadas dos vértices.
# * Um para enviar coordenadas de texturas.
# * Um para enviar coordenadas de normals para iluminação.

# Request a buffer slot from GPU
buffer = glGenBuffers(3)
# ###  Enviando coordenadas de vértices para a GPU

vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
vertices['position'] = vertices_list


# Upload data
glBindBuffer(GL_ARRAY_BUFFER, buffer[0])
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
stride = vertices.strides[0]
offset = ctypes.c_void_p(0)
loc_vertices = glGetAttribLocation(program.program, "position")
glEnableVertexAttribArray(loc_vertices)
glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)
# ###  Enviando coordenadas de textura para a GPU

textures = np.zeros(len(textures_coord_list), [("position", np.float32, 2)]) # duas coordenadas
textures['position'] = textures_coord_list


# Upload data
glBindBuffer(GL_ARRAY_BUFFER, buffer[1])
glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
stride = textures.strides[0]
offset = ctypes.c_void_p(0)
loc_texture_coord = glGetAttribLocation(program.program, "texture_coord")
glEnableVertexAttribArray(loc_texture_coord)
glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)
# ###  Enviando dados de Iluminação a GPU
# #### Dados de iluminação: vetores normais

normals = np.zeros(len(normals_list), [("position", np.float32, 3)]) # três coordenadas
normals['position'] = normals_list


# Upload coordenadas normals de cada vertice
glBindBuffer(GL_ARRAY_BUFFER, buffer[2])
glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
stride = normals.strides[0]
offset = ctypes.c_void_p(0)
loc_normals_coord = glGetAttribLocation(program.program, "normals")
glEnableVertexAttribArray(loc_normals_coord)
glVertexAttribPointer(loc_normals_coord, 3, GL_FLOAT, False, stride, offset)
# ### Desenhando nossos modelos
# * Cada modelo tem um Model para posicioná-los no mundo.
# * É necessário saber qual a posição inicial e total de vértices de cada modelo.
# * É necessário indicar qual o ID da textura do modelo.

def desenha_caixa():
    

    # aplica a matriz model
    angle = 0.0
    
    r_x = 0.0; r_y = 1.0; r_z = 0.0;
    
    # translacao
    t_x = 0.0; t_y = 0.0; t_z = 0.0;
    
    # escala
    s_x = 1.0; s_y = 1.0; s_z = 1.0;
    
    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program.program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
       
    
    #### define parametros de ilumincao do modelo
    ka = 0.1 # coeficiente de reflexao ambiente do modelo
    kd = 0.1 # coeficiente de reflexao difusa do modelo
    ks = 0.9 # coeficiente de reflexao especular do modelo
    ns = ns_inc # expoente de reflexao especular
    
    loc_ka = glGetUniformLocation(program.program, "ka") # recuperando localizacao da variavel ka na GPU
    glUniform1f(loc_ka, ka) ### envia ka pra gpu
    
    loc_kd = glGetUniformLocation(program.program, "kd") # recuperando localizacao da variavel kd na GPU
    glUniform1f(loc_kd, kd) ### envia kd pra gpu    
    
    loc_ks = glGetUniformLocation(program.program, "ks") # recuperando localizacao da variavel ks na GPU
    glUniform1f(loc_ks, ks) ### envia ks pra gpu        
    
    loc_ns = glGetUniformLocation(program.program, "ns") # recuperando localizacao da variavel ns na GPU
    glUniform1f(loc_ns, ns) ### envia ns pra gpu        

    
    #define id da textura do modelo
    glBindTexture(GL_TEXTURE_2D, 0)
    
    
    # desenha o modelo
    glDrawArrays(GL_TRIANGLES, 0, 36) ## renderizando

def desenha_luz(t_x, t_y, t_z):
    

    # aplica a matriz model
    angle = 0.0
    
    r_x = 0.0; r_y = 0.0; r_z = 1.0;
    
    # translacao
    #t_x = 0.0; t_y = 0.0; t_z = 0.0;
    
    # escala
    s_x = 0.1; s_y = 0.1; s_z = 0.1;
    
    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program.program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
       
    
    #### define parametros de ilumincao do modelo
    ka = 1 # coeficiente de reflexao ambiente do modelo
    kd = 1 # coeficiente de reflexao difusa do modelo
    ks = 1 # coeficiente de reflexao especular do modelo
    ns = 1000.0 # expoente de reflexao especular
    
    loc_ka = glGetUniformLocation(program.program, "ka") # recuperando localizacao da variavel ka na GPU
    glUniform1f(loc_ka, ka) ### envia ka pra gpu
    
    loc_kd = glGetUniformLocation(program.program, "kd") # recuperando localizacao da variavel kd na GPU
    glUniform1f(loc_kd, kd) ### envia kd pra gpu    
    
    loc_ks = glGetUniformLocation(program.program, "ks") # recuperando localizacao da variavel ks na GPU
    glUniform1f(loc_ks, ks) ### envia ns pra gpu        
    
    loc_ns = glGetUniformLocation(program.program, "ns") # recuperando localizacao da variavel ns na GPU
    glUniform1f(loc_ns, ns) ### envia ns pra gpu            
    
    loc_light_pos = glGetUniformLocation(program.program, "lightPos") # recuperando localizacao da variavel lightPos na GPU
    glUniform3f(loc_light_pos, t_x, t_y, t_z) ### posicao da fonte de luz
        
    
    #define id da textura do modelo
    glBindTexture(GL_TEXTURE_2D, 1)
    
    
    # desenha o modelo
    glDrawArrays(GL_TRIANGLES, 36, 36) ## renderizando
# ### Eventos para modificar a posição da câmera.
# 
# * Usei as teclas A, S, D e W para movimentação no espaço tridimensional.
# * Usei a posição do mouse para "direcionar" a câmera.

cameraPos   = glm.vec3(0.0,  0.0,  15.0);
cameraFront = glm.vec3(0.0,  0.0, -1.0);
cameraUp    = glm.vec3(0.0,  1.0,  0.0);


polygonal_mode = False

def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode
    global ns_inc
    
    cameraSpeed = 0.05
    if key == 87 and (action==1 or action==2): # tecla W
        cameraPos += cameraSpeed * cameraFront
    
    if key == 83 and (action==1 or action==2): # tecla S
        cameraPos -= cameraSpeed * cameraFront
    
    if key == 65 and (action==1 or action==2): # tecla A
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == 68 and (action==1 or action==2): # tecla D
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == 80 and action==1 and polygonal_mode==True:
        polygonal_mode=False
    else:
        if key == 80 and action==1 and polygonal_mode==False:
            polygonal_mode=True
        
    if key == 265 and (action==1 or action==2): # tecla D
        ns_inc = ns_inc * 2
        
    if key == 264 and (action==1 or action==2): # tecla D
        ns_inc = ns_inc / 2
        
firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  width/2
lastY =  height/2

def mouse_event(window, xpos, ypos):
    global firstMouse, cameraFront, yaw, pitch, lastX, lastY
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

    yaw += xoffset;
    pitch += yoffset;

    
    if pitch >= 90.0: pitch = 90.0
    if pitch <= -90.0: pitch = -90.0

    front = glm.vec3()
    front.x = math.cos(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    front.y = math.sin(glm.radians(pitch))
    front.z = math.sin(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)


    
glfw.set_key_callback(program.window,key_event)
glfw.set_cursor_pos_callback(program.window, mouse_event)
# ### Matrizes Model, View e Projection
# 
# Teremos uma aula específica para entender o seu funcionamento.

def model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    
    angle = math.radians(angle)
    
    matrix_transform = glm.mat4(1.0) # instanciando uma matriz identidade
       
    # aplicando rotacao
    matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))
        
  
    # aplicando translacao
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))    
    
    # aplicando escala
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))
    
    matrix_transform = np.array(matrix_transform)
    
    return matrix_transform

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
    mat_view = np.array(mat_view)
    return mat_view

def projection():
    global height, width
    # perspective parameters: fovy, aspect, near, far
    mat_projection = glm.perspective(glm.radians(45.0), width/height, 0.1, 1000.0)
    mat_projection = np.array(mat_projection)    
    return mat_projection
# ### Nesse momento, exibimos a janela.

glfw.show_window(program.window)
glfw.set_cursor_pos(program.window, lastX, lastY)
# ### Loop principal da janela.
# Enquanto a janela não for fechada, esse laço será executado. É neste espaço que trabalhamos com algumas interações com a OpenGL.

glEnable(GL_DEPTH_TEST) ### importante para 3D
   
ang = 0.1
ns_inc = 32
    
while not glfw.window_should_close(program.window):

    glfw.poll_events() 
    ang += 0.001
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(0.2, 0.2, 0.2, 1.0)
    
    if polygonal_mode==True:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    if polygonal_mode==False:
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    
    desenha_caixa()   
    
    ang += 0.05
    desenha_luz(math.cos(ang)*0.5, math.sin(ang)*0.5, 3.0)   


    
    mat_view = view()
    loc_view = glGetUniformLocation(program.program, "view")
    glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

    mat_projection = projection()
    loc_projection = glGetUniformLocation(program.program, "projection")
    glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    
    
    # atualizando a posicao da camera/observador na GPU para calculo da reflexao especular
    loc_view_pos = glGetUniformLocation(program.program, "viewPos") # recuperando localizacao da variavel viewPos na GPU
    glUniform3f(loc_view_pos, cameraPos[0], cameraPos[1], cameraPos[2]) ### posicao da camera/observador (x,y,z)
    
    glfw.swap_buffers(program.window)

glfw.terminate()
# # Exercício
# 
# * Aplique o modelo de iluminação especular em uma esfera.
# 
# * Faça com que o parâmetro expoente de reflexão especular seja incrementado/decrementado por alguma tecla. OBS: faça incremento na potência de dois.


