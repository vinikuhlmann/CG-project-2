from OpenGL.GL import *
import numpy as np
import glm
import math
from PIL import Image

from collections import namedtuple

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

Coord3d = namedtuple('Coord3d', 'x y z') # ? Talvez substituir por glm.vec3

class Model3d:

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
        self.start_vertex = Model3d.vertex_total
        self.vertex_count = len(self.vertices_list)
        Model3d.vertex_total += self.vertex_count

        self.texture_list = []
        for texture_filepath in texture_filepath_list: # Load textures
            print(f'Loading {texture_filepath}')
            load_texture(Model3d.texture_count, texture_filepath)
            self.texture_list.append(Model3d.texture_count)
            Model3d.texture_count += 1
        
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