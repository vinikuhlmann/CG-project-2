import os
import numpy as np
from OpenGL.GL import *
from PIL import Image
from model import *
from glfw_instance import GlfwInstance as GI

# Carrega os dados de um arquivo .obj
def load_obj(filepath):

    vertices = []
    normals = []
    texture_coords = []
    faces = []
    material = None

    for line in open(filepath, "r"): # para cada linha do arquivo .obj
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

# Carrega uma imagem de textura
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

class ModelManager:

    "static"
    main_dir = 'models'
    models = {}
    vertices = []
    texture_coords = []
    normals = []
    vertex_count = 0
    texture_count = 0

    # Carrega um modelo
    @staticmethod
    def load_model(model_dir, light_source=False, angle=0, r=Coord3d(0.0,1.0,0.0), t=Coord3d(0.0,0.0,0.0), s=Coord3d(1.0,1.0,1.0)):
        print(f'Loading model {model_dir}')
        model_name = model_dir
        model_dir = os.path.join(ModelManager.main_dir, model_dir)
        textures = []
        for filepath in os.listdir(model_dir):
            print(f'\tLoading {filepath}')
            filepath = os.path.join(model_dir, filepath)

            # Carregamento de arquivo .obj
            if filepath.endswith('.obj'):
                obj = load_obj(filepath)
                start_vertex = ModelManager.vertex_count
                if not light_source:
                    model = Model(obj, start_vertex, angle, r, t, s)
                else:
                    model = LightModel(obj, start_vertex, angle, r, t, s)
                ModelManager.vertex_count += model.vertex_count
            
            # Carregamento de textura
            elif filepath.endswith(('.jpg', '.png')):
                load_texture(ModelManager.texture_count, filepath)
                textures.append(ModelManager.texture_count)
                ModelManager.texture_count += 1
        
        model.add_textures(textures)
        
        # Adiciona o modelo na lista e guarda suas informações
        ModelManager.models[model_name] = model
        ModelManager.vertices += model.vertices
        ModelManager.texture_coords += model.texture_coords
        ModelManager.normals += model.normals
    
    def send_to_GPU():

        # Requisitar três slots para a GPU:
        #   Um para enviar coordenadas dos vértices.
        #   Um para enviar coordenadas de texturas.
        #   Um para enviar coordenadas de normals para iluminação.
        buffer = glGenBuffers(3)

        # Enviando coordenadas de vértices para a GPU
        vertices = np.zeros(len(ModelManager.vertices), [("position", np.float32, 3)])
        vertices['position'] = ModelManager.vertices
        glBindBuffer(GL_ARRAY_BUFFER, buffer[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        stride = vertices.strides[0]
        offset = ctypes.c_void_p(0)
        loc_vertices = glGetAttribLocation(GI.program, "position")
        glEnableVertexAttribArray(loc_vertices)
        glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

        # Enviando coordenadas de textura para a GPU
        textures = np.zeros(len(ModelManager.texture_coords), [("position", np.float32, 2)])
        textures['position'] = ModelManager.texture_coords
        glBindBuffer(GL_ARRAY_BUFFER, buffer[1])
        glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
        stride = textures.strides[0]
        offset = ctypes.c_void_p(0)
        loc_texture_coord = glGetAttribLocation(GI.program, "texture_coord")
        glEnableVertexAttribArray(loc_texture_coord)
        glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)

        # Enviando dados de Iluminação a GPU
        normals = np.zeros(len(ModelManager.normals), [("position", np.float32, 3)])
        normals['position'] = ModelManager.normals
        glBindBuffer(GL_ARRAY_BUFFER, buffer[2])
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        stride = normals.strides[0]
        offset = ctypes.c_void_p(0)
        loc_normals_coord = glGetAttribLocation(GI.program, "normals")
        glEnableVertexAttribArray(loc_normals_coord)
        glVertexAttribPointer(loc_normals_coord, 3, GL_FLOAT, False, stride, offset)
    
    def draw_models(ns_inc):

        for key, model in ModelManager.models.items():
            model.draw(ns_inc)