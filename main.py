import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math

from glfw_instance import GlfwInstance as GI
from model import *
from model_manager import ModelManager

GI.initialize()

ModelManager.load_model('sky')
ModelManager.load_model('terrain2', t=Coord3d(40, .2, -15), s=Coord3d(10, 10, 10) )

ModelManager.load_model('watchtower', r=Coord3d(0, 1, 0))
ModelManager.load_model('ranger', r=Coord3d(0, 1, 0), s=Coord3d(0.5, 0.5, 0.5))
ModelManager.load_model('stool', r=Coord3d(0, 1, 0), t=Coord3d(0, 6.5, 0), s=Coord3d(0.1, 0.1, 0.1))
ModelManager.load_model('moon', light_source=True, r=Coord3d(-1, 0, -1), s=Coord3d(0.01, 0.01, 0.01))
ModelManager.load_model('pinheiro', r=Coord3d(0, 1, 0), t=Coord3d(0, 1, 5), s=Coord3d(1, 1, 1))
ModelManager.load_model('toquinho', r=Coord3d(0, 1, 0), t=Coord3d(-3.5, 1, -2.5), s=Coord3d(1, 1, 1))
ModelManager.load_model('cerca', r=Coord3d(0, 1, 0), t=Coord3d(5, 1.56, -2.5), s=Coord3d(0.5, 0.5, 0.5))
ModelManager.load_model('arvore', r=Coord3d(0, 1, 0), t=Coord3d(5, 1, 0), s=Coord3d(0.06, 0.06, 0.06))
ModelManager.load_model('lata', r=Coord3d(0, 1, 0), t=Coord3d(0, 6.9, 0), s=Coord3d(0.06, 0.06, 0.06))
ModelManager.send_to_GPU()

"""
    CAMERA E MOUSE
    TODO: criar classe separada
"""

camera_pos   = glm.vec3(0,  7,  5)
camera_front = glm.vec3(0,  0, -1)
camera_up    = glm.vec3(0,  1,  0)
polygonal_mode = False
fovy = 45

def key_event(window,key,scancode,action,mods):

    global camera_pos, camera_front, camera_up, polygonal_mode
    global ns_inc, fovy
    
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
    if key == glfw.KEY_LEFT and (action==glfw.PRESS or glfw.REPEAT):
        fovy -= 5
    if key == glfw.KEY_RIGHT and (action==glfw.PRESS or glfw.REPEAT):
        fovy += 5
        
firstMouse = True
yaw = -90 
pitch = 0
lastX =  GI.width/2
lastY =  GI.height/2

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
    
    if pitch >= 90:
        pitch = 90
    if pitch <= -90:
        pitch = -90

    front = glm.vec3()
    front.x = math.cos(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    front.y = math.sin(glm.radians(pitch))
    front.z = math.sin(glm.radians(yaw)) * math.cos(glm.radians(pitch))
    camera_front = glm.normalize(front)
    
glfw.set_key_callback(GI.window,key_event)
glfw.set_cursor_pos_callback(GI.window, mouse_event)

# Matriz view
def view():
    global camera_pos, camera_front, camera_up
    mat_view = glm.lookAt(camera_pos, camera_pos + camera_front, camera_up)
    mat_view = np.array(mat_view)
    return mat_view

# Matriz projection
def projection():
    # perspective parameters: fovy, aspect, near, far
    global fovy
    mat_projection = glm.perspective(glm.radians(fovy), GI.width/GI.height, 0.1, 1000)
    mat_projection = np.array(mat_projection)    
    return mat_projection

"""
    EXECUCAO DO PROGRAMA
"""

# Exibir a janela
glfw.show_window(GI.window)
glfw.set_cursor_pos(GI.window, lastX, lastY)
glEnable(GL_DEPTH_TEST) # importante para 3D

ang = 0.1
ns_inc = 4
    
while not glfw.window_should_close(GI.window):

    glfw.poll_events() 
    ang += 0.001
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glClearColor(0.2, 0.2, 0.2, 1)
    
    if polygonal_mode==True:
        glPolygonMode(GL_FRONT_AND_BACK,GL_LINE)
    if polygonal_mode==False:
        glPolygonMode(GL_FRONT_AND_BACK,GL_FILL)
    
    ang += .2
    ModelManager.models['ranger'].transform( 
        t=Coord3d( math.cos(ang*0.02)*0.5, 6.5, math.sin(ang*0.02)*0.5 )
    )
    ModelManager.models['ranger'].rotate( 
        ang * -1.14,
    )
    ModelManager.models['moon'].transform(
        t=Coord3d(math.cos(ang*0.01)*20, 10, math.sin(ang*0.01)*20)
    )
    ModelManager.draw_models(
        ka=0.1, 
        kd=0.1, 
        ks=0.9, 
        ns=ns_inc
    )
    
    mat_view = view()
    loc_view = glGetUniformLocation(GI.program, "view")
    glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

    mat_projection = projection()
    loc_projection = glGetUniformLocation(GI.program, "projection")
    glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    
    
    # atualizando a posicao da camera/observador na GPU para calculo da reflexao especular
    loc_view_pos = glGetUniformLocation(GI.program, "viewPos") # recuperando localizacao da variavel viewPos na GPU
    glUniform3f(loc_view_pos, camera_pos[0], camera_pos[1], camera_pos[2]) # posicao da camera/observador (x,y,z)
    
    glfw.swap_buffers(GI.window)

glfw.terminate()