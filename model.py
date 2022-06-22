import numpy as np
import glm
import math

from collections import namedtuple

Coord3d = namedtuple('Coord3d', 'x y z') # ? Talvez substituir por glm.vec3

class Model:

    def __init__(self, obj, start_vertex, angle=0, r=Coord3d(0.0,1.0,0.0), t=Coord3d(0.0,0.0,0.0), s=Coord3d(1.0,1.0,1.0)):

        self.vertices = []
        self.texture_coords = []
        self.normals = []
        for face in obj['faces']:
            for vertex_index in face[0]:
                self.vertices.append( obj['vertices'][vertex_index-1] )
            for texture_coord_index in face[1]:
                self.texture_coords.append( obj['texture_coords'][texture_coord_index-1] )
            for normal_index in face[2]:
                self.normals.append( obj['normals'][normal_index-1] )
        self.start_vertex = start_vertex
        self.vertex_count = len(self.vertices)
        
        self.angle = angle
        self.r = r
        self.t = t
        self.s = s

        self.textures = []
    
    def add_textures(self, textures):
        self.textures = textures

    def model_matrix(self):
        angle_rad = math.radians(self.angle)
        matrix_transform = glm.mat4(1.0) # Matriz identidade
        matrix_transform = glm.rotate(matrix_transform, angle_rad, glm.vec3(self.r.x, self.r.y, self.r.z)) # Rotação
        matrix_transform = glm.translate(matrix_transform, glm.vec3(self.t.x, self.t.y, self.t.z)) # Translação
        matrix_transform = glm.scale(matrix_transform, glm.vec3(self.s.x, self.s.y, self.s.z)) # Escala
        matrix_transform = np.array(matrix_transform)
        return matrix_transform
    
    def transform(self, t: Coord3d):
        self.t = t