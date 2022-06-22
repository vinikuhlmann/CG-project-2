import os
from OpenGL.GL import *
from PIL import Image
from model import *

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
    model_list = {}
    vertices = []
    texture_coords = []
    normals = []
    vertex_count = 0
    texture_count = 0

    # Carrega um modelo
    @staticmethod
    def load_model(model_dir, angle=0, r=Coord3d(0.0,1.0,0.0), t=Coord3d(0.0,0.0,0.0), s=Coord3d(1.0,1.0,1.0)):
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
                model = Model(obj, start_vertex, angle, r, t, s)
                ModelManager.vertex_count += model.vertex_count
            
            # Carregamento de textura
            elif filepath.endswith(('.jpg', '.png')):
                load_texture(ModelManager.texture_count, filepath)
                textures.append(ModelManager.texture_count)
                ModelManager.texture_count += 1
        
        model.add_textures(textures)
        
        # Adiciona o modelo na lista e guarda suas informações
        ModelManager.model_list[model_name] = model
        ModelManager.vertices += model.vertices
        ModelManager.texture_coords += model.texture_coords
        ModelManager.normals += model.normals