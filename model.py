import numpy as np
import glm
import math
from OpenGL.GL import *
from glfw_instance import GlfwInstance as GI
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

        self.texture = None
    
    def add_texture(self, texture):
        self.texture = texture

    def model_matrix(self):
        angle_rad = math.radians(self.angle)
        matrix_transform = glm.mat4(1.0) # Matriz identidade
        matrix_transform = glm.translate(matrix_transform, glm.vec3(self.t.x, self.t.y, self.t.z)) # Translação
        matrix_transform = glm.rotate(matrix_transform, angle_rad, glm.vec3(self.r.x, self.r.y, self.r.z)) # Rotação
        matrix_transform = glm.scale(matrix_transform, glm.vec3(self.s.x, self.s.y, self.s.z)) # Escala
        matrix_transform = np.array(matrix_transform)
        return matrix_transform
    
    def transform(self, r=None, t=None, s=None):
        if r != None:
            self.r = r
        if t != None:
            self.t = t
        if s != None:
            self.s = s
    
    def rotate(self, angle):
        self.angle = angle
    
    # Desenha o modelo
    #   ka -> Coeficiente de reflexao ambiente do modelo
    #   kd -> Coeficiente de reflexao difusa do modelo
    #   ks -> Coeficiente de reflexao especular do modelo
    #   ns -> Expoente de reflexao especular
    def draw(self, ka, kd, ks, ns):

        mat_model = self.model_matrix()
        loc_model = glGetUniformLocation(GI.program, "model")
        glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
        
        ka = 0.1 # Coeficiente de reflexao ambiente do modelo
        kd = 0.1 # Coeficiente de reflexao difusa do modelo
        ks = 0.9 # Coeficiente de reflexao especular do modelo
        ns = ns # Expoente de reflexao especular
        
        # Recupera localização das variáveis na GPU
        loc_ka = glGetUniformLocation(GI.program, "ka")
        loc_kd = glGetUniformLocation(GI.program, "kd")
        loc_ks = glGetUniformLocation(GI.program, "ks")
        loc_ns = glGetUniformLocation(GI.program, "ns")
        
        # Insere o valor das variáveis
        glUniform1f(loc_ka, ka)
        glUniform1f(loc_kd, kd)
        glUniform1f(loc_ks, ks)
        glUniform1f(loc_ns, ns)
        
        if self.texture != None:
            glBindTexture(GL_TEXTURE_2D, self.texture) # Define id da textura do modelo

        glDrawArrays(GL_TRIANGLES, self.start_vertex, self.vertex_count) # Renderiza

class LightModel(Model):

    def draw(self, ka, kd, ks, ns):
        
        mat_model = self.model_matrix()
        loc_model = glGetUniformLocation(GI.program, "model")
        glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
        
        # Recupera localização das variáveis na GPU
        loc_ka = glGetUniformLocation(GI.program, "ka")
        loc_kd = glGetUniformLocation(GI.program, "kd")
        loc_ks = glGetUniformLocation(GI.program, "ks")
        loc_ns = glGetUniformLocation(GI.program, "ns")
        
        # Insere o valor das variáveis
        glUniform1f(loc_ka, ka)
        glUniform1f(loc_kd, kd)
        glUniform1f(loc_ks, ks)
        glUniform1f(loc_ns, ns)

        # Se objeto produzir luz, inserir luz
        loc_light_pos = glGetUniformLocation(GI.program, "lightPos") # Localizacao da variavel lightPos na GPU
        glUniform3f(loc_light_pos, self.t.x, self.t.y, self.t.z) # Define a posição da luz
        
        glBindTexture(GL_TEXTURE_2D, self.texture) # Define id da textura do modelo
        glDrawArrays(GL_TRIANGLES, self.start_vertex, self.vertex_count) # Renderiza